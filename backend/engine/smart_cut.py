r"""
NexuX V9.6 — Smart Cut Engine
==============================
Automatic jump-cut removal of silences and filler words — the feature
Opus Clip gates behind its paid tiers, implemented here with full
transparency (every cut is reported with a reason).

Algorithm:
1. Collect speech events (word-level when available, segment-level fallback)
   clipped to the clip window.
2. Mark cut ranges:
   - Silences: inter-speech gaps longer than ``max_silence`` are reduced to
     a short breath (``2 * pad``) instead of removed entirely, so the cut
     does not feel robotic.
   - Fillers: filler words (EN + ID lexicon from podcast_analyzer) are cut
     with a small padding, clamped to neighbouring word boundaries so we
     never slice through audible speech.
3. Keep ranges = complement of merged cut ranges. Micro keep-ranges
   (< ``min_keep``) between two cuts are absorbed into the cut.
4. ``remap_transcript`` compresses the timeline so downstream consumers
   (ASS karaoke subtitles, hook overlays) stay in sync after the cut.

All times are absolute source times unless stated otherwise.
"""
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .podcast_analyzer import FILLER_WORDS

log = logging.getLogger("nexus.smart_cut")

# ── Tuning constants ──
DEFAULT_MAX_SILENCE = 0.45   # gaps longer than this get jump-cut
DEFAULT_PAD = 0.06           # breath kept around each cut boundary
MIN_KEEP_SEGMENT = 0.25      # keep-ranges shorter than this are absorbed
MIN_NEW_DURATION = 8.0       # never smart-cut a clip below this length
MAX_FILLER_RATIO = 0.50      # safety: refuse to cut more than this fraction

_FILLER_SET = set(FILLER_WORDS.get("en", [])) | set(FILLER_WORDS.get("id", []))
_WORD_CLEAN_RE = re.compile(r"[^\w']+", re.UNICODE)


@dataclass
class SmartCutResult:
    """Result of a smart-cut analysis for one clip window."""
    keep_segments: List[Tuple[float, float]] = field(default_factory=list)
    removed_segments: List[Dict] = field(default_factory=list)  # {start,end,reason}
    original_duration: float = 0.0
    new_duration: float = 0.0
    removed_seconds: float = 0.0
    removed_pct: float = 0.0
    filler_count: int = 0
    silence_count: int = 0

    @property
    def worth_cutting(self) -> bool:
        """True when the cut meaningfully tightens the clip without gutting it."""
        return (
            len(self.keep_segments) >= 2
            and self.removed_seconds >= 1.0
            and self.new_duration >= MIN_NEW_DURATION
        )

    def to_dict(self) -> Dict:
        return {
            "keep_segments": [[round(s, 3), round(e, 3)] for s, e in self.keep_segments],
            "removed_segments": [
                {"start": round(r["start"], 3), "end": round(r["end"], 3),
                 "reason": r["reason"]}
                for r in self.removed_segments
            ],
            "original_duration": round(self.original_duration, 3),
            "new_duration": round(self.new_duration, 3),
            "removed_seconds": round(self.removed_seconds, 3),
            "removed_pct": round(self.removed_pct, 1),
            "filler_count": self.filler_count,
            "silence_count": self.silence_count,
        }


def _word_text(word: Dict) -> str:
    return _WORD_CLEAN_RE.sub("", str(word.get("word", word.get("text", "")))).lower()


def _collect_speech_events(
    transcript: Dict, clip_start: float, clip_end: float
) -> Tuple[List[Dict], bool]:
    """Collect speech events within the clip window.

    Returns (events, word_level). Each event: {start, end, text, is_filler}.
    Events are sorted, clamped to the window, and non-overlapping enough for
    gap analysis (overlaps are tolerated — the merge step handles them).
    """
    events: List[Dict] = []
    word_level = False

    for seg in transcript.get("segments", []) or []:
        try:
            ss, se = float(seg.get("start", 0)), float(seg.get("end", 0))
        except (TypeError, ValueError):
            continue
        if se <= clip_start or ss >= clip_end:
            continue

        words = seg.get("words") or []
        usable = []
        for w in words:
            try:
                ws, we = float(w.get("start", 0)), float(w.get("end", 0))
            except (TypeError, ValueError):
                continue
            if we <= clip_start or ws >= clip_end or we <= ws:
                continue
            usable.append((ws, we, w))

        if usable:
            word_level = True
            for ws, we, w in usable:
                text = _word_text(w)
                events.append({
                    "start": max(ws, clip_start),
                    "end": min(we, clip_end),
                    "text": text,
                    "is_filler": text in _FILLER_SET,
                })
        else:
            events.append({
                "start": max(ss, clip_start),
                "end": min(se, clip_end),
                "text": str(seg.get("text", "")),
                "is_filler": False,
            })

    events.sort(key=lambda e: (e["start"], e["end"]))
    return events, word_level


