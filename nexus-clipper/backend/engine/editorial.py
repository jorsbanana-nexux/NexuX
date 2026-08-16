"""
Nexus-Clipper V7.0 — Editorial Consciousness Engine
=====================================================
The brain that makes NexuX a conscious professional editor, not a rigid machine.

This module provides:
- Narrative structure analysis (setup, conflict, resolution, payoff)
- Emotional arc detection (sentiment trajectory through segments)
- Comedic timing awareness (setup → punchline patterns)
- Semantic coherence scoring (does this clip stand alone as a complete thought?)
- Momentum/energy analysis (rising action, climax, falling action)
- Contextual significance (does this segment matter to the whole story?)
- Hook intelligence (what makes the first 3 seconds compelling?)

Unlike the old keyword-matching approach, this module understands
WHAT is being said, not just HOW MANY buzzwords appear.
"""
import re
import math
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

log = logging.getLogger("nexus.editorial")


# ── Data Structures ───────────────────────────────────

@dataclass
class EditorialScore:
    """Multi-dimensional editorial evaluation of a clip candidate."""
    narrative_completeness: float = 0.0    # 0-1: Does the clip tell a complete story?
    emotional_arc: float = 0.0           # 0-1: Is there an emotional journey?
    hook_intelligence: float = 0.0       # 0-1: Is the opening genuinely compelling?
    coherence: float = 0.0              # 0-1: Does it stand alone as a thought?
    momentum: float = 0.0                # 0-1: Is there energy/escalation?
    comedic_timing: float = 0.0          # 0-1: Is there setup→punchline structure?
    contextual_significance: float = 0.0 # 0-1: Does this matter to the whole?
    uniqueness: float = 0.0              # 0-1: Is this non-generic content?
    
    evidence: List[str] = field(default_factory=list)  # WHY these scores
    verdict: str = ""  # "STRONG", "GOOD", "WEAK", "REJECT"
    
    @property
    def composite(self) -> float:
        """Weighted composite editorial score (0-1)."""
        weights = {
            "narrative_completeness": 0.18,
            "emotional_arc": 0.15,
            "hook_intelligence": 0.18,
            "coherence": 0.15,
            "momentum": 0.12,
            "comedic_timing": 0.05,
            "contextual_significance": 0.10,
            "uniqueness": 0.07,
        }
        return sum(getattr(self, k) * v for k, v in weights.items())


# ── Linguistic Patterns ──────────────────────────────

# Emotional markers — not just keywords, but emotional TRANSITIONS
EMOTIONAL_SHIFTS = {
    "curiosity_to_revelation": [
        (r"\b(what if|i wonder|have you ever|imagine if)\b", r"\b(actually|turns out|the truth is|here's what)\b"),
        (r"\b(nobody knows|nobody talks about)\b", r"\b(but actually|the reality is|in fact)\b"),
    ],
    "tension_to_release": [
        (r"\b(but then|suddenly|out of nowhere|wait)\b", r"\b(and that's when|so basically|which means)\b"),
        (r"\b(the problem was|here's the issue)\b", r"\b(that's why|so what we|the solution)\b"),
    ],
    "setup_to_punchline": [
        (r"\b(so|i was|my friend|this guy|she said|he said)\b.{0,40}$", r"\b(and then|but then|and she|and he|plot twist)\b"),
        (r"\b(you would think|you'd expect|normally)\b", r"\b(but no|but actually|not at all|wrong)\b"),
    ],
    "question_to_answer": [
        (r"\b(why|how|what makes|what's the secret)\b.*\?", r"\b(because|the answer|here's why|it's because)\b"),
        (r"\b(did you know|guess what)\b", r"\b(it turns out|apparently|the fact is)\b"),
    ],
}

