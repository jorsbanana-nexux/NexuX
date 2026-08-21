"""
NexuX V8.5 — Virality Score Engine
====================================
Multi-dimensional virality prediction that scores clips 0-100,
matching and exceeding Opus Clip's scoring system.

Unlike Opus Clip's black-box score, NexuX provides a FULL BREAKDOWN:
- Hook Power (0-100): How strong is the first 3 seconds?
- Retention Prediction (0-100): Will viewers watch to the end?
- Shareability (0-100): Will people share this?
- Trend Alignment (0-100): Does it match viral patterns?
- Emotional Impact (0-100): How strong is the emotional reaction?
- Information Density (0-100): Value-per-second delivered?
- Caption Virality (0-100): How viral is the on-screen text?
- Pacing Quality (0-100): Is the rhythm optimal for short-form?

Final score = weighted average -> 0-100 with letter grade (S, A, B, C, D)
"""
import re
import math
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("nexus.virality")


# -- Virality Scoring Constants --

# Weights for final composite score (must sum to 1.0)
DIMENSION_WEIGHTS = {
    "hook_power": 0.20,
    "retention_prediction": 0.15,
    "shareability": 0.12,
    "trend_alignment": 0.10,
    "emotional_impact": 0.13,
    "information_density": 0.10,
    "caption_virality": 0.08,
    "pacing_quality": 0.12,
}

# Viral keyword patterns (Indonesian + English)
VIRAL_PATTERNS = {
    "shock": [
        r"\b(shocking|insane|crazy|mind.?blowing|unbelievable|jaw.?dropping)\b",
        r"\b(gila|buset|edan|njir|anjir|ngilu|gokil|ga?ila)\b",
        r"\b(tidak percaya|terbongkar|terungkap|rahasia)\b",
    ],
    "authority": [
        r"\b(secret|truth about|what nobody|the real reason)\b",
        r"\b(rahasia|yang tidak|kebenaran|alasan sebenarnya)\b",
        r"\b(proven|science says|studies show|research)\b",
    ],
    "curiosity": [
        r"\b(what happens|why you should|the reason|you won't believe)\b",
        r"\b(apa yang terjadi|kenapa kamu|alasannya|tak akan percaya)\b",
        r"\b(the truth|hidden|nobody talks about)\b",
    ],
    "relatable": [
        r"\b(everyone|we all|you know when|me too|same)\b",
        r"\b(sering kali|semua orang|pasti pernah|sama aja)\b",
        r"\b(relatable|that's so|literally me|story of my life)\b",
    ],
    "conflict": [
        r"\b(but then|plot twist|turned out|didn't expect)\b",
        r"\b(tapi|eh ternyata|plot twist|nggak nyangka|siapa sangka)\b",
        r"\b(against all|fight back|stood up|called out)\b",
    ],
    "numbered": [
        r"\b(\d+\s+(things|reasons|ways|tips|secrets|mistakes|signs))\b",
        r"\b(\d+\s+(hal|alasan|cara|rahasia|kesalahan|tanda))\b",
    ],
    "money_success": [
        r"\b(made \$|earned|profit|revenue|income|salary)\b",
        r"\b(untung|cuan|gaji|penghasilan|juta|miliar)\b",
        r"\b(successful|achieved|bought my first|quit my job)\b",
    ],
    "educational": [
        r"\b(how to|step by step|tutorial|guide|learn)\b",
        r"\b(cara|tutorial|panduan|belajar|langkah)\b",
    ],
}

# Trend signals (what's trending in 2025-2026 short-form)
TREND_SIGNALS = {
    "face_to_camera": 0.15,
    "quick_cuts": 0.10,
    "before_after": 0.20,
    "reaction": 0.15,
    "story_time": 0.10,
    "listicle": 0.15,
    "myth_busting": 0.15,
    "personal_story": 0.10,
    "controversy": 0.20,
    "behind_scenes": 0.10,
    "transformation": 0.15,
    "lesson_learned": 0.10,
}

