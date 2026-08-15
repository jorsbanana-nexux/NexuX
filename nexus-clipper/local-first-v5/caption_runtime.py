from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from captions import render_ass as _render_ass


def _fragments_for_word(word: dict[str, Any], timeline: Any) -> list[dict[str, Any]]:
    try:
        start = float(word.get("start", 0.0))
        end = float(word.get("end", 0.0))
    except (TypeError, ValueError):
        return []
    if end <= start:
        return []
    fragments: list[dict[str, Any]] = []
    for keep in getattr(timeline, "keep_ranges", ()):
        overlap_start = max(start, float(keep.source_start))
        overlap_end = min(end, float(keep.source_end))
        if overlap_end <= overlap_start:
            continue
        fragment = dict(word)
        fragment["start"] = overlap_start
        fragment["end"] = overlap_end
        fragments.append(fragment)
    return fragments


def _prepare_transcript(transcript: dict[str, Any], timeline: Any | None) -> dict[str, Any]:
    if timeline is None:
        return transcript
    prepared = deepcopy(transcript)
    for segment in prepared.get("segments", []):
        words = []
        for word in segment.get("words", []) or []:
            words.extend(_fragments_for_word(word, timeline))
        segment["words"] = words
    return prepared


def render_ass_safe(
    transcript: dict[str, Any], timeline: Any | None, out: Path, preset: str = "karaoke", font: str | None = None,
    face_samples: list[dict[str, Any]] | None = None, canvas_w: int = 1080, canvas_h: int = 1920,
    headline: str | None = None, emoji: list[str] | None = None, overrides: dict[str, Any] | None = None,
) -> Path:
    prepared = _prepare_transcript(transcript, timeline)
    return _render_ass(
        prepared,
        timeline,
        out,
        preset=preset,
        font=font,
        face_samples=face_samples,
        canvas_w=canvas_w,
        canvas_h=canvas_h,
        headline=headline,
        emoji=emoji,
        overrides=overrides,
    )