# Narrative completeness markers
NARRATIVE_BEATS = {
    "setup": [
        r"\b(let me (explain|tell you)|so here's|to understand this|the context)\b",
        r"\b(background|context|context is|setting the stage)\b",
        r"\b(in the beginning|it started when|it all began)\b",
    ],
    "conflict": [
        r"\b(but|however|the problem|the challenge|what went wrong)\b",
        r"\b(nobody expected|it shouldn't have|against all odds)\b",
        r"\b(the issue was|here's where it gets|that's when things)\b",
    ],
    "escalation": [
        r"\b(and then|on top of that|to make matters|but wait|it gets worse|it gets better)\b",
        r"\b(not only|but also|additionally|furthermore|and here's the kicker)\b",
    ],
    "payoff": [
        r"\b(and that's why|so the lesson|the takeaway|moral of the story)\b",
        r"\b(which means|that's how|and that's what|the result)\b",
        r"\b(in the end|ultimately|at the end of the day)\b",
    ],
    "revelation": [
        r"\b(turns out|the truth is|actually|here's what nobody)\b",
        r"\b(what they don't tell you|the secret is|here's the real)\b",
        r"\b(and that changed everything|mind blown|that's the thing)\b",
    ],
}

# Hook intelligence patterns — what makes first 3 seconds genuinely compelling
HOOK_ARCHETYPES = {
    "pattern_interrupt": r"\b(stop|wait|hold on|listen|look|hey)\b",
    "bold_claim": r"\b(this (will|is going to|changed|is the)\b|you (need|have to|must)\b|never (again|do this)\b)",
    "curiosity_gap": r"\b(the truth about|what nobody|the secret|why you|the real reason)\b",
    "contrarian": r"\b(everyone is wrong|contrary to|despite what|people think|but actually)\b",
    "personal_stakes": r"\b(i (lost|made|found|discovered|quit|fired|failed)\b|my (biggest|worst|first))\b",
    "numbered_authority": r"\b(\d+ (things|reasons|ways|secrets|lessons|mistakes)\b)",
    "story_launch": r"\b(so (this|there|i)|let me tell you|story time|this happened)\b",
    "visual_command": r"\b(look at|check this out|watch this|see this)\b",
}

# Generic filler that reduces uniqueness
FILLER_PATTERNS = [
    r"\b(uh|um|like|you know|i mean|sort of|kind of|basically|literally)\b",
    r"\b(anyway|so yeah|and stuff|and things|whatever|blah)\b",
]

# Momentum indicators — energy shifts in language
ENERGY_MARKERS = {
    "rising": [r"\b(more|bigger|faster|escalating|intensifying|building up)\b",
               r"\b(!|all caps|increasingly|even more|not just)\b"],
    "peak": [r"\b(and then BOOM|that's when everything|the climax|peak|the moment)\b",
             r"\b(suddenly|out of nowhere|all of a sudden|just like that)\b"],
    "cooling": [r"\b(so basically|in summary|to wrap up|long story short|anyway)\b",
               r"\b(after that|moving on|next|so then)\b"],
}


# ── Core Analysis Functions ───────────────────────────

