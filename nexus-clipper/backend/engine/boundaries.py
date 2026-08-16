"""
Nexus-Clipper V6.4 — Natural Speech Boundary Detection
=======================================================
Clips should cut at natural speech boundaries (sentence endings, pauses,
topic shifts), NOT at arbitrary window boundaries.

This module analyzes transcript segments and finds the best cut points
that respect natural speech rhythm:
- Sentence boundaries (period, question mark, exclamation)
- Pause durations (gaps between segments > 0.5s)
- Topic shifts (discourse markers like "anyway", "next", "so then")
- Word boundaries (never cut mid-word)
- Clause boundaries (comma, semicolon, dash)

The result: clips that feel like complete thoughts, not fragments.
"""
import re
import logging
from typing import List, Dict, Tuple, Optional

log = logging.getLogger("nexus.boundaries")


# ── Sentence End Markers ─────────────────────────────
SENTENCE_ENDERS = re.compile(r'[.!?]\s*$')

# Natural pause markers in text
PAUSE_MARKERS = [
    r'\b(anyway|so then|next|moving on|now then|alright then|ok so)\b',
    r'\b(let me|let\'s|let us)\b',
    r'\b(first|secondly|finally|lastly|in conclusion)\b',
    r'\b(on the other hand|in contrast|however that being said)\b',
]

# Discourse markers that signal a topic shift
TOPIC_SHIFT_MARKERS = [
    r'\b(anyway|so|ok|alright|now)\b.*[,.]',
    r'\b(let\'s talk about|moving on to|next up|turning to)\b',
    r'\b(that reminds me|speaking of|by the way)\b',
]


def find_natural_boundaries(
    segments: List[Dict],
    target_start: float,
    target_end: float,
    full_duration: float,
    tolerance: float = 5.0,
) -> Tuple[float, float]:
    """
    Find the best natural speech boundaries near the target clip start/end.
    
    Args:
        segments: Full transcript segments
        target_start: Desired clip start time
        target_end: Desired clip end time  
        full_duration: Total video duration
        tolerance: How far to search for boundaries (seconds)
    
    Returns:
        (adjusted_start, adjusted_end) snapped to natural boundaries
    """
    adjusted_start = _find_best_start(segments, target_start, tolerance)
    adjusted_end = _find_best_end(segments, target_end, full_duration, tolerance)
    
    # Ensure we don't overlap or create zero-length clips
    min_duration = 10.0
    if adjusted_end - adjusted_start < min_duration:
        # Fall back to original if adjustment makes clip too short
        adjusted_start = target_start
        adjusted_end = target_end
    
    return round(adjusted_start, 2), round(adjusted_end, 2)


def _find_best_start(
    segments: List[Dict],
    target_start: float,
    tolerance: float,
) -> float:
    """Find the best starting point near target_start that aligns with a natural boundary."""
    best_start = target_start
    best_score = 0
    
    # Search within ±tolerance seconds
    search_min = max(0, target_start - tolerance)
    search_max = target_start + tolerance
    
    # Find candidate boundaries
    candidates = []
    
    for seg in segments:
        seg_start = float(seg.get("start", 0))
        seg_end = float(seg.get("end", 0))
        
        # Boundary at segment start (natural pause from previous segment)
        if search_min <= seg_start <= search_max:
            # Check if there's a gap before this segment (pause)
            prev_idx = _find_prev_segment_idx(segments, seg)
            if prev_idx is not None:
                prev_end = float(segments[prev_idx].get("end", 0))
                pause_duration = seg_start - prev_end
            else:
                pause_duration = 0
            
            text = seg.get("text", "").strip()
            score = _boundary_start_score(text, pause_duration)
            candidates.append((seg_start, score, "segment_start"))
        
        # Boundary at sentence end within a segment
        words = seg.get("words", [])
        if words:
            for word in words:
                word_end = float(word.get("end", 0))
                if search_min <= word_end <= search_max:
                    word_text = word.get("word", word.get("text", "")).strip()
                    if SENTENCE_ENDERS.search(word_text):
                        # This word ends a sentence — great boundary
                        next_word_start = _get_next_word_start(words, word)
                        if next_word_start:
                            candidates.append((next_word_start, 0.95, "sentence_end"))
    
    # Also consider the original target as a candidate
    candidates.append((target_start, 0.3, "original"))
    
    # Pick the best candidate
    for candidate_start, score, boundary_type in candidates:
        # Prefer boundaries closer to the target
        distance_penalty = abs(candidate_start - target_start) / tolerance
        adjusted_score = score * (1.0 - distance_penalty * 0.3)
        
        if adjusted_score > best_score:
            best_score = adjusted_score
            best_start = candidate_start
    
    if best_start != target_start:
        log.debug(f"[Boundaries] Start: {target_start:.1f}s → {best_start:.1f}s")
    
    return best_start


