from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from audio_intelligence import analyze_audio

# Only high-confidence disfluencies are hard-cut by default. Context-sensitive
# words such as "jadi", "nah", "like", and "actually" remain intact.
FILLERS = {
    "um", "uh", "hmm", "hm", "eee", "aaa", "eh", "anu",
    "you know", "youknow", "maksud saya",
}


@dataclass(frozen=True)
class Cut:
    start: float
    end: float
    reason: str


@dataclass(frozen=True)
class KeepRange:
    source_start: float
    source_end: float
    output_start: float
    output_end: float


@dataclass(frozen=True)
class EditTimeline:
    source_start: float
    source_end: float
    duration_before: float
    duration_after: float
    cuts: tuple[Cut, ...]
    keep_ranges: tuple[KeepRange, ...]
    audio_profile: dict[str, Any] | None = None

    def source_to_output(self, timestamp: float) -> float | None:
        for item in self.keep_ranges:
            if item.source_start <= timestamp <= item.source_end:
                return item.output_start + (timestamp - item.source_start)
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_start": self.source_start,
            "source_end": self.source_end,
            "duration_before": self.duration_before,
            "duration_after": self.duration_after,
            "cuts": [c.__dict__ for c in self.cuts],
            "keep_ranges": [r.__dict__ for r in self.keep_ranges],
            "audio_profile": self.audio_profile,
        }


def _merge_cuts(cuts: Iterable[Cut], start: float, end: float, min_gap: float = 0.05) -> list[Cut]:
    clipped: list[Cut] = []
    for cut in cuts:
        s = max(start, min(end, cut.start))
        e = max(start, min(end, cut.end))
        if e - s >= min_gap:
            clipped.append(Cut(s, e, cut.reason))
    clipped.sort(key=lambda c: (c.start, c.end))
    merged: list[Cut] = []
    for cut in clipped:
        if not merged or cut.start > merged[-1].end + min_gap:
            merged.append(cut)
            continue
        prev = merged[-1]
        reason = prev.reason if prev.reason == cut.reason else f"{prev.reason}+{cut.reason}"
        merged[-1] = Cut(prev.start, max(prev.end, cut.end), reason)
    return merged


def parse_silences(stderr: str) -> list[Cut]:
    starts: list[float] = []
    cuts: list[Cut] = []
    for line in stderr.splitlines():
        m_start = re.search(r"silence_start:\s*([0-9.]+)", line)
        if m_start:
            starts.append(float(m_start.group(1)))
            continue
        m_end = re.search(r"silence_end:\s*([0-9.]+)", line)
        if m_end and starts:
            s = starts.pop(0)
            cuts.append(Cut(s, float(m_end.group(1)), "silence"))
    return cuts


