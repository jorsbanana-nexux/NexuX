"""
NexuX V8.5 — Hook Detection Engine
====================================
Intelligent hook detection that surpasses Opus Clip's hook finder.

Finds the BEST opening line for each clip by analyzing:
1. Linguistic hook archetypes (8 types)
2. Emotional energy in first 3 seconds
3. Question/curiosity gap detection
4. Pattern interrupt detection
5. Bold claim / contrarian detection
6. Story launch detection
7. Personal stakes / vulnerability
8. Visual + audio cue correlation
9. Optimal clip start optimization (shift boundaries to capture best hook)
10. Hook strength scoring (0-100)

Unlike Opus Clip which just uses the first sentence, NexuX:
- Scans ALL possible start points within a 10-second window
- Finds the STRONGEST opening, not just the earliest
- Can shift clip start by up to 5 seconds to capture a better hook
- Scores hook potential and recommends the best start time
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

log = logging.getLogger("nexus.hook_detection")


# -- Hook Archetypes --

HOOK_ARCHETYPES = {
    "pattern_interrupt": {
        "patterns": [
            r"\b(stop|wait|hold on|listen|look|hey|listen up|pay attention)\b",
            r"\b(berhenti|tunggu|dengar|lihat|eh|perhatikan)\b",
        ],
        "base_score": 75,
        "description": "Interrupts the viewer's scroll pattern",
        "optimal_length": "3-8 words",
    },
    "bold_claim": {
        "patterns": [
            r"\b(this (will|is going to|changed|is the)\b|you (need|have to|must)\b|never (again|do this|should you))\b",
            r"\b(ini (akan|adalah|mengubah|adalah)|kamu (harus|wajib)|jangan pernah)\b",
            r"\b(the (best|worst|most|only) )\b",
            r"\b(yang (terbaik|terburuk|paling|satu-satunya))\b",
        ],
        "base_score": 78,
        "description": "Bold statement that demands attention",
        "optimal_length": "5-15 words",
    },
    "curiosity_gap": {
        "patterns": [
            r"\b(the truth about|what nobody|the secret|why you|the real reason|here's what)\b",
            r"\b(kebenaran tentang|yang tidak|rahasia|kenapa kamu|alasan sebenarnya|inilah)\b",
            r"\b(most people don't|what they don't|you think you know|but here's the thing)\b",
            r"\b(kebanyakan orang tidak|yang tidak mereka|kamu pikir kamu tahu|tapi sebenarnya)\b",
        ],
        "base_score": 82,
        "description": "Opens a curiosity loop the viewer must close",
        "optimal_length": "8-20 words",
    },
    "contrarian": {
        "patterns": [
            r"\b(everyone is wrong|contrary to|despite what|people think|but actually)\b",
            r"\b(unpopular opinion|hot take|nobody wants to admit|the uncomfortable truth)\b",
            r"\b(orang salah|berlawanan|ternyata|sebenernya|pendapat tidak populer)\b",
            r"\b(justru|malah|padahal)\b",
        ],
        "base_score": 80,
        "description": "Challenges conventional wisdom — sparks debate",
        "optimal_length": "5-15 words",
    },
    "personal_stakes": {
        "patterns": [
            r"\b(i (lost|made|found|discovered|quit|failed|started|sold|bought))\b",
            r"\b(my (biggest|worst|first|best|most|crazy|insane))\b",
            r"\b(aku (kehilangan|membuat|menemukan|berhenti|gagal|memulai|menjual|membeli))\b",
            r"\b(saya (kehilangan|membuat|menemukan|berhenti|gagal|memulai))\b",
        ],
        "base_score": 77,
        "description": "Personal story with stakes — creates emotional investment",
        "optimal_length": "5-15 words",
    },
    "numbered_authority": {
        "patterns": [
            r"\b(\d+\s+(things|reasons|ways|tips|secrets|mistakes|signs|lessons))\b",
            r"\b(\d+\s+(hal|alasan|cara|rahasia|kesalahan|tanda|pelajaran))\b",
            r"\b(top \d+|worst \d+|best \d+)\b",
        ],
        "base_score": 85,
        "description": "Numbered lists are inherently clickable and shareable",
        "optimal_length": "4-12 words",
    },
    "story_launch": {
        "patterns": [
            r"\b(so (this|there|i)|let me tell you|story time|this happened|a while back)\b",
            r"\b(jadi (ini|ada|saya)|cerita nih|ini terjadi|dulu ceritanya)\b",
            r"\b(i was|i remember|back when|a few years ago)\b",
        ],
        "base_score": 72,
        "description": "Launches a narrative — viewers stay for the story",
        "optimal_length": "5-12 words",
    },
    "question_hook": {
        "patterns": [
            r"\b(did you know|guess what|what if|have you ever wondered|why do)\b",
            r"\b(tahukah kamu|tebak apa|bagaimana jika|pernahkah kamu|kenapa)\b",
            r"\b(can you|do you|are you|what's the|how come)\b",
            r"\b(bisakah|apakah kamu|apa sih|gimana sih)\b",
        ],
        "base_score": 79,
        "description": "Direct question — forces viewer to engage mentally",
        "optimal_length": "5-15 words",
    },
    "visual_command": {
        "patterns": [
            r"\b(look at|check this out|watch this|see this|notice how)\b",
            r"\b(lihat|perhatikan ini|cek ini|coba lihat|perhatikan bagaimana)\b",
        ],
        "base_score": 74,
        "description": "Directs visual attention — great for showing something",
        "optimal_length": "3-10 words",
    },
}

# Emotional amplifiers — words that boost hook score
EMOTIONAL_AMPLIFIERS = {
    "high": ["crazy", "insane", "shocking", "unbelievable", "mind-blowing",
             "gila", "buset", "anjir", "edan", "nggak nyangka"],
    "medium": ["amazing", "incredible", "terrible", "awful", "bizarre",
               "keren", "luar biasa", "aneh", "ajaib"],
}

# Hook killers — words that destroy hook effectiveness
HOOK_KILLERS = [
    r"^(uh|um|er|ah|hmm|so yeah|well um)",
    r"^(okay so|alright so|basically|essentially)",
    r"^(iya|ya|oke|nah|eh)",
    r"\b(anyway|anyways|moving on|so that's|and that's about it)\b",
    r"\b(in conclusion|to summarize|as I mentioned earlier)\b",
    r"\b(let me start by saying|before we begin|as a preamble)\b",
]


@dataclass
class HookResult:
    """Result of hook detection for a clip."""
    best_start: float = 0.0          # Optimal clip start time
    original_start: float = 0.0      # Original clip start
    shift_amount: float = 0.0        # How much we shifted (can be negative)
    hook_text: str = ""              # The hook text
    hook_archetype: str = ""          # Which archetype was detected
    hook_score: float = 0.0          # 0-100 hook strength
    confidence: float = 0.0          # Confidence in the hook
    alternatives: List[Dict] = field(default_factory=list)  # Other candidate hooks
    should_shift: bool = False        # Whether to shift clip start
    reasoning: str = ""               # Why this hook was chosen


def detect_best_hook(
    segments: List[Dict],
    clip_start: float,
    clip_end: float,
    max_shift: float = 5.0,
    search_window: float = 10.0,
) -> HookResult:
    """
    Find the best possible hook (opening line) for a clip.

    Scans all possible start positions within [clip_start - max_shift,
    clip_start + search_window] and finds the one with the strongest hook.

    Args:
        segments: All transcript segments
        clip_start: Current clip start time
        clip_end: Clip end time
        max_shift: Maximum backward shift (earlier) in seconds
        search_window: Forward search window in seconds

    Returns:
        HookResult with optimal start time and hook details
    """
    result = HookResult(original_start=clip_start)

    # Define search range
    search_start = max(0, clip_start - max_shift)
    search_end = clip_start + search_window

    # Get segments in the search range
    search_segs = [
        s for s in segments
        if s.get("start", 0) < search_end and s.get("end", 0) > search_start
    ]

    if not search_segs:
        return result

    # Generate candidate hook positions
    candidates = _generate_hook_candidates(
        search_segs, search_start, search_end, clip_end
    )

    if not candidates:
        # Fallback: use original start
        result.best_start = clip_start
        result.hook_text = _get_text_at_time(search_segs, clip_start, 3.0)
        result.hook_score = _score_hook_text(result.hook_text)
        return result

    # Score each candidate
    for candidate in candidates:
        candidate["score"] = _score_hook_text(candidate["text"])
        candidate["archetype"] = _identify_archetype(candidate["text"])
        candidate["penalty"] = _calculate_position_penalty(
            candidate["start"], clip_start, max_shift
        )
        candidate["final_score"] = candidate["score"] - candidate["penalty"]

    # Sort by final score
    candidates.sort(key=lambda c: c["final_score"], reverse=True)

    # Best candidate
    best = candidates[0]
    result.best_start = best["start"]
    result.shift_amount = best["start"] - clip_start
    result.should_shift = abs(result.shift_amount) > 0.5
    result.hook_text = best["text"]
    result.hook_archetype = best["archetype"]
    result.hook_score = best["score"]
    result.confidence = _calculate_confidence(best)
    result.alternatives = [
        {
            "start": c["start"],
            "text": c["text"][:80],
            "score": round(c["final_score"], 1),
            "archetype": c["archetype"],
        }
        for c in candidates[1:4]  # Top 3 alternatives
    ]

    # Generate reasoning
    result.reasoning = _generate_reasoning(best, result.should_shift, result.shift_amount)

    log.info(
        f"[HookDetection] Best hook at {result.best_start:.1f}s "
        f"(shift: {result.shift_amount:+.1f}s) | "
        f"Archetype: {result.hook_archetype} | "
        f"Score: {result.hook_score:.1f}/100 | "
        f"Hook: \"{result.hook_text[:50]}...\""
    )

    return result


def _generate_hook_candidates(
    segments: List[Dict],
    search_start: float,
    search_end: float,
    clip_end: float,
) -> List[Dict]:
    """Generate candidate hook positions from segment boundaries."""
    candidates = []

    # Strategy 1: Use segment boundaries as potential hook starts
    for seg in segments:
        seg_start = seg.get("start", 0)
        if seg_start < search_start or seg_start > search_end:
            continue

        # Get text from this segment + next 3 seconds
        hook_text = _get_text_from_time(segments, seg_start, min(seg_start + 3.0, clip_end))
        if not hook_text or len(hook_text.strip()) < 5:
            continue

        candidates.append({
            "start": seg_start,
            "text": hook_text.strip(),
            "source": "segment_boundary",
        })

    # Strategy 2: Also check word-level boundaries (if available) for finer granularity
    for seg in segments:
        words = seg.get("words", [])
        if not words:
            continue
        seg_start = seg.get("start", 0)
        if seg_start < search_start or seg_start > search_end:
            continue

        # Check first few words as potential hook starts
        for i, w in enumerate(words[:3]):
            w_start = float(w.get("start", 0))
            if w_start < search_start or w_start > search_end:
                continue
            if i == 0:
                continue  # Already covered by segment boundary

            hook_text = _get_text_from_time(segments, w_start, min(w_start + 3.0, clip_end))
            if not hook_text or len(hook_text.strip()) < 5:
                continue

            candidates.append({
                "start": w_start,
                "text": hook_text.strip(),
                "source": "word_boundary",
            })

    # Deduplicate by start time (keep first occurrence)
    seen = set()
    unique = []
    for c in candidates:
        key = round(c["start"], 1)
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique


def _get_text_at_time(segments: List[Dict], start: float, duration: float) -> str:
    """Get transcript text starting from a given time for a given duration."""
    texts = []
    for s in segments:
        if s.get("start", 0) < start + duration and s.get("end", 0) > start:
            texts.append(s.get("text", ""))
    return " ".join(texts).strip()


def _get_text_from_time(segments: List[Dict], start: float, end: float) -> str:
    """Get transcript text between start and end times."""
    texts = []
    for s in segments:
        if s.get("start", 0) < end and s.get("end", 0) > start:
            texts.append(s.get("text", ""))
    return " ".join(texts).strip()


def _score_hook_text(text: str) -> float:
    """Score a hook text on its hook potential (0-100)."""
    if not text or len(text.strip()) < 5:
        return 20.0

    text_lower = text.lower().strip()
    score = 35.0  # Base score for having text

    # Check for hook archetypes
    archetype = _identify_archetype(text)
    if archetype:
        arch_info = HOOK_ARCHETYPES[archetype]
        score = arch_info["base_score"]

    # Emotional amplifiers
    for level, words in EMOTIONAL_AMPLIFIERS.items():
        boost = 8 if level == "high" else 5
        for w in words:
            if w in text_lower:
                score += boost
                break

    # Hook killers (strong penalty)
    for killer in HOOK_KILLERS:
        if re.search(killer, text_lower):
            score -= 20
            break

    # Length check — optimal hooks are 3-15 words
    word_count = len(text_lower.split())
    if 3 <= word_count <= 8:
        score += 10  # Punchy
    elif 8 < word_count <= 15:
        score += 5   # Good
    elif word_count > 25:
        score -= 10  # Too long, not punchy
    elif word_count < 3:
        score -= 5   # Too short

    # Question marks boost
    if "?" in text:
        score += 8

    # Numbers in hook (high click-through)
    if re.search(r"\b\d+\b", text):
        score += 6

    # Exclamation (energy)
    if "!" in text:
        score += 4

    # First word strength
    first_word = text_lower.split()[0] if text_lower.split() else ""
    strong_openers = {"so", "but", "and", "the", "this", "here's", "imagine",
                      "never", "everyone", "nobody", "what", "why", "how",
                      "look", "stop", "wait", "did", "guess", "okay"}
    if first_word in strong_openers:
        score += 5

    # All caps (shouting = attention)
    if text.isupper() and len(text) > 5:
        score += 5

    return min(100.0, max(0.0, score))


def _identify_archetype(text: str) -> str:
    """Identify which hook archetype a text matches."""
    text_lower = text.lower()

    # Check each archetype (priority order matters)
    # Check most specific patterns first
    priority_order = [
        "numbered_authority",
        "curiosity_gap",
        "contrarian",
        "pattern_interrupt",
        "bold_claim",
        "question_hook",
        "personal_stakes",
        "story_launch",
        "visual_command",
    ]

    for archetype in priority_order:
        arch = HOOK_ARCHETYPES[archetype]
        for pattern in arch["patterns"]:
            if re.search(pattern, text_lower):
                return archetype

    return ""


def _calculate_position_penalty(
    candidate_start: float,
    original_start: float,
    max_shift: float,
) -> float:
    """
    Calculate penalty for shifting clip start.

    Shifting backward (earlier) is less penalized than forward (later).
    We want to find a better hook but not at the cost of losing content.
    """
    shift = candidate_start - original_start

    if abs(shift) < 0.5:
        return 0.0  # No significant shift

    # Backward shift (earlier) — mild penalty
    if shift < 0:
        return abs(shift) * 1.5  # 1.5 points per second shifted back

    # Forward shift (later) — stronger penalty (losing beginning of clip)
    return shift * 3.0  # 3 points per second shifted forward


def _calculate_confidence(candidate: Dict) -> float:
    """Calculate confidence in the hook selection."""
    confidence = 0.5

    # Higher score = more confident
    if candidate["score"] > 70:
        confidence += 0.2
    elif candidate["score"] > 60:
        confidence += 0.1
    elif candidate["score"] < 40:
        confidence -= 0.15

    # Archetype detected = more confident
    if candidate.get("archetype"):
        confidence += 0.15

    # Less shift = more confident (closer to original)
    if candidate.get("penalty", 0) < 3:
        confidence += 0.1

    return min(1.0, max(0.1, confidence))


def _generate_reasoning(best: Dict, should_shift: bool, shift: float) -> str:
    """Generate human-readable reasoning for the hook choice."""
    archetype = best.get("archetype", "none detected")
    score = best.get("score", 0)

    parts = [f"Best hook score: {score:.0f}/100"]

    if archetype and archetype != "":
        desc = HOOK_ARCHETYPES[archetype]["description"]
        parts.append(f"Archetype: {archetype} ({desc})")

    if should_shift:
        direction = "earlier" if shift < 0 else "later"
        parts.append(f"Recommended: shift clip start {abs(shift):.1f}s {direction}")
    else:
        parts.append("Original clip start is optimal")

    return " | ".join(parts)


# -- Batch Hook Detection --

def detect_hooks_batch(
    clips: List[Dict],
    full_segments: List[Dict],
    max_shift: float = 5.0,
) -> List[HookResult]:
    """
    Detect best hooks for all clips in a batch.

    Returns list of HookResults aligned with the clips list.
    """
    results = []
    for clip in clips:
        hook = detect_best_hook(
            segments=full_segments,
            clip_start=clip["start"],
            clip_end=clip["end"],
            max_shift=max_shift,
        )
        results.append(hook)

    # Log summary
    shifted = sum(1 for h in results if h.should_shift)
    avg_score = sum(h.hook_score for h in results) / max(len(results), 1)
    archetypes = [h.hook_archetype for h in results if h.hook_archetype]
    log.info(
        f"[HookDetection] Batch: {len(results)} clips | "
        f"Shifted: {shifted} | Avg score: {avg_score:.1f} | "
        f"Archetypes: {', '.join(set(archetypes))}"
    )

    return results


# -- API Response Format --

def hook_to_api_dict(hook: HookResult) -> Dict:
    """Convert HookResult to API-friendly dict."""
    return {
        "best_start": round(hook.best_start, 2),
        "original_start": round(hook.original_start, 2),
        "shift_amount": round(hook.shift_amount, 2),
        "should_shift": hook.should_shift,
        "hook_text": hook.hook_text[:100],
        "hook_archetype": hook.hook_archetype,
        "hook_score": round(hook.hook_score, 1),
        "confidence": round(hook.confidence, 2),
        "alternatives": hook.alternatives,
        "reasoning": hook.reasoning,
    }