def _find_best_end(
    segments: List[Dict],
    target_end: float,
    full_duration: float,
    tolerance: float,
) -> float:
    """Find the best ending point near target_end that aligns with a natural boundary."""
    best_end = target_end
    best_score = 0
    
    search_min = target_end - tolerance
    search_max = min(full_duration, target_end + tolerance)
    
    candidates = []
    
    for seg in segments:
        seg_start = float(seg.get("start", 0))
        seg_end = float(seg.get("end", 0))
        
        # Boundary at segment end
        if search_min <= seg_end <= search_max:
            text = seg.get("text", "").strip()
            score = _boundary_end_score(text)
            candidates.append((seg_end, score, "segment_end"))
        
        # Boundary at sentence end within a segment
        words = seg.get("words", [])
        if words:
            for word in words:
                word_end = float(word.get("end", 0))
                if search_min <= word_end <= search_max:
                    word_text = word.get("word", word.get("text", "")).strip()
                    if SENTENCE_ENDERS.search(word_text):
                        candidates.append((word_end, 0.95, "sentence_end"))
        
        # Boundary at segment start (ends right before a new topic begins)
        if search_min <= seg_start <= search_max:
            text = seg.get("text", "").strip()
            # Check if this segment starts a new topic
            for pattern in TOPIC_SHIFT_MARKERS:
                if re.search(pattern, text, re.IGNORECASE):
                    candidates.append((seg_start, 0.8, "topic_shift"))
                    break
    
    # Original target as fallback
    candidates.append((target_end, 0.3, "original"))
    
    # Pick best candidate
    for candidate_end, score, boundary_type in candidates:
        distance_penalty = abs(candidate_end - target_end) / tolerance
        adjusted_score = score * (1.0 - distance_penalty * 0.3)
        
        if adjusted_score > best_score:
            best_score = adjusted_score
            best_end = candidate_end
    
    if best_end != target_end:
        log.debug(f"[Boundaries] End: {target_end:.1f}s → {best_end:.1f}s")
    
    return best_end


def _boundary_start_score(text: str, pause_duration: float) -> float:
    """Score how good a starting boundary is (0-1)."""
    score = 0.4  # Base score for being at a segment boundary
    
    # Longer pause = better boundary (natural breath point)
    score += min(0.3, pause_duration * 0.15)
    
    # Sentence-starting words = good boundary
    if re.match(r'\b(the|a|an|this|that|so|but|and|here|now|well|ok|alright|let me)\b',
                text, re.IGNORECASE):
        score += 0.2
    
    # Question starting = creates curiosity (good hook)
    if re.match(r'\b(what|why|how|who|when|where|did|do|can|could|would|have you)\b',
                text, re.IGNORECASE):
        score += 0.15
    
    # Topic shift markers = clean break
    for pattern in TOPIC_SHIFT_MARKERS:
        if re.search(pattern, text, re.IGNORECASE):
            score += 0.1
            break
    
    return min(1.0, score)


def _boundary_end_score(text: str) -> float:
    """Score how good an ending boundary is (0-1)."""
    score = 0.4  # Base score for being at a segment boundary
    
    # Sentence-ending punctuation = natural conclusion
    if SENTENCE_ENDERS.search(text):
        score += 0.3
    
    # Conclusive phrases
    conclusive = [
        r'\b(that\'s why|so there you go|that\'s the story|and that\'s it|bottom line)\b',
        r'\b(the takeaway|the lesson|the point is|what this means)\b',
        r'\b(right\?|you know\?|make sense\?|crazy right\?)\b',
    ]
    for pattern in conclusive:
        if re.search(pattern, text, re.IGNORECASE):
            score += 0.2
            break
    
    # Trailing filler = bad ending (don't end on "uh" or "um")
    if re.search(r'\b(uh|um|like|you know|sort of)\b\s*$', text, re.IGNORECASE):
        score -= 0.2
    
    return max(0.1, min(1.0, score))


def _find_prev_segment_idx(segments: List[Dict], current_seg: Dict) -> Optional[int]:
    """Find the index of the segment before the current one."""
    current_start = float(current_seg.get("start", 0))
    best_idx = None
    best_start = 0
    
    for i, seg in enumerate(segments):
        seg_start = float(seg.get("start", 0))
        if seg_start < current_start and seg_start >= best_start:
            best_idx = i
            best_start = seg_start
    
    return best_idx


def _get_next_word_start(words: List[Dict], current_word: Dict) -> Optional[float]:
    """Get the start time of the word following the current word."""
    current_end = float(current_word.get("end", 0))
    
    for w in words:
        w_start = float(w.get("start", 0))
        if w_start > current_end:
            return w_start
    
    return None


# ── Batch Boundary Adjustment ─────────────────────────

def adjust_clip_boundaries(
    clips: List[Dict],
    segments: List[Dict],
    full_duration: float,
    tolerance: float = 5.0,
) -> List[Dict]:
    """
    Adjust all clip candidates to natural speech boundaries.
    
    This is called after initial candidate selection to snap each clip's
    start/end to the nearest natural speech boundary, producing clips
    that feel like complete thoughts rather than arbitrary fragments.
    """
    if not segments or not clips:
        return clips
    
    adjusted = []
    for clip in clips:
        new_start, new_end = find_natural_boundaries(
            segments, clip["start"], clip["end"], full_duration, tolerance
        )
        
        new_clip = dict(clip)
        new_clip["start"] = new_start
        new_clip["end"] = new_end
        new_clip["duration"] = round(new_end - new_start, 1)
        
        if new_start != clip["start"] or new_end != clip["end"]:
            log.info(f"[Boundaries] Adjusted [{clip['start']:.1f}-{clip['end']:.1f}s] → "
                     f"[{new_start:.1f}-{new_end:.1f}s]")
        
        adjusted.append(new_clip)
    
    return adjusted