# Retention patterns
RETENTION_SIGNALS = {
    "open_loop": [
        r"\b(but here's|wait until|you'll see|the crazy part)\b",
        r"\b(tapi yang|tunggu sampai|hal gilanya|yang paling)\b",
    ],
    "pattern_break": [
        r"\b(actually|but wait|hold on|plot twist)\b",
        r"\b(sebenernya|tapi tunggu|eh|plot twist)\b",
    ],
    "payoff_tease": [
        r"\b(at the end|the best part|the result|and then)\b",
        r"\b(di akhir|yang paling|hasilnya|dan kemudian)\b",
    ],
    "escalation": [
        r"\b(and then|on top of|but it gets|even worse|even better)\b",
        r"\b(lalu|di atas itu|lebih parah|lebih bagus)\b",
    ],
}

ANTI_VIRAL_PATTERNS = [
    r"\b(uh|um|er|ah|hmm|you know|i mean|like basically)\b",
    r"\b(eh|um|ah|yang jadi|gitu lah|ya begitu)\b",
    r"\b(anyway|moving on|so yeah|that's it)\b",
    r"\b(in conclusion|to summarize|in summary)\b",
]


@dataclass
class ViralityScore:
    """Complete virality evaluation with breakdown."""
    hook_power: float = 0.0
    retention_prediction: float = 0.0
    shareability: float = 0.0
    trend_alignment: float = 0.0
    emotional_impact: float = 0.0
    information_density: float = 0.0
    caption_virality: float = 0.0
    pacing_quality: float = 0.0

    composite: float = 0.0
    grade: str = "D"
    verdict: str = ""
    confidence: float = 0.0

    breakdown: Dict[str, Dict] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    detected_patterns: List[str] = field(default_factory=list)
    trend_signals: List[str] = field(default_factory=list)


def score_clip_virality(
    clip: Dict,
    transcript: List[Dict],
    full_segments: List[Dict],
    clip_duration: float,
    hook_text: Optional[str] = None,
    style_name: Optional[str] = None,
    face_data: Optional[Dict] = None,
) -> ViralityScore:
    """Score a clip's virality potential on 8 dimensions."""
    score = ViralityScore()

    clip_text = " ".join(s.get("text", "") for s in transcript).strip()
    clip_lower = clip_text.lower()

    if not clip_lower or len(clip_lower) < 15:
        score.verdict = "Insufficient content for virality analysis"
        score.confidence = 0.2
        return score

    # 1. Hook Power
    score.hook_power = _score_hook_power(transcript, clip, clip_duration, hook_text)
    score.breakdown["hook_power"] = {
        "score": round(score.hook_power, 1),
        "label": "Hook Power",
        "description": "Strength of the first 3 seconds to stop scrolling",
        "max": 100,
    }

    # 2. Retention Prediction
    score.retention_prediction = _score_retention(transcript, clip_duration, clip_lower)
    score.breakdown["retention_prediction"] = {
        "score": round(score.retention_prediction, 1),
        "label": "Retention Prediction",
        "description": "Likelihood viewers watch to the end",
        "max": 100,
    }

    # 3. Shareability
    score.shareability = _score_shareability(clip_lower, clip_duration, transcript)
    score.breakdown["shareability"] = {
        "score": round(score.shareability, 1),
        "label": "Shareability",
        "description": "How likely viewers are to share this clip",
        "max": 100,
    }

    # 4. Trend Alignment
    score.trend_alignment = _score_trend_alignment(clip_lower, transcript, face_data, clip_duration)
    score.breakdown["trend_alignment"] = {
        "score": round(score.trend_alignment, 1),
        "label": "Trend Alignment",
        "description": "How well it matches current viral patterns",
        "max": 100,
    }

    # 5. Emotional Impact
    score.emotional_impact = _score_emotional_impact(transcript, clip_lower)
    score.breakdown["emotional_impact"] = {
        "score": round(score.emotional_impact, 1),
        "label": "Emotional Impact",
        "description": "Strength of emotional reaction triggered",
        "max": 100,
    }

    # 6. Information Density
    score.information_density = _score_information_density(clip_lower, clip_duration, transcript)
    score.breakdown["information_density"] = {
        "score": round(score.information_density, 1),
        "label": "Information Density",
        "description": "Value delivered per second",
        "max": 100,
    }

    # 7. Caption Virality
    score.caption_virality = _score_caption_virality(hook_text, style_name, clip_lower)
    score.breakdown["caption_virality"] = {
        "score": round(score.caption_virality, 1),
        "label": "Caption Virality",
        "description": "How engaging the on-screen text is",
        "max": 100,
    }

    # 8. Pacing Quality
    score.pacing_quality = _score_pacing(transcript, clip_duration)
    score.breakdown["pacing_quality"] = {
        "score": round(score.pacing_quality, 1),
        "label": "Pacing Quality",
        "description": "Rhythm and energy variation throughout the clip",
        "max": 100,
    }

    # Composite
    dimensions = {
        "hook_power": score.hook_power,
        "retention_prediction": score.retention_prediction,
        "shareability": score.shareability,
        "trend_alignment": score.trend_alignment,
        "emotional_impact": score.emotional_impact,
        "information_density": score.information_density,
        "caption_virality": score.caption_virality,
        "pacing_quality": score.pacing_quality,
    }

    score.composite = sum(dimensions[k] * DIMENSION_WEIGHTS[k] for k in DIMENSION_WEIGHTS)
    score.grade = _score_to_grade(score.composite)
    score.verdict = _grade_to_verdict(score.grade, score.composite)
    score.confidence = _calculate_confidence(transcript, clip_duration, len(clip_lower))
    score.recommendations = _generate_recommendations(dimensions, score.detected_patterns)
    score.evidence = _generate_evidence(dimensions, score.detected_patterns, score.trend_signals)

    log.info(
        f"[Virality] Score: {score.composite:.1f}/100 ({score.grade}) | "
        f"Hook: {score.hook_power:.0f} | Retention: {score.retention_prediction:.0f} | "
        f"Share: {score.shareability:.0f} | Trend: {score.trend_alignment:.0f} | "
        f"Emotion: {score.emotional_impact:.0f} | Info: {score.information_density:.0f} | "
        f"Caption: {score.caption_virality:.0f} | Pacing: {score.pacing_quality:.0f}"
    )

    return score


