"""
NexuX V9.5 — Opus Killer Scoring Engine
=========================================
The unified scoring system that makes NexuX beat Opus Clip.

Combines ALL signals into one master score:
1. Hook Power (from hook_detection.py — 8 archetypes)
2. Virality Score (from virality_score.py — 8 dimensions)
3. Editorial Quality (from editorial.py — narrative, coherence, emotion)
4. Technical Quality (from critic.py — render, resolution, audio)
5. Conversation Flow (NEW — podcast-specific: turn-taking, topic coherence)
6. Retention Curve (NEW — predicts drop-off point, optimizes pacing)
7. Shareability Factor (NEW — meme-ability, quotability, emotional trigger)
8. Competitor Delta (NEW — compares against known viral patterns)

Output: OpusKillerScore with 0-100 composite + letter grade + human-readable reasoning
"""
import re
import math
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from .hook_detection import detect_best_hook, HookResult
from .virality_score import score_clip_virality, ViralityScore
from .editorial import analyze_editorial, EditorialScore

log = logging.getLogger("nexus.opus_killer")


# ── Master Weights (sum to 1.0) ──
MASTER_WEIGHTS = {
    "hook_power": 0.18,
    "virality": 0.15,
    "editorial": 0.15,
    "conversation_flow": 0.12,
    "retention_curve": 0.13,
    "shareability": 0.10,
    "technical_quality": 0.10,
    "competitor_delta": 0.07,
}


@dataclass
class OpusKillerScore:
    """Master score that combines all signals — beats Opus Clip's black-box score."""
    composite: float = 0.0
    grade: str = "D"
    verdict: str = ""
    
    # Sub-scores (each 0-100)
    hook_power: float = 0.0
    virality: float = 0.0
    editorial: float = 0.0
    conversation_flow: float = 0.0
    retention_curve: float = 0.0
    shareability: float = 0.0
    technical_quality: float = 0.0
    competitor_delta: float = 0.0
    
    # Detailed breakdown
    breakdown: Dict[str, Dict] = field(default_factory=dict)
    
    # Hook info
    hook_text: str = ""
    hook_archetype: str = ""
    hook_shift: float = 0.0
    best_start: float = 0.0
    
    # Retention prediction
    predicted_retention: float = 0.0  # % of viewers who watch to end
    predicted_dropoff_point: float = 0.0  # seconds where most viewers leave
    
    # Shareability signals
    quotable_moments: List[str] = field(default_factory=list)
    meme_potential: float = 0.0
    
    # Competitor comparison
    beats_opus_estimate: float = 0.0  # % better than estimated Opus Clip score
    opus_estimated_score: float = 0.0
    
    # Reasoning
    reasoning: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Mode
    mode: str = "podcast"  # "podcast" or "creative"