def analyze_editorial(
    segments: List[Dict],
    clip_start: float,
    clip_end: float,
    full_duration: float,
    full_segments: Optional[List[Dict]] = None,
) -> EditorialScore:
    """
    Perform editorial analysis on a clip candidate.
    
    This is the heart of NexuX's editorial consciousness. It evaluates
    a clip not by keyword counting, but by understanding narrative structure,
    emotional trajectory, and whether the clip works as a standalone piece.
    
    Args:
        segments: Transcript segments overlapping with the clip
        clip_start: Clip start time
        clip_end: Clip end time
        full_duration: Total video duration
        full_segments: All transcript segments (for context)
    
    Returns:
        EditorialScore with multi-dimensional evaluation + evidence
    """
    score = EditorialScore()
    evidence = []
    
    # Get text content
    clip_text = " ".join(s.get("text", "") for s in segments).strip()
    clip_lower = clip_text.lower()
    
    if not clip_lower or len(clip_lower) < 20:
        score.verdict = "REJECT"
        score.evidence.append("Clip has insufficient text content")
        return score
    
    # ── 1. Narrative Completeness ──
    # Does this clip contain setup → payoff? Or is it a fragment?
    beats_found = _detect_narrative_beats(clip_lower)
    score.narrative_completeness = _score_narrative_completeness(beats_found)
    if beats_found:
        beat_names = [b[0] for b in beats_found]
        evidence.append(f"Narrative beats: {', '.join(beat_names)}")
        if "payoff" in beat_names or "revelation" in beat_names:
            evidence.append("Clip has a satisfying conclusion")
        if "setup" in beat_names and ("payoff" in beat_names or "revelation" in beat_names):
            evidence.append("Complete narrative arc: setup → payoff")
    else:
        evidence.append("No clear narrative beats detected — clip may feel incomplete")
    
    # ── 2. Emotional Arc ──
    # Is there an emotional journey within the clip?
    emotional_trajectory = _analyze_emotional_arc(segments)
    score.emotional_arc = emotional_trajectory["score"]
    if emotional_trajectory["shifts"]:
        evidence.append(f"Emotional shifts: {len(emotional_trajectory['shifts'])} transitions detected")
        evidence.append(f"Arc type: {emotional_trajectory['arc_type']}")
    else:
        evidence.append("Flat emotional arc — energy may feel monotonous")
    
    # ── 3. Hook Intelligence ──
    # Evaluate the opening 3 seconds on a deeper level
    hook_text = _get_hook_text(segments, clip_start, max(3.0, (clip_end - clip_start) * 0.2))
    score.hook_intelligence = _score_hook_intelligence(hook_text)
    hook_type = _identify_hook_archetype(hook_text)
    if hook_type:
        evidence.append(f"Hook archetype: {hook_type} (strong opening)")
    else:
        evidence.append("No clear hook archetype — opening may not grab attention")
        score.hook_intelligence = max(0.2, score.hook_intelligence)  # floor
    
    # ── 4. Coherence (standalone thought) ──
    # Does this clip make sense on its own, without the surrounding context?
    score.coherence = _score_coherence(segments, clip_text)
    if score.coherence > 0.7:
        evidence.append("Clip stands alone as a complete thought")
    elif score.coherence < 0.4:
        evidence.append("Clip feels like a fragment — needs surrounding context to make sense")
    
    # ── 5. Momentum ──
    # Is there energy escalation or a sense of building toward something?
    momentum = _analyze_momentum(segments)
    score.momentum = momentum["score"]
    if momentum["trajectory"]:
        evidence.append(f"Momentum: {momentum['trajectory']}")
    else:
        evidence.append("Steady energy — no escalation or climax")
    
    # ── 6. Comedic Timing ──
    # Is there a setup → punchline structure?
    comedic = _detect_comedic_timing(clip_lower, segments)
    score.comedic_timing = comedic["score"]
    if comedic["detected"]:
        evidence.append(f"Comedic structure: {comedic['pattern']}")
    
    # ── 7. Contextual Significance ──
    # Does this segment matter to the overall video?
    if full_segments and full_duration > 0:
        score.contextual_significance = _score_contextual_significance(
            clip_start, clip_end, full_duration, segments, full_segments
        )
        if score.contextual_significance > 0.7:
            evidence.append("Highly significant segment in the context of the full video")
        elif score.contextual_significance < 0.3:
            evidence.append("Low contextual significance — may be filler or tangent")
    
    # ── 8. Uniqueness ──
    # Is this non-generic content? Does it avoid filler?
    score.uniqueness = _score_uniqueness(clip_lower)
    if score.uniqueness < 0.3:
        evidence.append("High filler content — clip may feel generic")
    
    # ── Verdict ──
    comp = score.composite
    if comp >= 0.7:
        score.verdict = "STRONG"
    elif comp >= 0.5:
        score.verdict = "GOOD"
    elif comp >= 0.3:
        score.verdict = "WEAK"
    else:
        score.verdict = "REJECT"
    
    score.evidence = evidence
    return score


# ── Narrative Beat Detection ─────────────────────────

def _detect_narrative_beats(text: str) -> List[Tuple[str, str]]:
    """Detect narrative structure beats in text."""
    beats = []
    for beat_name, patterns in NARRATIVE_BEATS.items():
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                beats.append((beat_name, pattern))
                break  # one match per beat type is enough
    return beats