# -- Individual Dimension Scorers --

def _score_hook_power(segments, clip, clip_duration, hook_text=None):
    """Score the hook power of the first 3 seconds."""
    clip_start = clip.get("start", 0)
    hook_duration = min(3.0, clip_duration * 0.25)

    hook_segs = [
        s for s in segments
        if s.get("start", 0) < clip_start + hook_duration and s.get("end", 0) > clip_start
    ]

    hook_text_raw = " ".join(s.get("text", "") for s in hook_segs).strip().lower()

    if not hook_text_raw:
        return 20.0

    score = 40.0

    hook_archetypes = {
        "pattern_interrupt": r"\b(stop|wait|hold on|listen|look|hey)\b",
        "bold_claim": r"\b(this (will|is|changed)|you (need|have to|must)|never)\b",
        "curiosity_gap": r"\b(the truth|what nobody|the secret|why you|the real reason)\b",
        "contrarian": r"\b(everyone is wrong|contrary to|but actually|people think)\b",
        "personal_stakes": r"\b(i (lost|made|found|quit|failed|discovered))\b",
        "numbered": r"\b(\d+\s+(things|reasons|ways|tips|secrets))\b",
        "story_launch": r"\b(so (this|there|i)|let me tell|story time)\b",
        "question": r"\b(did you know|guess what|what if|have you ever)\b",
    }

    for name, pattern in hook_archetypes.items():
        if re.search(pattern, hook_text_raw):
            score += 10
            score.detected_patterns.append(name) if hasattr(score, 'detected_patterns') else None

    hook_words = len(hook_text_raw.split())
    if 3 <= hook_words <= 12:
        score += 10
    elif hook_words < 3:
        score -= 5
    elif hook_words > 20:
        score -= 10

    first_word = hook_text_raw.split()[0] if hook_text_raw else ""
    strong_openers = {"so", "but", "and", "the", "this", "here's", "imagine",
                      "never", "everyone", "nobody", "what", "why", "how",
                      "look", "stop", "wait"}
    if first_word in strong_openers:
        score += 5

    if "?" in hook_text_raw[:100]:
        score += 8

    emotional_words = ["crazy", "insane", "shocking", "unbelievable",
                       "gila", "buset", "anjir", "edan"]
    if any(w in hook_text_raw for w in emotional_words):
        score += 8

    filler_starts = ["uh", "um", "yeah", "okay", "so yeah", "i mean"]
    if any(hook_text_raw.startswith(f) for f in filler_starts):
        score -= 15

    return min(100.0, max(0.0, score))