def _merge_ranges(ranges: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """Merge overlapping or touching ranges."""
    if not ranges:
        return []
    out = [list(ranges[0])]
    for s, e in ranges[1:]:
        if s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return [(s, e) for s, e in out]


def compute_keep_segments(
    transcript: Dict,
    clip_start: float,
    clip_end: float,
    max_silence: float = DEFAULT_MAX_SILENCE,
    remove_fillers: bool = True,
    pad: float = DEFAULT_PAD,
    min_keep: float = MIN_KEEP_SEGMENT,
) -> SmartCutResult:
    """Compute keep/cut ranges for a clip window.

    Args:
        transcript: transcript dict with segments (word-level preferred).
        clip_start/clip_end: absolute clip window.
        max_silence: silence gaps longer than this are jump-cut.
        remove_fillers: cut filler words (word-level transcripts only).
        pad: breath kept around each cut boundary.
        min_keep: keep-ranges shorter than this are absorbed into cuts.
    """
    result = SmartCutResult(original_duration=max(0.0, clip_end - clip_start))
    if clip_end <= clip_start:
        return result

    events, word_level = _collect_speech_events(transcript, clip_start, clip_end)
    if not events:
        # No speech data — keep everything (nothing smart to do)
        result.keep_segments = [(clip_start, clip_end)]
        result.new_duration = result.original_duration
        return result

    cuts: List[Tuple[float, float]] = []
    reasons: List[Dict] = []

    # ── Silence cuts: shrink long gaps to a short breath ──
    for prev, nxt in zip(events, events[1:]):
        gap = nxt["start"] - prev["end"]
        if gap > max_silence:
            cs, ce = prev["end"] + pad, nxt["start"] - pad
            if ce > cs:
                cuts.append((cs, ce))
                reasons.append({"start": cs, "end": ce, "reason": "silence"})
                result.silence_count += 1

    # ── Filler cuts (word-level only) ──
    if remove_fillers and word_level:
        for i, ev in enumerate(events):
            if not ev["is_filler"]:
                continue
            cs = ev["start"] - pad
            ce = ev["end"] + pad
            # Clamp to neighbours so we never slice audible speech
            if i > 0:
                cs = max(cs, events[i - 1]["end"])
            if i < len(events) - 1:
                ce = min(ce, events[i + 1]["start"])
            if ce > cs:
                cuts.append((cs, ce))
                reasons.append({"start": cs, "end": ce, "reason": "filler"})
                result.filler_count += 1

    cuts = _merge_ranges(sorted(cuts))
    if not cuts:
        result.keep_segments = [(clip_start, clip_end)]
        result.new_duration = result.original_duration
        return result

    # ── Keep ranges = complement of cuts ──
    keep: List[Tuple[float, float]] = []
    cursor = clip_start
    for cs, ce in cuts:
        if cs > cursor:
            keep.append((cursor, cs))
        cursor = max(cursor, ce)
    if cursor < clip_end:
        keep.append((cursor, clip_end))

    # Absorb micro keep-ranges (islands between two cuts) — a tiny sliver
    # between cuts would flash a single frame, so drop it entirely.
    if len(keep) > 1:
        keep = [(s, e) for s, e in keep if e - s >= min_keep] or keep

    if not keep:
        keep = [(clip_start, clip_end)]

    result.keep_segments = keep
    result.removed_segments = reasons
    result.new_duration = sum(e - s for s, e in keep)
    result.removed_seconds = max(0.0, result.original_duration - result.new_duration)
    result.removed_pct = (
        100.0 * result.removed_seconds / result.original_duration
        if result.original_duration > 0 else 0.0
    )

    # Safety: refuse pathological cuts (transcript likely misaligned)
    if result.original_duration > 0 and (
        result.removed_pct > MAX_FILLER_RATIO * 100
    ):
        log.warning(
            f"[SmartCut] Refusing cut: {result.removed_pct:.0f}% removal exceeds "
            f"safety limit — transcript may be misaligned"
        )
        result.keep_segments = [(clip_start, clip_end)]
        result.removed_segments = []
        result.new_duration = result.original_duration
        result.removed_seconds = 0.0
        result.removed_pct = 0.0
        result.filler_count = 0
        result.silence_count = 0

    return result


def compress_time(t: float, keep_segments: List[Tuple[float, float]]) -> Optional[float]:
    """Map an absolute time to the compressed (post-cut) timeline.

    Returns None when the time falls inside a removed range.
    """
    offset = 0.0
    for s, e in keep_segments:
        if s <= t <= e:
            return offset + (t - s)
        if t < s:
            return None
        offset += e - s
    return None


def remap_transcript(
    transcript: Dict, keep_segments: List[Tuple[float, float]]
) -> Dict:
    """Retime a transcript onto the compressed post-cut timeline.

    Words/segments inside removed ranges are dropped; kept ones are shifted
    so t=0 is the start of the first keep segment. Segment entries without
    surviving words are dropped.
    """
    new_segments = []
    for seg in transcript.get("segments", []) or []:
        try:
            ss, se = float(seg.get("start", 0)), float(seg.get("end", 0))
        except (TypeError, ValueError):
            continue

        new_words = []
        for w in seg.get("words") or []:
            try:
                ws, we = float(w.get("start", 0)), float(w.get("end", 0))
            except (TypeError, ValueError):
                continue
            nws, nwe = compress_time(ws, keep_segments), compress_time(we, keep_segments)
            if nws is None or nwe is None or nwe <= nws:
                continue
            nw = dict(w)
            nw["start"], nw["end"] = round(nws, 3), round(nwe, 3)
            new_words.append(nw)

        if new_words:
            ns = dict(seg)
            ns["start"] = new_words[0]["start"]
            ns["end"] = new_words[-1]["end"]
            ns["text"] = " ".join(
                str(w.get("word", w.get("text", ""))) for w in new_words
            ).strip() or seg.get("text", "")
            ns["words"] = new_words
            new_segments.append(ns)
            continue

        # Segment-level fallback (no word timing)
        nss, nse = compress_time(ss, keep_segments), compress_time(se, keep_segments)
        if nss is not None and nse is not None and nse > nss:
            ns = dict(seg)
            ns["start"], ns["end"] = round(nss, 3), round(nse, 3)
            new_segments.append(ns)

    return {
        **{k: v for k, v in transcript.items() if k not in ("segments", "text")},
        "segments": new_segments,
        "text": " ".join(s.get("text", "") for s in new_segments).strip(),
        "smart_cut_remapped": True,
    }