def _score_narrative_completeness(beats: List[Tuple[str, str]]) -> float:
    """Score how complete the narrative arc is (0-1)."""
    if not beats:
        return 0.15
    
    beat_names = set(b[0] for b in beats)
    
    # Full arc: setup + conflict + payoff/revelation
    if "setup" in beat_names and ("payoff" in beat_names or "revelation" in beat_names):
        if "conflict" in beat_names or "escalation" in beat_names:
            return 1.0  # Complete narrative arc
        return 0.8  # Setup + payoff without conflict
    
    # Has a payoff or revelation at least
    if "payoff" in beat_names or "revelation" in beat_names:
        return 0.65
    
    # Has escalation (building energy)
    if "escalation" in beat_names:
        return 0.5
    
    # Has setup only (incomplete)
    if "setup" in beat_names:
        return 0.3
    
    return 0.25


# ── Emotional Arc Analysis ────────────────────────────

def _analyze_emotional_arc(segments: List[Dict]) -> Dict:
    """Analyze the emotional trajectory through clip segments."""
    if len(segments) < 2:
        return {"score": 0.2, "shifts": [], "arc_type": "flat"}
    
    # Calculate per-segment emotional intensity
    intensities = []
    for seg in segments:
        text = seg.get("text", "").lower()
        intensity = _segment_emotional_intensity(text)
        intensities.append(intensity)
    
    # Detect shifts (significant changes in intensity)
    shifts = []
    for i in range(1, len(intensities)):
        delta = intensities[i] - intensities[i-1]
        if abs(delta) > 0.15:
            shifts.append({
                "index": i,
                "direction": "up" if delta > 0 else "down",
                "magnitude": abs(delta),
            })
    
    # Classify arc type
    arc_type = "flat"
    score = 0.2
    if len(intensities) >= 3:
        first_third = sum(intensities[:len(intensities)//3]) / max(len(intensities)//3, 1)
        last_third = sum(intensities[-len(intensities)//3:]) / max(len(intensities)//3, 1)
        mid = sum(intensities) / len(intensities)
        
        if last_third > first_third + 0.15:
            arc_type = "rising"  # builds to climax
            score = 0.7 + min(0.3, (last_third - first_third))
        elif first_third > last_third + 0.15 and last_third < mid:
            arc_type = "falling"  # starts strong, cools
            score = 0.4
        elif max(intensities) - min(intensities) > 0.25:
            arc_type = "dynamic"  # varying intensity
            score = 0.6
        elif len(shifts) >= 2:
            arc_type = "fluctuating"
            score = 0.55
    
    return {"score": min(1.0, score), "shifts": shifts, "arc_type": arc_type}


def _segment_emotional_intensity(text: str) -> float:
    """Estimate emotional intensity of a text segment (0-1)."""
    if not text:
        return 0.3
    
    score = 0.3  # baseline
    
    # Question marks = curiosity/engagement
    if "?" in text:
        score += 0.1
    
    # Exclamation = excitement
    excl_count = text.count("!")
    score += min(0.2, excl_count * 0.1)
    
    # Emotional words
    high_energy = ["amazing", "incredible", "shocking", "crazy", "insane", "wow",
                   "unbelievable", "terrifying", "hilarious", "devastating", "mengerikan",
                   "menakjubkan", "gila", "buset"]
    score += min(0.2, sum(0.05 for w in high_energy if w in text))
    
    # Intensifiers
    intensifiers = ["very", "really", "so", "extremely", "absolutely", "literally",
                    "totally", "completely", "actually", "betul", "banget", "sangat"]
    score += min(0.1, sum(0.02 for w in intensifiers if w in text))
    
    # Hedging/filler reduces intensity
    hedge = ["maybe", "i guess", "sort of", "i think maybe", "perhaps", "kinda"]
    score -= min(0.1, sum(0.03 for w in hedge if w in text))
    
    # ALL CAPS words = shouting/intensity
    caps_words = sum(1 for w in text.split() if len(w) > 2 and w.isupper())
    score += min(0.15, caps_words * 0.05)
    
    return max(0.1, min(1.0, score))


# ── Hook Intelligence ─────────────────────────────────

def _get_hook_text(segments: List[Dict], clip_start: float, hook_duration: float) -> str:
    """Extract text from the first N seconds of the clip."""
    hook_end = clip_start + hook_duration
    return " ".join(
        s.get("text", "")
        for s in segments
        if s.get("start", 0) < hook_end
    ).lower().strip()


def _score_hook_intelligence(hook_text: str) -> float:
    """Score hook quality on a deeper level than keyword matching."""
    if not hook_text or len(hook_text) < 5:
        return 0.15
    
    score = 0.2  # baseline for having any content
    
    # Check against archetypal hook patterns
    for archetype, pattern in HOOK_ARCHETYPES.items():
        if re.search(pattern, hook_text, re.IGNORECASE):
            score += 0.25
            break  # one strong archetype is enough
    
    # Brevity = punchiness (short hooks are stronger)
    word_count = len(hook_text.split())
    if word_count <= 8:
        score += 0.2
    elif word_count <= 15:
        score += 0.1
    elif word_count > 30:
        score -= 0.1  # Too verbose for a hook
    
    # Questions in hook = curiosity
    if "?" in hook_text:
        score += 0.15
    
    # Numbers in hook = specificity
    if re.search(r'\b\d+\b', hook_text):
        score += 0.1
    
    # Personal pronouns = relatability
    if re.search(r'\b(i|you|we|my|your)\b', hook_text):
        score += 0.1
    
    # Negative contractions = tension
    if re.search(r"\b(don't|never|nobody|can't|won't|stop)\b", hook_text):
        score += 0.1
    
    return min(1.0, score)


def _identify_hook_archetype(hook_text: str) -> Optional[str]:
    """Identify which hook archetype is being used."""
    for archetype, pattern in HOOK_ARCHETYPES.items():
        if re.search(pattern, hook_text, re.IGNORECASE):
            return archetype.replace("_", " ").title()
    return None


# ── Coherence Scoring ─────────────────────────────────

def _score_coherence(segments: List[Dict], full_text: str) -> float:
    """Score whether a clip stands alone as a coherent thought."""
    if not segments or not full_text:
        return 0.2
    
    score = 0.3  # baseline
    
    # Does it start with a self-contained opening?
    first_text = segments[0].get("text", "").strip().lower() if segments else ""
    self_contained_openers = [
        r"^(so|this|here|let me|i'm going to|the|imagine|what if|did you know)",
        r"^(people|everyone|most|nobody|the truth)",
    ]
    for pattern in self_contained_openers:
        if re.search(pattern, first_text):
            score += 0.15
            break
    
    # Does it end with a conclusion/punchline?
    last_text = segments[-1].get("text", "").strip().lower() if segments else ""
    conclusive_endings = [
        r"(that's why|so |which means|the lesson|the point|takeaway|moral|bottom line)$",
        r"(that's it|and that's|there you go|that's the story|crazy right)$",
        r"(!|\?|right\?)$",
    ]
    for pattern in conclusive_endings:
        if re.search(pattern, last_text):
            score += 0.2
            break
    
    # Has a clear topic/subject (not just rambling)
    word_count = len(full_text.split())
    if 20 <= word_count <= 120:
        score += 0.15  # Good length for standalone
    elif word_count < 10:
        score -= 0.1   # Too short to be meaningful
    elif word_count > 200:
        score -= 0.1   # Too long, may be rambling
    
    # References to external context (bad for standalone)
    context_refs = [
        r"\b(as i (mentioned|said) earlier|like i said|going back to|remember when)\b",
        r"\b(previously|earlier i|before that|as we discussed)\b",
    ]
    for pattern in context_refs:
        if re.search(pattern, full_text, re.IGNORECASE):
            score -= 0.15
            break
    
    # Discourse markers = structured thinking
    markers = ["because", "so", "which", "that's why", "therefore", "meaning"]
    marker_count = sum(1 for m in markers if m in full_text.lower())
    score += min(0.1, marker_count * 0.03)
    
    return max(0.1, min(1.0, score))


# ── Momentum Analysis ─────────────────────────────────

def _analyze_momentum(segments: List[Dict]) -> Dict:
    """Analyze energy trajectory through the clip."""
    if len(segments) < 2:
        return {"score": 0.3, "trajectory": "static"}
    
    # Word rate per segment as energy proxy
    rates = []
    for seg in segments:
        text = seg.get("text", "")
        dur = max(seg.get("end", 0) - seg.get("start", 0), 0.1)
        wps = len(text.split()) / dur
        rates.append(wps)
    
    # Check for escalation pattern
    first_half = sum(rates[:len(rates)//2]) / max(len(rates)//2, 1)
    second_half = sum(rates[len(rates)//2:]) / max(len(rates) - len(rates)//2, 1)
    
    trajectory = "static"
    score = 0.3
    
    if second_half > first_half * 1.3:
        trajectory = "accelerating"
        score = 0.7 + min(0.3, (second_half - first_half) / max(first_half, 0.1) * 0.5)
    elif second_half < first_half * 0.7:
        trajectory = "decelerating"
        score = 0.4
    elif max(rates) > min(rates) * 2:
        trajectory = "variable"
        score = 0.55
    
    # Check for explicit energy markers
    full_text = " ".join(s.get("text", "") for s in segments).lower()
    for energy_type, patterns in ENERGY_MARKERS.items():
        for pattern in patterns:
            if re.search(pattern, full_text, re.IGNORECASE):
                if energy_type == "rising" and trajectory == "static":
                    trajectory = "rising (linguistic)"
                    score = max(score, 0.55)
                elif energy_type == "peak":
                    trajectory = "peaks"
                    score = max(score, 0.65)
                break
    
    return {"score": min(1.0, score), "trajectory": trajectory}


# ── Comedic Timing ───────────────────────────────────

def _detect_comedic_timing(text: str, segments: List[Dict]) -> Dict:
    """Detect setup → punchline patterns."""
    detected = False
    pattern = ""
    score = 0.15
    
    for shift_name, patterns in EMOTIONAL_SHIFTS.items():
        if shift_name != "setup_to_punchline":
            continue
        for setup_pat, punch_pat in patterns:
            if re.search(setup_pat, text, re.IGNORECASE) and re.search(punch_pat, text, re.IGNORECASE):
                detected = True
                pattern = shift_name
                score = 0.7
                break
    
    # Check for comedic timing in segment boundaries
    if not detected and len(segments) >= 2:
        for i in range(1, len(segments)):
            prev_text = segments[i-1].get("text", "").lower()
            curr_text = segments[i].get("text", "").lower()
            
            # Setup: normal statement
            # Punchline: sudden shift (but, and then, actually)
            if re.search(r"\b(but then|and then|but actually|plot twist|twist:)\b", curr_text):
                # Check if previous segment was a setup (longer, calmer)
                prev_dur = segments[i-1].get("end", 0) - segments[i-1].get("start", 0)
                curr_dur = segments[i].get("end", 0) - segments[i].get("start", 0)
                if prev_dur > curr_dur * 1.5:  # Setup longer than punchline = comedic timing
                    detected = True
                    pattern = "timing-based setup → punchline"
                    score = 0.6
                    break
    
    # Laughter indicators
    if re.search(r"\b(haha|lol|lmao|that's funny|joke aside)\b", text, re.IGNORECASE):
        score = max(score, 0.4)
        if not detected:
            pattern = "humor-adjacent"
    
    return {"detected": detected, "pattern": pattern, "score": min(1.0, score)}


# ── Contextual Significance ──────────────────────────

def _score_contextual_significance(
    clip_start: float,
    clip_end: float,
    full_duration: float,
    clip_segments: List[Dict],
    full_segments: List[Dict],
) -> float:
    """Score how significant this segment is to the overall video."""
    score = 0.3
    
    # Position in video (climax tends to be 60-80% through)
    pos_ratio = clip_start / max(full_duration, 1)
    if 0.15 <= pos_ratio <= 0.85:
        score += 0.15  # Not at the very start or end
    if 0.4 <= pos_ratio <= 0.75:
        score += 0.1   # "Meat" of the content
    
    # Duration proportion (neither too short nor too long relative to video)
    clip_dur = clip_end - clip_start
    dur_ratio = clip_dur / max(full_duration, 1)
    if 0.02 <= dur_ratio <= 0.15:
        score += 0.1   # Reasonable proportion
    
    # Keyword density relative to full video
    clip_text = " ".join(s.get("text", "") for s in clip_segments).lower()
    full_text = " ".join(s.get("text", "") for s in full_segments).lower()
    
    clip_words = set(clip_text.split())
    full_words = set(full_text.split())
    
    if clip_words and full_words:
        # Information density: does this clip have unique vocabulary?
        unique_ratio = len(clip_words - full_words) / max(len(clip_words), 1)
        # Lower unique ratio = more central vocabulary = more significant
        if unique_ratio < 0.3:
            score += 0.1
        elif unique_ratio > 0.7:
            score -= 0.05  # Mostly unique words = tangent?
    
    # Is this segment referenced later? (forward references = significance)
    clip_end_idx = 0
    for i, seg in enumerate(full_segments):
        if seg.get("start", 0) >= clip_end:
            clip_end_idx = i
            break
    
    later_text = " ".join(
        s.get("text", "") for s in full_segments[clip_end_idx:]
    ).lower()
    
    # If later segments reference content from this clip, it's significant
    clip_keywords = [w for w in clip_text.split() if len(w) > 5 and w.isalpha()]
    if clip_keywords:
        referenced = sum(1 for w in clip_keywords[:10] if w in later_text)
        if referenced > 3:
            score += 0.15  # Referenced later = significant
    
    return max(0.1, min(1.0, score))


# ── Uniqueness ────────────────────────────────────────

def _score_uniqueness(text: str) -> float:
    """Score how non-generic/non-filler the content is."""
    if not text:
        return 0.1
    
    word_count = len(text.split())
    if word_count == 0:
        return 0.1
    
    # Count filler words
    filler_count = 0
    for pattern in FILLER_PATTERNS:
        filler_count += len(re.findall(pattern, text, re.IGNORECASE))
    
    filler_ratio = filler_count / max(word_count, 1)
    
    # Low filler = high uniqueness
    score = 1.0 - min(0.8, filler_ratio * 4)
    
    # Very short clips with few unique words
    unique_words = set(w.lower() for w in text.split() if len(w) > 2)
    type_token_ratio = len(unique_words) / max(word_count, 1)
    
    if type_token_ratio < 0.3:
        score -= 0.15  # Repetitive
    elif type_token_ratio > 0.6:
        score += 0.1   # Rich vocabulary
    
    return max(0.1, min(1.0, score))


# ── Batch Analysis ────────────────────────────────────

def batch_editorial_analysis(
    candidates: List[Dict],
    segments: List[Dict],
    full_duration: float,
) -> List[Dict]:
    """
    Run editorial analysis on all clip candidates and return enriched results.
    
    This enriches each candidate with editorial scores and evidence,
    then re-ranks based on the composite editorial score blended with
    the original algorithmic score.
    """
    full_segments = segments  # Full transcript segments for context
    
    for candidate in candidates:
        clip_start = candidate["start"]
        clip_end = candidate["end"]
        
        # Get segments overlapping this clip
        clip_segs = [
            s for s in full_segments
            if s.get("start", 0) < clip_end and s.get("end", 0) > clip_start
        ]
        
        editorial = analyze_editorial(
            clip_segs, clip_start, clip_end, full_duration, full_segments
        )
        
        # Enrich candidate with editorial data
        candidate["editorial"] = {
            "narrative_completeness": round(editorial.narrative_completeness, 3),
            "emotional_arc": round(editorial.emotional_arc, 3),
            "hook_intelligence": round(editorial.hook_intelligence, 3),
            "coherence": round(editorial.coherence, 3),
            "momentum": round(editorial.momentum, 3),
            "comedic_timing": round(editorial.comedic_timing, 3),
            "contextual_significance": round(editorial.contextual_significance, 3),
            "uniqueness": round(editorial.uniqueness, 3),
            "composite": round(editorial.composite, 3),
            "verdict": editorial.verdict,
            "evidence": editorial.evidence,
        }
        
        # Blend editorial score with algorithmic score
        # Editorial gets 50% weight (it's the editorial consciousness)
        original = candidate.get("score", 0)
        editorial_score = editorial.composite
        candidate["score"] = round(original * 0.4 + editorial_score * 0.6, 3)
    
    # Re-sort by blended score
    candidates.sort(key=lambda x: x["score"], reverse=True)
    
    log.info(f"[Editorial] Enriched {len(candidates)} candidates. "
             f"Top editorial verdict: {candidates[0]['editorial']['verdict'] if candidates else 'none'}")
    
    return candidates