def _score_retention(segments, clip_duration, clip_lower):
    """Predict viewer retention."""
    score = 50.0

    for signal_name, patterns in RETENTION_SIGNALS.items():
        for pattern in patterns:
            if re.search(pattern, clip_lower):
                score += 8
                break

    if 15 <= clip_duration <= 45:
        score += 15
    elif 45 < clip_duration <= 60:
        score += 8
    elif clip_duration > 60:
        score -= 10
    elif clip_duration < 10:
        score -= 5

    if segments:
        seg_durations = [s.get("end", 0) - s.get("start", 0) for s in segments]
        if len(seg_durations) > 2:
            avg_dur = sum(seg_durations) / len(seg_durations)
            variance = sum((d - avg_dur) ** 2 for d in seg_durations) / len(seg_durations)
            if variance > 1.0:
                score += 10

    mid_point = clip_duration * 0.5
    mid_segs = [s for s in segments if abs(s.get("start", 0) - mid_point) < 3.0]
    mid_text = " ".join(s.get("text", "") for s in mid_segs).lower()
    if any(w in mid_text for w in ["but", "actually", "wait", "however", "then"]):
        score += 12

    if segments and len(segments) <= 2 and clip_duration > 20:
        score -= 10

    return min(100.0, max(0.0, score))


def _score_shareability(clip_lower, clip_duration, segments):
    """Predict shareability."""
    score = 45.0

    relatable_patterns = [
        r"\b(everyone|we all|you know when|that feeling|me too|same)\b",
        r"\b(sering kali|semua orang|pasti pernah|rasanya|sama)\b",
    ]
    for pattern in relatable_patterns:
        if re.search(pattern, clip_lower):
            score += 12
            break

    takeaway_patterns = [
        r"\b(lesson|takeaway|moral|remember this|the key|the point)\b",
        r"\b(pelajaran|hikmah|ingat ini|kunci|intinya)\b",
    ]
    for pattern in takeaway_patterns:
        if re.search(pattern, clip_lower):
            score += 10
            break

    if '"' in clip_lower or '"' in clip_lower or '"' in clip_lower:
        score += 8

    fact_patterns = [
        r"\b(did you know|fact|actually|turns out|the truth is)\b",
        r"\b(tahukah kamu|faktanya|sebenernya|ternyata|kebenarannya)\b",
    ]
    for pattern in fact_patterns:
        if re.search(pattern, clip_lower):
            score += 10
            break

    inspire_patterns = [
        r"\b(you can|never give up|believe|achieve|dream|possible)\b",
        r"\b(kamu bisa|jangan menyerah|percaya|capai|mimpi|mungkin)\b",
    ]
    for pattern in inspire_patterns:
        if re.search(pattern, clip_lower):
            score += 8
            break

    controversy_patterns = [
        r"\b(wrong|unpopular opinion|hot take|actually|nobody)\b",
        r"\b(salah|kontroversial|sebenarnya|justru|malah)\b",
    ]
    for pattern in controversy_patterns:
        if re.search(pattern, clip_lower):
            score += 8
            break

    if clip_duration <= 30:
        score += 8
    elif clip_duration <= 45:
        score += 4

    if clip_duration > 90:
        score -= 15

    return min(100.0, max(0.0, score))


def _score_trend_alignment(clip_lower, segments, face_data, clip_duration):
    """Score alignment with current viral trends."""
    score = 40.0
    detected = []

    for category, patterns in VIRAL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, clip_lower):
                score += TREND_SIGNALS.get(category, 0.05) * 100 * 0.3
                detected.append(category)
                break

    if face_data:
        face_present = face_data.get("faces_detected", 0)
        if face_present > 0:
            score += TREND_SIGNALS["face_to_camera"] * 100 * 0.3
            detected.append("face_to_camera")
        face_confidence = face_data.get("confidence", 0)
        if face_confidence > 0.8:
            score += 5

    if re.search(r"\b(before|after|then|now|used to|transformed)\b", clip_lower):
        score += TREND_SIGNALS["before_after"] * 100 * 0.2
        detected.append("before_after")

    if re.search(r"\b(myth|wrong|actually|not true|debunked)\b", clip_lower):
        score += TREND_SIGNALS["myth_busting"] * 100 * 0.2
        detected.append("myth_busting")

    if re.search(r"\b(unpopular|controversial|hot take|nobody wants)\b", clip_lower):
        score += TREND_SIGNALS["controversy"] * 100 * 0.2
        detected.append("controversy")

    anti_patterns_found = sum(1 for p in ANTI_VIRAL_PATTERNS if re.search(p, clip_lower))
    score -= anti_patterns_found * 8

    return min(100.0, max(0.0, score))


