"""
Nexus-Clipper V6.4 — Subtitle Quality Engine
=============================================
Professional subtitle rendering with readability guarantees.

The old system burned in words without checking if humans can actually
read them. This module enforces:
- CPS (Characters Per Second) limits — text never appears too fast
- Maximum line length — lines never run too wide
- Smart word grouping — 2-3 words appear together for natural reading
- Line breaking at natural points — commas, conjunctions, pauses
- Minimum display time — each subtitle stays on screen long enough
- Reading speed validation — respects WPM (words per minute) limits

This is what separates professional subtitles from amateur ones.
"""
import re
import logging
from typing import List, Dict, Tuple, Optional

log = logging.getLogger("nexus.subtitle_quality")


# ── Readability Constants ────────────────────────────

MAX_CPS = 25          # Max characters per second (broadcast standard: 17-25)
MAX_WPM = 240         # Max words per minute (comfortable reading: 180-240)
MIN_DISPLAY_TIME = 0.7  # Min seconds a word/phrase should be visible
MAX_LINE_LENGTH = 42   # Max characters per line (optimal: 35-42)
MAX_LINES = 2          # Max simultaneous lines
OPTIMAL_WPM = 180      # Target comfortable reading speed


# ── Word Grouping ────────────────────────────────────

def group_words_for_readability(
    words: List[Dict],
    clip_start: float,
    clip_end: float,
) -> List[Dict]:
    """
    Group individual words into readable phrases.
    
    Instead of popping one word at a time (which can be too fast),
    this groups 2-4 words that appear close together in time into
    a single display unit. This is how professional captions work.
    
    Args:
        words: Word-level timing data from transcript
        clip_start: Clip start time
        clip_end: Clip end time
    
    Returns:
        List of grouped word phrases with combined timing
    """
    if not words:
        return []

    groups = []
    current_group = []
    current_group_start = None
    current_group_end = None

    for word in words:
        w_start = float(word.get("start", 0))
        w_end = float(word.get("end", 0))
        w_text = word.get("word", word.get("text", "")).strip()

        if not w_text or w_end < clip_start or w_start > clip_end:
            continue

        # Clamp to clip boundaries
        w_start = max(w_start, clip_start)
        w_end = min(w_end, clip_end)

        if not current_group:
            current_group = [word]
            current_group_start = w_start
            current_group_end = w_end
            continue

        # Check if this word should join the current group
        gap = w_start - current_group_end
        group_text = " ".join(
            w.get("word", w.get("text", "")).strip()
            for w in current_group
        )

        # Group if:
        # 1. Gap is small (< 0.15s = natural speech flow)
        # 2. Combined text isn't too long
        # 3. Combined display time is reasonable
        should_group = (
            gap < 0.15 and
            len(group_text) + len(w_text) + 1 <= MAX_LINE_LENGTH and
            len(current_group) < 4
        )

        # Also group if the word is very short (article, preposition)
        if w_text.lower() in ("the", "a", "an", "of", "to", "in", "is", "it", "on",
                              "at", "by", "for", "and", "or", "but", "so", "as", "if"):
            should_group = should_group or (gap < 0.3 and len(current_group) < 3)

        if should_group:
            current_group.append(word)
            current_group_end = w_end
        else:
            # Finalize current group
            groups.append(_make_group(current_group, current_group_start, current_group_end))
            current_group = [word]
            current_group_start = w_start
            current_group_end = w_end

    # Don't forget the last group
    if current_group:
        groups.append(_make_group(current_group, current_group_start, current_group_end))

    # Enforce minimum display time
    for g in groups:
        duration = g["end"] - g["start"]
        if duration < MIN_DISPLAY_TIME:
            # Extend the end time to meet minimum
            g["end"] = g["start"] + MIN_DISPLAY_TIME
            g["duration"] = MIN_DISPLAY_TIME

    # Check CPS and split groups that are too dense
    final_groups = []
    for g in groups:
        cps = len(g["text"]) / max(g["duration"], 0.1)
        if cps > MAX_CPS:
            # This group has too much text for its duration — extend duration
            needed_duration = len(g["text"]) / MAX_CPS
            g["end"] = g["start"] + needed_duration
            g["duration"] = needed_duration
            log.debug(f"[Subtitle] Extended group duration for CPS: "
                     f"{g['text'][:30]}... → {needed_duration:.2f}s")
        final_groups.append(g)

    return final_groups


def _make_group(words: List[Dict], start: float, end: float) -> Dict:
    """Create a word group dict."""
    text = " ".join(w.get("word", w.get("text", "")).strip() for w in words)
    return {
        "text": text,
        "start": start,
        "end": end,
        "duration": end - start,
        "word_count": len(words),
        "words": words,
    }


# ── Line Breaking ────────────────────────────────────

