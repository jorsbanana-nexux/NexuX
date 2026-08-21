"""
NexuX V9.5 — AI Content Analysis Engine
==================================================
Editorial-conscious viral clip selection with:
- Editorial consciousness (narrative, emotion, coherence, hook intelligence)
- Technical scoring (pace, face, scene, speaker)
- Critic revision loop integration
- Multi-language support (EN, ID, ES)

The old V7.0 approach was rigid keyword matching. V8.0 blends
algorithmic signals with editorial consciousness for gold-standard results.
"""
import json, os, re
from typing import List, Dict, Optional, Tuple
import logging

from .constants import (
    EXCITEMENT_KEYWORDS, HOOK_PATTERNS, RETENTION_TRIGGERS,
    OUTPUT_DIR,
)
from .utils import clean_for_json
from .editorial import batch_editorial_analysis, analyze_editorial
from .boundaries import adjust_clip_boundaries

log = logging.getLogger("nexus.analyze")


# ── Main Analysis ───────────────────────────────────

def analyze_content(
    transcript: Dict,
    target_duration: int = 60,
    face_data: Optional[List[Dict]] = None,
    scene_data: Optional[List[Dict]] = None,
    screen_data: Optional[List[Dict]] = None,
    max_clips: int = 10,
    use_ai_scoring: bool = True,
    editorial_enrichment: bool = True,
) -> List[Dict]:
    """Analyze transcript to find best viral clip candidates.
    
    V8.0 Multi-dimensional scoring:
    1. Hook Score (0-20): First 3 seconds impact (keyword-based)
    2. Pace Score (0-20): Words per second
    3. Keyword Score (0-25): Excitement keyword density
    4. Speaker Score (0-15): Speaker variety & interaction
    5. Face Score (0-10): Face visibility
    6. Position Score (0-10): Where in video
    7. Editorial Consciousness (V8.0): Narrative, emotion, coherence, hook intelligence
    
    Args:
        transcript: Whisper transcript with segments
        target_duration: Target clip duration in seconds
        face_data: Optional face tracking data
        scene_data: Optional scene change data
        screen_data: Optional screen share data
        max_clips: Maximum clips to return
        use_ai_scoring: Whether to use Gemini for semantic analysis
        editorial_enrichment: Whether to apply editorial consciousness scoring
    
    Returns:
        List of clip candidates sorted by score (desc), enriched with editorial data
    """
    segments = transcript.get("segments", [])
    if not segments:
        log.warning("[Analyze] No transcript segments")
        return []

    # Get total duration
    try:
        total_duration = float(segments[-1].get("end") or 0)
        if total_duration <= 0:
            total_duration = float(segments[-1].get("start", 0) + 5)
    except (IndexError, KeyError, TypeError):
        log.error("[Analyze] Cannot determine duration")
        return []

    log.info(f"[Analyze] Duration: {total_duration:.1f}s | Target: {target_duration}s | "
             f"Editorial: {'ON' if editorial_enrichment else 'OFF'}")

    # Short video → single full clip
    if total_duration <= target_duration:
        clips = _make_full_clip(segments, total_duration)
        if editorial_enrichment:
            clips = batch_editorial_analysis(clips, segments, total_duration)
        return clips

    # Windowed scanning
    window = target_duration
    step = max(1, target_duration // 5)  # 80% overlap for precision
    candidates = []

    start = 0.0
    while start + max(5, target_duration // 3) <= total_duration:
        end = min(start + window, total_duration)
        
        # Segments overlapping this window
        win_segs = [
            s for s in segments
            if s.get("start", 0) < end and s.get("end", 0) > start
        ]
        if len(win_segs) < 2:
            start += step
            continue

        # ── Score Calculation ──
        scores = {}
        
        # 1. Hook Score (first 3s or first 20% of window)
        hook_text = " ".join(
            s.get("text", "")
            for s in win_segs
            if s.get("start", 0) < start + max(3, (end-start)*0.2)
        ).lower()
        scores["hook"] = _score_hook(hook_text) * 20
        
        # 2. Pace Score
        total_words = sum(len(s.get("text", "").split()) for s in win_segs)
        wps = total_words / max(end - start, 1)
        # Optimal WPS for viral content: 2.5-4.0
        scores["pace"] = min(20, max(0, (wps - 1.0) * 6))
        
        # 3. Keyword Score
        win_text = " ".join(s.get("text", "") for s in win_segs).lower()
        kw_hits = sum(1 for kw in EXCITEMENT_KEYWORDS if kw in win_text)
        scores["keyword"] = min(25, kw_hits * 5)
        
        # 4. Speaker Score
        speakers = set(
            s.get("speaker", "SPEAKER_00")
            for s in win_segs if s.get("speaker"))
        speaker_count = len(speakers)
        scores["speaker"] = min(15, speaker_count * 5)
        
        # 5. Face Score
        face_vis = 0.0
        if face_data:
            relevant = [fd for fd in face_data if start <= fd["time"] <= end]
            if relevant:
                face_vis = sum(
                    1 for fd in relevant if fd.get("face_count", 0) > 0
                ) / len(relevant)
        scores["face"] = face_vis * 10
        
        # 6. Position Score (slightly favors later clips)
        pos_ratio = start / max(total_duration, 1)
        scores["position"] = min(10, pos_ratio * 8 + 3)
        
        # 7. Scene Change bonus
        scene_bonus = 0
        if scene_data:
            scene_count = sum(
                1 for sc in scene_data
                if start <= sc["time"] <= end)
            scene_bonus = min(5, scene_count * 1)
        
        # 8. Screen share bonus (good for educational content)
        screen_bonus = 0
        if screen_data:
            in_range = [s for s in screen_data if start <= s["time"] <= end]
            if in_range:
                pct_screen = sum(1 for s in in_range if s.get("is_screen_share")) / len(in_range)
                screen_bonus = pct_screen * 5

        # Composite algorithmic score
        total_score = (
            scores["hook"] +
            scores["pace"] +
            scores["keyword"] +
            scores["speaker"] +
            scores["face"] +
            scores["position"] +
            scene_bonus +
            screen_bonus
        ) / 100  # Normalize to 0-1

        clip_text = " ".join(s.get("text", "") for s in win_segs)

        candidates.append({
            "start": round(start, 2),
            "end": round(end, 2),
            "duration": round(end - start, 1),
            "score": round(total_score, 3),
            "scores": {
                "hook": round(scores["hook"], 1),
                "pace": round(scores["pace"], 1),
                "keyword": round(scores["keyword"], 1),
                "speaker": round(scores["speaker"], 1),
                "face": round(scores["face"], 1),
                "position": round(scores["position"], 1),
                "scene_bonus": round(scene_bonus, 1),
                "screen_bonus": round(screen_bonus, 1),
            },
            "text_preview": clip_text[:300],
            "wps": round(wps, 2),
            "keywords_found": kw_hits,
            "speaker_count": speaker_count,
            "face_visible_pct": round(face_vis * 100, 1),
            "word_count": total_words,
            "segments_in_window": len(win_segs),
        })

        start += step

    # Fallback if no candidates
    if not candidates:
        log.warning("[Analyze] No candidates — using full video")
        return _make_full_clip(segments, total_duration)

    # Sort & deduplicate
    candidates.sort(key=lambda x: x["score"], reverse=True)
    taken: List[Tuple[float, float]] = []
    result = []

    for c in candidates:
        overlaps = any(
            not (c["end"] <= t[0] or c["start"] >= t[1])
            for t in taken)
        if overlaps:
            continue
        taken.append((c["start"], c["end"]))
        
        # AI semantic re-scoring via Gemini (if available)
        if use_ai_scoring:
            try:
                ai_score = _ai_semantic_score(c["text_preview"])
                if ai_score:
                    c["ai_score"] = ai_score["score"]
                    c["ai_analysis"] = ai_score.get("analysis", "")
                    # Blend AI score with algorithmic score
                    c["score"] = round(c["score"] * 0.6 + ai_score["score"] * 0.4, 3)
            except Exception as e:
                log.warning(f"[Analyze] AI scoring failed: {e}")
        
        result.append(c)
        if len(result) >= max_clips * 2:  # Keep extras for critic replacement
            break

    # ── V8.0: Natural Speech Boundary Adjustment ──
    log.info("[Analyze] Snapping to natural speech boundaries...")
    result = adjust_clip_boundaries(result, segments, total_duration, tolerance=5.0)

    # ── V8.0: Editorial Consciousness Enrichment ──
    if editorial_enrichment:
        log.info("[Analyze] Applying editorial consciousness scoring...")
        result = batch_editorial_analysis(result, segments, total_duration)
        
        # Log editorial verdicts
        for c in result:
            ed = c.get("editorial", {})
            if ed.get("verdict"):
                log.info(f"  Clip [{c['start']:.0f}-{c['end']:.0f}s] "
                        f"score={c['score']:.3f} verdict={ed['verdict']}")

    # Trim to max_clips
    result = result[:max_clips]

    # Re-sort after all scoring
    result.sort(key=lambda x: x["score"], reverse=True)

    log.info(f"[Analyze] Selected {len(result)}/{len(candidates)} clips. "
             f"Top score: {result[0]['score']:.3f}" if result else "[Analyze] No clips selected")
    return result


# ── Scoring Helpers ─────────────────────────────────

def _score_hook(text: str) -> float:
    """Score the hook strength of opening text (0-1)."""
    if not text:
        return 0.3
    
    score = 0.0
    for pattern, bonus in HOOK_PATTERNS:
        if pattern in text:
            score += bonus
    
    # Bonus for short, punchy opening
    first_sentence = text.split(".")[0] if "." in text else text
    word_count = len(first_sentence.split())
    if 4 <= word_count <= 12:
        score += 3
    elif word_count < 4:
        score += 1  # Very short, could be impactful
    
    return min(1.0, score / 25)


def _make_full_clip(segments: list, duration: float) -> List[Dict]:
    """Create a single clip covering the full video."""
    full_text = " ".join(s.get("text", "") for s in segments)
    word_count = len(full_text.split())
    return [{
        "start": 0,
        "end": duration,
        "duration": duration,
        "score": 0.7,
        "scores": {"hook": 10, "pace": 10, "keyword": 15, "speaker": 5, "face": 5, "position": 5},
        "text_preview": full_text[:300],
        "wps": round(word_count / max(duration, 1), 2),
        "keywords_found": 0,
        "speaker_count": 1,
        "face_visible_pct": 0,
        "word_count": word_count,
        "segments_in_window": len(segments),
        "type": "full_video",
    }]


# ── AI Semantic Scoring (Gemini) ─────────────────────

def _ai_semantic_score(text: str) -> Optional[Dict]:
    """Use Gemini API for semantic viral potential analysis."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key or len(text) < 50:
        return None
    
    try:
        import urllib.request
        
        prompt = f"""Analyze this video transcript excerpt for viral potential.
Rate 0-1 how compelling this content is for short-form video (TikTok/Reels/Shorts).
Consider: hook strength, emotional engagement, clarity of message, standalone coherence.
Return JSON: {{"score": float, "analysis": "brief explanation"}}

Transcript: "{text[:500]}" """

        url = (f"https://generativelanguage.googleapis.com/v1beta/"
               f"models/gemini-1.5-flash:generateContent?key={api_key}")
        
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 200}
        }).encode()
        
        req = urllib.request.Request(url, data=payload, method="POST")
        req.add_header("Content-Type", "application/json")
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        
        text_response = data.get("candidates", [{}])[0].get(
            "content", {}).get("parts", [{}])[0].get("text", "")
        
        # Parse JSON from response
        json_match = re.search(r'\{[^}]+\}', text_response)
        if json_match:
            result = json.loads(json_match.group())
            return {"score": float(result.get("score", 0.5)),
                    "analysis": result.get("analysis", "")}
    except Exception as e:
        log.debug(f"[Analyze] Gemini scoring skipped: {e}")
    
    return None


def batch_analyze_with_ai(transcript: Dict, **kwargs) -> List[Dict]:
    """Convenience wrapper for analyze_content with AI scoring enabled."""
    kwargs["use_ai_scoring"] = True
    kwargs["editorial_enrichment"] = True
    return analyze_content(transcript, **kwargs)