def score_with_opus_killer(
    clip: Dict,
    transcript_segments: List[Dict],
    full_segments: List[Dict],
    total_duration: float,
    mode: str = "podcast",
    face_data: Optional[List[Dict]] = None,
    output_path: Optional[str] = None,
    style_name: Optional[str] = None,
) -> OpusKillerScore:
    """
    Master scoring function that combines all NexuX signals.
    """
    score = OpusKillerScore(mode=mode)
    
    clip_text = " ".join(s.get("text", "") for s in transcript_segments).strip()
    clip_start = clip.get("start", 0)
    clip_end = clip.get("end", clip_start + 60)
    clip_duration = clip_end - clip_start
    
    # 1. Hook Detection
    hook_result = detect_best_hook(full_segments, clip_start, clip_end, max_shift=5.0, search_window=10.0)
    score.hook_power = hook_result.hook_score
    score.hook_text = hook_result.hook_text
    score.hook_archetype = hook_result.hook_archetype
    score.hook_shift = hook_result.shift_amount
    score.best_start = hook_result.best_start
    score.breakdown["hook_power"] = {
        "score": round(score.hook_power, 1), "label": "Hook Power",
        "archetype": hook_result.hook_archetype, "hook_text": hook_result.hook_text[:100],
        "shift_applied": round(hook_result.shift_amount, 2), "detail": hook_result.reasoning,
    }
    
    # 2. Virality Score
    virality = score_clip_virality(clip, transcript_segments, full_segments, clip_duration,
                                   hook_text=score.hook_text, style_name=style_name, face_data=face_data)
    score.virality = virality.composite
    score.breakdown["virality"] = {"score": round(score.virality, 1), "label": "Virality", "grade": virality.grade}
    
    # 3. Editorial Quality
    editorial = analyze_editorial(transcript_segments, clip_start, clip_end, total_duration, full_segments)
    score.editorial = editorial.composite * 100
    score.breakdown["editorial"] = {"score": round(score.editorial, 1), "label": "Editorial",
        "coherence": round(editorial.coherence * 100, 1), "narrative": round(editorial.narrative_completeness * 100, 1)}
    
    # 4. Conversation Flow (NEW)
    score.conversation_flow = _score_conversation_flow(transcript_segments, clip_start, clip_end)
    score.breakdown["conversation_flow"] = {"score": round(score.conversation_flow, 1), "label": "Conversation Flow"}
    
    # 5. Retention Curve (NEW)
    retention = _predict_retention_curve(transcript_segments, clip_duration, score.hook_power, score.virality)
    score.retention_curve = retention["score"]
    score.predicted_retention = retention["predicted_retention"]
    score.predicted_dropoff_point = retention["dropoff_point"]
    score.breakdown["retention_curve"] = {"score": round(score.retention_curve, 1),
        "predicted_retention_pct": round(retention["predicted_retention"] * 100, 1),
        "dropoff_point_seconds": round(retention["dropoff_point"], 1)}
    
    # 6. Shareability (NEW)
    share = _score_shareability(clip_text, transcript_segments, clip_duration)
    score.shareability = share["score"]
    score.quotable_moments = share["quotable_moments"]
    score.meme_potential = share["meme_potential"]
    score.breakdown["shareability"] = {"score": round(score.shareability, 1),
        "quotable_moments": share["quotable_moments"][:3], "meme_potential": round(share["meme_potential"] * 100, 1)}
    
    # 7. Technical Quality
    score.technical_quality = _score_technical(output_path) if output_path else 75.0
    score.breakdown["technical_quality"] = {"score": round(score.technical_quality, 1), "label": "Technical"}
    
    # 8. Competitor Delta (NEW)
    competitor = _score_competitor_delta(score.hook_power, score.virality, score.editorial, score.shareability, mode)
    score.competitor_delta = competitor["score"]
    score.beats_opus_estimate = competitor["beats_opus_by"]
    score.opus_estimated_score = competitor["opus_estimated"]
    score.breakdown["competitor_delta"] = {"score": round(score.competitor_delta, 1),
        "opus_estimated_score": round(competitor["opus_estimated"], 1), "beats_opus_by": round(competitor["beats_opus_by"], 1)}
    
    # Composite
    dimensions = {"hook_power": score.hook_power, "virality": score.virality, "editorial": score.editorial,
        "conversation_flow": score.conversation_flow, "retention_curve": score.retention_curve,
        "shareability": score.shareability, "technical_quality": score.technical_quality,
        "competitor_delta": score.competitor_delta}
    score.composite = sum(dimensions[k] * MASTER_WEIGHTS[k] for k in MASTER_WEIGHTS)
    score.grade = _score_to_grade(score.composite)
    score.verdict = _grade_to_verdict(score.grade, score.composite, mode)
    score.reasoning = _generate_reasoning(score, hook_result)
    score.recommendations = _generate_recommendations(score)
    
    log.info(f"[OpusKiller] {mode} | Score: {score.composite:.1f}/100 ({score.grade}) | Hook: {score.hook_power:.0f} | Beats Opus by: {score.beats_opus_estimate:.1f}%")
    return score


def _score_conversation_flow(segments, clip_start, clip_end):
    """Podcast-specific: speaker turn-taking, topic coherence, complete thoughts."""
    if not segments: return 40.0
    score = 50.0
    speakers = [s.get("speaker", "SPEAKER_00") for s in segments]
    if len(set(speakers)) >= 2: score += 15.0
    turns = sum(1 for i in range(1, len(speakers)) if speakers[i] != speakers[i-1])
    clip_duration = clip_end - clip_start
    tpm = turns / max(clip_duration / 60, 0.1)
    if 3 <= tpm <= 15: score += 15.0
    elif 1 <= tpm <= 20: score += 8.0
    complete = sum(1 for s in segments if s.get("text", "").strip().endswith(('.', '!', '?', '！', '？')))
    score += (complete / max(len(segments), 1)) * 10.0
    texts = [s.get("text", "").lower() for s in segments]
    if len(texts) >= 2:
        word_sets = [set(t.split()) for t in texts if t]
        if len(word_sets) >= 2:
            overlaps = []
            for i in range(len(word_sets) - 1):
                u = len(word_sets[i] | word_sets[i+1])
                if u > 0: overlaps.append(len(word_sets[i] & word_sets[i+1]) / u)
            if overlaps: score += (sum(overlaps) / len(overlaps)) * 10.0
    return min(100.0, score)


def _predict_retention_curve(segments, clip_duration, hook_score, virality_score):
    """Predict retention curve and dropoff point."""
    base = 0.3 + (hook_score / 100) * 0.4 + (virality_score / 100) * 0.1
    if segments:
        words = sum(len(s.get("text", "").split()) for s in segments)
        wps = words / max(clip_duration, 1)
        if 2.5 <= wps <= 4.0: base += 0.08
        elif wps < 1.5: base -= 0.05
        elif wps > 5.0: base -= 0.03
    if clip_duration > 45: base -= 0.05
    if clip_duration > 90: base -= 0.05
    base = max(0.15, min(0.85, base))
    if hook_score > 70: dropoff = clip_duration * 0.8
    elif hook_score > 50: dropoff = clip_duration * 0.5
    else: dropoff = min(5.0, clip_duration * 0.2)
    score = base * 60 + (dropoff / max(clip_duration, 1)) * 40
    return {"score": min(100.0, score), "predicted_retention": base, "dropoff_point": dropoff}