def _score_emotional_impact(segments, clip_lower):
    """Score emotional impact."""
    score = 35.0

    high_emotion = [
        r"\b(love|hate|amazing|terrible|incredible|awful|best|worst)\b",
        r"\b(cinta|benci|keren|jelek|luar biasa|terbaik|terburuk)\b",
        r"\b(!|omg|wow|woah|no way|are you serious)\b",
        r"\b(gila|buset|anjir|sialan|bangsat|mantap)\b",
    ]
    medium_emotion = [
        r"\b(surprised|shocked|happy|sad|angry|excited|scared|nervous)\b",
        r"\b(terkejut|senang|sedih|marah|bersemangat|takut|gugup)\b",
    ]

    high_count = sum(1 for p in high_emotion if re.search(p, clip_lower))
    medium_count = sum(1 for p in medium_emotion if re.search(p, clip_lower))

    score += high_count * 12
    score += medium_count * 7

    if segments:
        emotions_by_time = _track_emotion_timeline(segments)
        if len(set(emotions_by_time)) > 1:
            score += 15
        elif emotions_by_time:
            score += 5

    if re.search(r"\b(i |me |my |i'm|i was|i've)\b", clip_lower):
        score += 8

    vulnerable_patterns = [
        r"\b(i failed|i lost|i was wrong|i struggled|i was scared)\b",
        r"\b(gagal|kalah|salah|berjuang|takut)\b",
    ]
    for p in vulnerable_patterns:
        if re.search(p, clip_lower):
            score += 10
            break

    words = clip_lower.split()
    caps_words = sum(1 for w in words if w.isupper() and len(w) > 2)
    if caps_words > 0:
        score += min(10, caps_words * 3)

    return min(100.0, max(0.0, score))


def _score_information_density(clip_lower, clip_duration, segments):
    """Score information density."""
    score = 50.0

    total_words = len(clip_lower.split())
    wps = total_words / max(clip_duration, 1)

    if 2.5 <= wps <= 4.0:
        score += 20
    elif 2.0 <= wps < 2.5 or 4.0 < wps <= 4.5:
        score += 10
    elif wps > 4.5:
        score -= 5
    elif wps < 1.5:
        score -= 10

    words = clip_lower.split()
    if words:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio > 0.7:
            score += 15
        elif unique_ratio > 0.5:
            score += 8
        elif unique_ratio < 0.3:
            score -= 10

    numbers = len(re.findall(r"\b\d+\b", clip_lower))
    score += min(10, numbers * 3)

    specific_indicators = [
        r"\b(percent|percentage|study|research|data|statistics)\b",
        r"\b(persen|studi|riset|data|statistik)\b",
    ]
    for p in specific_indicators:
        if re.search(p, clip_lower):
            score += 8
            break

    filler_count = sum(1 for p in ANTI_VIRAL_PATTERNS if re.search(p, clip_lower))
    score -= filler_count * 5

    return min(100.0, max(0.0, score))


def _score_caption_virality(hook_text, style_name, clip_lower):
    """Score how viral the on-screen captions will be."""
    score = 50.0

    if hook_text:
        hook_lower = hook_text.lower()
        hook_len = len(hook_text)
        if 10 <= hook_len <= 40:
            score += 15
        elif hook_len < 10:
            score -= 5
        elif hook_len > 60:
            score -= 10

        power_words = ["secret", "truth", "nobody", "actually", "real",
                       "rahasia", "kebenaran", "sebenarnya", "nyatanya"]
        power_count = sum(1 for w in power_words if w in hook_lower)
        score += power_count * 8

        if hook_text.isupper():
            score += 5

    viral_styles = {"hormozi", "mrbeast", "mrbeast_v2", "tiktok_viral", "gaming"}
    if style_name and style_name.lower() in viral_styles:
        score += 12

    if re.search(r"\b(secret|truth|nobody|actually|real|never|always)\b", clip_lower):
        score += 8

    return min(100.0, max(0.0, score))