def detect_silence(video: Path, start: float, end: float, noise_db: str = "-35dB", min_duration: float = 0.45) -> list[Cut]:
    if end <= start:
        return []
    cmd = [
        "ffmpeg", "-hide_banner", "-nostats", "-ss", f"{start:.3f}", "-i", str(video),
        "-t", f"{end-start:.3f}", "-vn", "-af", f"silencedetect=noise={noise_db}:d={min_duration}",
        "-f", "null", "-",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if r.returncode not in (0, 1):
        return []
    return [Cut(c.start + start, c.end + start, c.reason) for c in parse_silences(r.stderr)]


def _normalise_word(word: str) -> str:
    return re.sub(r"[^\w']+", "", word, flags=re.UNICODE).casefold()


def detect_fillers(segments: list[dict[str, Any]], start: float, end: float) -> list[Cut]:
    cuts: list[Cut] = []
    for seg in segments:
        for word in seg.get("words", []) or []:
            try:
                ws, we = float(word.get("start", 0)), float(word.get("end", 0))
            except (TypeError, ValueError):
                continue
            if we < start or ws > end:
                continue
            if _normalise_word(str(word.get("word", "")).strip()) in FILLERS:
                pad = min(0.035, max(0.0, (we - ws) * 0.15))
                cuts.append(Cut(max(start, ws - pad), min(end, we + pad), "filler"))
    return cuts


def _flatten_words(segments: list[dict[str, Any]], start: float, end: float) -> list[dict[str, Any]]:
    words: list[dict[str, Any]] = []
    for seg in segments:
        for word in seg.get("words", []) or []:
            try:
                ws, we = float(word.get("start", 0)), float(word.get("end", 0))
            except (TypeError, ValueError):
                continue
            if we <= start or ws >= end or we <= ws:
                continue
            words.append({"word": _normalise_word(str(word.get("word", ""))), "start": ws, "end": we})
    words.sort(key=lambda item: (item["start"], item["end"]))
    return words


def detect_repetition(segments: list[dict[str, Any]], start: float, end: float) -> list[Cut]:
    words = _flatten_words(segments, start, end)
    if len(words) < 6:
        return []
    cuts: list[Cut] = []
    for n in (3, 4, 5):
        upper = len(words) - (2 * n) + 1
        for i in range(max(0, upper)):
            a = [w["word"] for w in words[i:i+n]]
            b = [w["word"] for w in words[i+n:i+2*n]]
            if not a or a != b or not all(a):
                continue
            first_end = words[i+n-1]["end"]
            second_start = words[i+n]["start"]
            if 0 <= second_start - first_end <= 0.35:
                s = max(start, words[i]["start"])
                e = min(end, second_start)
                if e - s >= 0.12:
                    cuts.append(Cut(s, e, "repetition"))
                    break
        if cuts:
            break
    return cuts


def _audio_profile_from_clip(clip: dict[str, Any], video: Path, start: float, end: float, segments: list[dict[str, Any]]) -> dict[str, Any]:
    cached = clip.get("audio_profile")
    if isinstance(cached, dict) and cached:
        return dict(cached)
    return analyze_audio(video, start, end, speech_segments=segments).to_dict()


def build_timeline(video: Path, transcript: dict[str, Any], clip: dict[str, Any]) -> EditTimeline:
    start, end = float(clip["start"]), float(clip["end"])
    duration = max(0.0, end - start)
    segments = transcript.get("segments", [])
    audio_profile = _audio_profile_from_clip(clip, video, start, end, segments)
    min_silence = 0.65 if float(audio_profile.get("rhythm_score", 50.0)) >= 40.0 else 0.5
    silence = detect_silence(video, start, end, min_duration=0.45)
    filler = detect_fillers(segments, start, end)
    repetition = detect_repetition(segments, start, end)
    meaningful_silence = [c for c in silence if (c.end - c.start) >= min_silence]
    safe_cuts = _merge_cuts([*meaningful_silence, *filler, *repetition], start, end)

    keep: list[KeepRange] = []
    cursor = start
    output_cursor = 0.0
    for cut in safe_cuts:
        if cut.start > cursor:
            length = cut.start - cursor
            keep.append(KeepRange(cursor, cut.start, output_cursor, output_cursor + length))
            output_cursor += length
        cursor = max(cursor, cut.end)
    if cursor < end:
        length = end - cursor
        keep.append(KeepRange(cursor, end, output_cursor, output_cursor + length))
        output_cursor += length

    if not keep:
        keep = [KeepRange(start, end, 0.0, duration)]
        safe_cuts = []
        output_cursor = duration

    return EditTimeline(start, end, duration, output_cursor, tuple(safe_cuts), tuple(keep), audio_profile)


def remap_word_fragments(word: dict[str, Any], timeline: EditTimeline) -> list[dict[str, Any]]:
    try:
        start = float(word.get("start", 0.0))
        end = float(word.get("end", 0.0))
    except (TypeError, ValueError):
        return []
    if end <= start:
        return []
    fragments: list[dict[str, Any]] = []
    for keep in timeline.keep_ranges:
        overlap_start = max(start, keep.source_start)
        overlap_end = min(end, keep.source_end)
        if overlap_end <= overlap_start:
            continue
        mapped_start = keep.output_start + (overlap_start - keep.source_start)
        mapped_end = keep.output_start + (overlap_end - keep.source_start)
        fragments.append({"word": word.get("word", ""), "start": mapped_start, "end": mapped_end})
    return fragments


def remap_word(word: dict[str, Any], timeline: EditTimeline) -> dict[str, Any] | None:
    fragments = remap_word_fragments(word, timeline)
    return fragments[0] if len(fragments) == 1 else None


def ffmpeg_filter_for_timeline(timeline: EditTimeline) -> tuple[str, str]:
    v_parts: list[str] = []
    a_parts: list[str] = []
    for i, item in enumerate(timeline.keep_ranges):
        v_parts.append(f"[0:v]trim=start={item.source_start:.6f}:end={item.source_end:.6f},setpts=PTS-STARTPTS[v{i}]")
        a_parts.append(f"[0:a]atrim=start={item.source_start:.6f}:end={item.source_end:.6f},asetpts=PTS-STARTPTS[a{i}]")
    n = len(timeline.keep_ranges)
    if n == 1:
        return f"{v_parts[0]};{a_parts[0]};[v0]null[vout];[a0]anull[aout]", ""
    concat_inputs = "".join(f"[v{i}][a{i}]" for i in range(n))
    return ";".join(v_parts + a_parts) + f";{concat_inputs}concat=n={n}:v=1:a=1[vout][aout]", ""
