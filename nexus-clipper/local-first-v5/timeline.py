from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from audio_intelligence import analyze_audio

FILLERS = {"um", "uh", "hmm", "hm", "eee", "aaa", "eh", "anu", "kayak", "like", "you know", "youknow", "actually", "basically", "maksud saya", "gitu", "jadi", "nah"}


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
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{start:.3f}", "-i", str(video), "-t", f"{end-start:.3f}", "-vn", "-af", f"silencedetect=noise={noise_db}:d={min_duration}", "-f", "null", "-"]
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


def detect_repetition(segments: list[dict[str, Any]], start: float, end: float) -> list[Cut]:
    cuts: list[Cut] = []
    for seg in segments:
        words = seg.get("words") or []
        if len(words) < 6:
            continue
        norm = [_normalise_word(w.get("word", "")) for w in words]
        for n in (3, 4, 5):
            for i in range(0, len(words) - (2 * n) + 1):
                a, b = norm[i:i+n], norm[i+n:i+2*n]
                if a != b or not all(a):
                    continue
                first_end = float(words[i+n-1].get("end", words[i+n-1].get("start", 0)))
                second_start = float(words[i+n].get("start", first_end))
                if 0 <= second_start - first_end <= 0.35:
                    s = max(start, float(words[i].get("start", 0)))
                    e = min(end, second_start)
                    if e - s >= 0.12:
                        cuts.append(Cut(s, e, "repetition"))
                        break
            if cuts:
                break
    return cuts


def build_timeline(video: Path, transcript: dict[str, Any], clip: dict[str, Any]) -> EditTimeline:
    start, end = float(clip["start"]), float(clip["end"])
    duration = max(0.0, end - start)
    segments = transcript.get("segments", [])

    cached_profile = clip.get("audio_profile")
    if isinstance(cached_profile, dict) and cached_profile:
        audio_profile = dict(cached_profile)
    else:
        audio_profile = analyze_audio(video, start, end, speech_segments=segments).to_dict()

    min_silence = 0.65
    if float(audio_profile.get("rhythm_score", 50.0)) < 40.0:
        min_silence = 0.5
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


def remap_word(word: dict[str, Any], timeline: EditTimeline) -> dict[str, Any] | None:
    s = timeline.source_to_output(float(word.get("start", 0)))
    e = timeline.source_to_output(float(word.get("end", 0)))
    if s is None or e is None or e <= s:
        return None
    return {"word": word.get("word", ""), "start": s, "end": e}


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