def _score_pacing(segments, clip_duration):
    """Score pacing quality."""
    score = 50.0

    if not segments or len(segments) < 2:
        return score + 10

    seg_durations = [s.get("end", 0) - s.get("start", 0) for s in segments]

    if len(seg_durations) > 1:
        avg = sum(seg_durations) / len(seg_durations)
        variance = sum((d - avg) ** 2 for d in seg_durations) / len(seg_durations)
        std_dev = math.sqrt(variance)

        if 1.0 < std_dev < 5.0:
            score += 20
        elif 0.5 < std_dev <= 1.0:
            score += 10
        elif std_dev > 5.0:
            score += 5

    pauses = []
    for i in range(1, len(segments)):
        gap = segments[i].get("start", 0) - segments[i-1].get("end", 0)
        if gap > 0:
            pauses.append(gap)

    if pauses:
        avg_pause = sum(pauses) / len(pauses)
        max_pause = max(pauses)
        if max_pause > 3.0:
            score -= 10
        elif avg_pause < 0.5:
            score += 8
        elif avg_pause < 1.0:
            score += 5

    seg_texts = [s.get("text", "") for s in segments]
    word_counts = [len(t.split()) for t in seg_texts if t.strip()]

    if len(word_counts) > 2:
        avg_words = sum(word_counts) / len(word_counts)
        variance_words = sum((w - avg_words) ** 2 for w in word_counts) / len(word_counts)
        if variance_words > 10:
            score += 12

    if 20 <= clip_duration <= 45:
        score += 5
    elif clip_duration > 60:
        score -= 5

    return min(100.0, max(0.0, score))


# -- Helper Functions --

def _track_emotion_timeline(segments):
    """Track emotional tone through segments."""
    emotions = []
    for seg in segments:
        text = seg.get("text", "").lower()
        if re.search(r"\b(happy|joy|love|excited|amazing|great|wonderful)\b", text):
            emotions.append("positive")
        elif re.search(r"\b(sad|angry|fear|worried|scared|terrible|awful)\b", text):
            emotions.append("negative")
        elif re.search(r"\b(surprised|shocked|wow|incredible|unbelievable)\b", text):
            emotions.append("surprise")
        else:
            emotions.append("neutral")
    return emotions


def _score_to_grade(score):
    """Convert 0-100 score to letter grade."""
    if score >= 85: return "S"
    if score >= 75: return "A"
    if score >= 60: return "B"
    if score >= 45: return "C"
    if score >= 30: return "D"
    return "F"


def _grade_to_verdict(grade, score):
    """Generate human-readable verdict."""
    verdicts = {
        "S": f"VIRAL GOLD - Score {score:.0f}/100. Exceptional viral potential. All dimensions strong.",
        "A": f"HIGHLY VIRAL - Score {score:.0f}/100. Strong viral potential with minor areas to optimize.",
        "B": f"GOOD - Score {score:.0f}/100. Solid clip that could perform well with the right audience.",
        "C": f"AVERAGE - Score {score:.0f}/100. May get views but unlikely to go viral without optimization.",
        "D": f"WEAK - Score {score:.0f}/100. Low viral potential. Consider revising or replacing.",
        "F": f"MISS - Score {score:.0f}/100. Very unlikely to perform. Rethink the clip selection.",
    }
    return verdicts.get(grade, "Unknown")


def _calculate_confidence(segments, clip_duration, text_length):
    """Calculate confidence in the virality score."""
    confidence = 0.5
    if text_length > 200: confidence += 0.2
    elif text_length > 100: confidence += 0.1
    elif text_length < 50: confidence -= 0.15

    if len(segments) > 5: confidence += 0.15
    elif len(segments) > 2: confidence += 0.05
    elif len(segments) < 2: confidence -= 0.1

    if 15 <= clip_duration <= 45: confidence += 0.1
    return min(1.0, max(0.1, confidence))