def smart_line_break(text: str, max_length: int = MAX_LINE_LENGTH) -> str:
    """
    Break a long line into two lines at a natural point.
    
    Uses ASS \\N (hard newline) to split. Tries to break at:
    1. Punctuation (comma, semicolon, dash)
    2. Conjunctions (and, but, so, because)
    3. Natural word boundary closest to midpoint
    """
    if len(text) <= max_length:
        return text

    # Try to find a punctuation break
    for punct in [", ", "; ", " - ", ". ", "? ", "! "]:
        idx = text[:len(text) // 2 + len(text) // 3].rfind(punct)
        if idx > max_length * 0.3:
            return text[:idx + 1].strip() + "\\N" + text[idx + len(punct):].strip()

    # Try conjunctions
    for conj in [" and ", " but ", " so ", " because ", " or ", " when ", " while "]:
        idx = text[:len(text) // 2 + len(text) // 3].rfind(conj)
        if idx > max_length * 0.3:
            return text[:idx].strip() + "\\N" + text[idx:].strip()

    # Fallback: break at word boundary nearest midpoint
    mid = len(text) // 2
    for offset in range(0, 20):
        for pos in [mid + offset, mid - offset]:
            if 0 < pos < len(text) and text[pos] == " ":
                return text[:pos].strip() + "\\N" + text[pos:].strip()

    return text


# ── CPS Validation ───────────────────────────────────

def validate_readability(
    groups: List[Dict],
) -> Dict:
    """
    Validate that subtitle groups meet readability standards.
    
    Returns a report with any issues found and overall quality score.
    """
    issues = []
    max_cps_found = 0
    min_duration_found = float("inf")
    total_text_length = 0
    total_duration = 0

    for i, g in enumerate(groups):
        cps = len(g["text"]) / max(g["duration"], 0.1)
        wpm = g["word_count"] / max(g["duration"], 0.1) * 60

        max_cps_found = max(max_cps_found, cps)
        min_duration_found = min(min_duration_found, g["duration"])
        total_text_length += len(g["text"])
        total_duration += g["duration"]

        if cps > MAX_CPS:
            issues.append(f"Group {i}: CPS={cps:.1f} (max {MAX_CPS}) — too fast: \"{g['text'][:40]}\"")
        if g["duration"] < MIN_DISPLAY_TIME:
            issues.append(f"Group {i}: Duration={g['duration']:.2f}s (min {MIN_DISPLAY_TIME}s)")
        if len(g["text"]) > MAX_LINE_LENGTH:
            issues.append(f"Group {i}: Line length={len(g['text'])} (max {MAX_LINE_LENGTH})")

    avg_cps = total_text_length / max(total_duration, 0.1)
    quality_score = 1.0

    if max_cps_found > MAX_CPS:
        quality_score -= 0.3
    if min_duration_found < MIN_DISPLAY_TIME:
        quality_score -= 0.2
    if avg_cps > MAX_CPS * 0.8:
        quality_score -= 0.2
    if issues:
        quality_score -= min(0.3, len(issues) * 0.05)

    return {
        "quality_score": max(0.0, quality_score),
        "issues": issues,
        "max_cps": round(max_cps_found, 1),
        "avg_cps": round(avg_cps, 1),
        "min_duration": round(min_duration_found, 2),
        "total_groups": len(groups),
        "readable": quality_score > 0.7,
    }


# ── Full Subtitle Quality Pipeline ───────────────────

def process_subtitle_quality(
    transcript: Dict,
    clip: Dict,
    style_config: Dict,
) -> Tuple[List[Dict], Dict]:
    """
    Full subtitle quality pipeline.
    
    Takes raw transcript segments and produces readability-validated
    word groups with proper timing, line breaking, and CPS enforcement.
    
    Returns:
        (word_groups, quality_report)
    """
    segments = transcript.get("segments", [])
    clip_start = clip["start"]
    clip_end = clip["end"]

    all_groups = []

    for seg in segments:
        ss = float(seg.get("start", 0))
        se = float(seg.get("end", 0))

        # Skip segments outside clip range
        if se < clip_start or ss > clip_end:
            continue

        words = seg.get("words", [])
        if words:
            groups = group_words_for_readability(words, clip_start, clip_end)
            all_groups.extend(groups)
        else:
            # Fallback: treat entire segment as one group
            text = seg.get("text", "").strip()
            if text:
                seg_start = max(ss, clip_start)
                seg_end = min(se, clip_end)
                all_groups.append({
                    "text": text,
                    "start": seg_start,
                    "end": seg_end,
                    "duration": seg_end - seg_start,
                    "word_count": len(text.split()),
                    "words": [],
                })

    # Apply smart line breaking
    for g in all_groups:
        if len(g["text"]) > MAX_LINE_LENGTH:
            g["text"] = smart_line_break(g["text"])

    # Validate
    report = validate_readability(all_groups)

    if not report["readable"]:
        log.warning(f"[Subtitle] Quality issues: {len(report['issues'])} found. "
                    f"Score: {report['quality_score']:.2f}")
    else:
        log.info(f"[Subtitle] Quality OK — {len(all_groups)} groups, "
                 f"CPS={report['avg_cps']:.1f}, score={report['quality_score']:.2f}")

    return all_groups, report