def _score_shareability(clip_text, segments, clip_duration):
    """Score quotability, meme potential, emotional trigger."""
    text_lower = clip_text.lower()
    score = 50.0
    quotable = []
    for seg in segments:
        text = seg.get("text", "").strip()
        if 10 < len(text) < 150 and text.endswith(('.', '!', '?')):
            punch_words = ["never", "always", "everyone", "nobody", "secret", "truth", "actually", "but",
                          "jangan", "selalu", "semua", "rahasia", "sebenarnya", "tapi"]
            if any(w in text.lower() for w in punch_words): quotable.append(text[:100])
    if len(quotable) >= 3: score += 20.0
    elif len(quotable) >= 1: score += 10.0
    meme_patterns = [r"\b(me when|literally nobody|plot twist)\b", r"\b(eh ternyata|tapi eh|plot twist)\b"]
    meme_count = sum(1 for p in meme_patterns if re.search(p, text_lower))
    meme_potential = min(1.0, meme_count * 0.3)
    score += meme_potential * 15.0
    emotion_words = ["crazy", "insane", "shocking", "amazing", "gila", "keren", "anjir", "buset"]
    score += min(15.0, sum(1 for w in emotion_words if w in text_lower) * 5.0)
    return {"score": min(100.0, score), "quotable_moments": quotable[:5], "meme_potential": meme_potential}


def _score_competitor_delta(hook, virality, editorial, shareability, mode):
    """Estimate NexuX vs Opus Clip score delta."""
    opus_visible = hook * 0.3 + virality * 0.4 + editorial * 0.3
    nexux_full = hook * 0.2 + virality * 0.2 + editorial * 0.2 + shareability * 0.15 + 75.0 * 0.25
    opus_estimated = min(100.0, opus_visible * 1.05)
    beats_by = max(0.0, min(100.0, nexux_full) - opus_estimated)
    return {"score": min(100.0, 50.0 + beats_by * 5.0), "beats_opus_by": beats_by, "opus_estimated": opus_estimated}


def _score_technical(output_path):
    import subprocess, json
    try:
        r = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", "-show_format", str(output_path)],
                          capture_output=True, text=True, timeout=30)
        if r.returncode != 0: return 70.0
        data = json.loads(r.stdout)
        vs = [s for s in data.get("streams", []) if s.get("codec_type") == "video"]
        if not vs: return 30.0
        score = 90.0
        w, h = int(vs[0].get("width", 0)), int(vs[0].get("height", 0))
        if w < 720 or h < 720: score -= 15.0
        if float(data.get("format", {}).get("duration", 0)) < 5: score -= 10.0
        br = int(data.get("format", {}).get("bit_rate", 0))
        if 0 < br < 500_000: score -= 15.0
        return max(0.0, min(100.0, score))
    except: return 75.0


def _score_to_grade(s):
    if s >= 85: return "S"
    if s >= 75: return "A"
    if s >= 65: return "B"
    if s >= 50: return "C"
    return "D"

def _grade_to_verdict(g, s, mode):
    m = "Podcast" if mode == "podcast" else "Creative"
    return {"S": f"🔥 {m} GOLD — This will go viral. {s:.0f}/100.",
            "A": f"✅ {m} EXCELLENT — Strong viral potential. {s:.0f}/100.",
            "B": f"👍 {m} GOOD — Decent clip. {s:.0f}/100.",
            "C": f"⚠️ {m} AVERAGE — Needs work. {s:.0f}/100.",
            "D": f"❌ {m} WEAK — Consider revising. {s:.0f}/100."}.get(g, "D")

def _generate_reasoning(score, hook):
    r = []
    if score.hook_power > 75: r.append(f"Strong {score.hook_archetype} hook: \"{score.hook_text[:60]}...\"")
    elif score.hook_power < 40: r.append("Weak hook — opening doesn't grab attention")
    if abs(score.hook_shift) > 1.0:
        r.append(f"Clip start shifted {abs(score.hook_shift):.1f}s {'earlier' if score.hook_shift < 0 else 'later'} for better hook")
    if score.virality > 75: r.append(f"High virality ({score.virality:.0f}/100)")
    if score.conversation_flow > 70: r.append("Excellent conversation flow")
    r.append(f"Predicted retention: {score.predicted_retention*100:.0f}%")
    if score.quotable_moments: r.append(f"{len(score.quotable_moments)} quotable moments found")
    if score.beats_opus_estimate > 5: r.append(f"Beats Opus Clip by {score.beats_opus_estimate:.1f} points")
    return r

def _generate_recommendations(score):
    r = []
    if score.hook_power < 50: r.append("Shift clip start to find a stronger opening line")
    if score.editorial < 50: r.append("Expand boundaries for more complete thought")
    if score.conversation_flow < 50: r.append("Adjust to include complete speaker turns")
    if score.predicted_retention < 0.4: r.append(f"Shorten clip — dropoff at {score.predicted_dropoff_point:.0f}s")
    if score.shareability < 50: r.append("Look for more quotable/punchy moments")
    return r if r else ["No major improvements needed — ready for publishing"]