def _generate_recommendations(dimensions, detected_patterns):
    """Generate actionable recommendations based on weak dimensions."""
    recs = []
    if dimensions["hook_power"] < 60:
        recs.append("HOOK: Shift clip start to capture a stronger opening line. Look for pattern interrupts, bold claims, or questions in the first 3 seconds.")
    if dimensions["retention_prediction"] < 60:
        recs.append("RETENTION: Add a mid-clip pattern break or open loop to prevent the 50% drop-off. Consider shortening if over 45s.")
    if dimensions["shareability"] < 55:
        recs.append("SHARE: Look for relatable, educational, or controversial moments that people would forward to friends.")
    if dimensions["trend_alignment"] < 50:
        recs.append("TREND: This clip may not match current viral formats. Consider clips with before/after, myth-busting, or numbered list patterns.")
    if dimensions["emotional_impact"] < 50:
        recs.append("EMOTION: Find moments with stronger emotional language or personal vulnerability. Neutral content rarely goes viral.")
    if dimensions["information_density"] < 55:
        recs.append("DENSITY: Remove filler segments or trim pauses to increase value-per-second. Target 2.5-4.0 words per second.")
    if dimensions["caption_virality"] < 60:
        recs.append("CAPTION: Use a more viral style preset (hormozi, mrbeast) and ensure hook text is short and punchy (10-40 chars).")
    if dimensions["pacing_quality"] < 55:
        recs.append("PACING: Adjust boundaries for better rhythm. Mix short and long sentences. Remove long pauses between segments.")
    return recs


def _generate_evidence(dimensions, detected_patterns, trend_signals):
    """Generate evidence list explaining the score."""
    evidence = []
    sorted_dims = sorted(dimensions.items(), key=lambda x: x[1], reverse=True)
    top_3 = sorted_dims[:3]
    bottom_2 = sorted_dims[-2:]

    dim_labels = {
        "hook_power": "Hook Power", "retention_prediction": "Retention",
        "shareability": "Shareability", "trend_alignment": "Trend Alignment",
        "emotional_impact": "Emotional Impact", "information_density": "Info Density",
        "caption_virality": "Caption Virality", "pacing_quality": "Pacing",
    }

    for dim, val in top_3:
        if val >= 70:
            evidence.append(f"Strong {dim_labels.get(dim, dim)} ({val:.0f}/100)")
    for dim, val in bottom_2:
        if val < 50:
            evidence.append(f"Weak {dim_labels.get(dim, dim)} ({val:.0f}/100)")

    if detected_patterns:
        evidence.append(f"Viral patterns detected: {', '.join(detected_patterns[:5])}")
    if trend_signals:
        evidence.append(f"Trend signals: {', '.join(trend_signals[:5])}")
    return evidence


# -- Batch Scoring --

def score_batch(clips, transcript, full_duration, hook_texts=None, style_name=None, face_data=None):
    """Score multiple clips and return sorted by virality."""
    full_segments = transcript.get("segments", [])
    results = []

    for i, clip in enumerate(clips):
        clip_segs = [s for s in full_segments if s.get("start", 0) < clip["end"] and s.get("end", 0) > clip["start"]]
        clip_dur = clip["end"] - clip["start"]
        hook = hook_texts[i] if hook_texts and i < len(hook_texts) else None

        score = score_clip_virality(
            clip=clip, transcript=clip_segs, full_segments=full_segments,
            clip_duration=clip_dur, hook_text=hook, style_name=style_name, face_data=face_data,
        )
        results.append((clip, score))

    results.sort(key=lambda x: x[1].composite, reverse=True)

    log.info(f"[Virality] Ranked {len(results)} clips:")
    for i, (clip, score) in enumerate(results):
        log.info(f"  #{i+1} Score: {score.composite:.1f} ({score.grade}) [{clip['start']:.1f}s - {clip['end']:.1f}s]")

    return results


# -- API Response Format --

def score_to_api_dict(score):
    """Convert ViralityScore to API-friendly dict for frontend display."""
    return {
        "composite": round(score.composite, 1),
        "grade": score.grade,
        "verdict": score.verdict,
        "confidence": round(score.confidence, 2),
        "breakdown": score.breakdown,
        "evidence": score.evidence,
        "recommendations": score.recommendations,
        "detected_patterns": score.detected_patterns,
        "trend_signals": score.trend_signals,
        "scores": {
            "hook_power": round(score.hook_power, 1),
            "retention_prediction": round(score.retention_prediction, 1),
            "shareability": round(score.shareability, 1),
            "trend_alignment": round(score.trend_alignment, 1),
            "emotional_impact": round(score.emotional_impact, 1),
            "information_density": round(score.information_density, 1),
            "caption_virality": round(score.caption_virality, 1),
            "pacing_quality": round(score.pacing_quality, 1),
        },
    }
