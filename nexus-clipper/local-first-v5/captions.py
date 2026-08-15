from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class Phrase:
    words: tuple[Word, ...]
    start: float
    end: float


PRESETS: dict[str, dict[str, Any]] = {
    "karaoke": {
        "font": "Arial",
        "size": 78,
        "primary": "&H00FFFFFF",
        "highlight": "&H0000E8FF",
        "outline": "&H00000000",
        "outline_width": 6,
        "margin_v": 330,
        "bold": True,
    },
    "pop_line": {
        "font": "Arial",
        "size": 82,
        "primary": "&H00FFFFFF",
        "highlight": "&H0000D7FF",
        "outline": "&H00000000",
        "outline_width": 7,
        "margin_v": 360,
        "bold": True,
    },
    "deep_diver": {
        "font": "Arial",
        "size": 62,
        "primary": "&H00F5F5F5",
        "highlight": "&H0000C8FF",
        "outline": "&H00111111",
        "outline_width": 4,
        "margin_v": 350,
        "bold": False,
    },
}

KEYWORDS = {
    "money", "uang", "growth", "tumbuh", "gagal", "failure", "success", "sukses",
    "secret", "rahasia", "mistake", "kesalahan", "never", "jangan", "why", "kenapa",
    "how", "cara", "important", "penting", "warning", "bahaya", "100", "10x", "million", "juta",
}


def _norm(text: str) -> str:
    return re.sub(r"[^\w]+", "", text, flags=re.UNICODE).casefold()


def phrases_from_words(words: Iterable[dict[str, Any]], max_words: int = 4, max_duration: float = 2.6, max_gap: float = 0.45) -> list[Phrase]:
    current: list[Word] = []
    phrases: list[Phrase] = []
    for item in words:
        try:
            w = Word(str(item.get("word", "")).strip(), float(item.get("start", 0)), float(item.get("end", 0)))
        except (TypeError, ValueError):
            continue
        if not w.text or w.end <= w.start:
            continue
        if not current:
            current = [w]
            continue
        gap = w.start - current[-1].end
        duration = w.end - current[0].start
        sentence_break = current[-1].text.rstrip().endswith(('.', '!', '?', ':'))
        if len(current) >= max_words or duration > max_duration or gap > max_gap or sentence_break:
            phrases.append(Phrase(tuple(current), current[0].start, current[-1].end))
            current = [w]
        else:
            current.append(w)
    if current:
        phrases.append(Phrase(tuple(current), current[0].start, current[-1].end))
    return phrases


def _ts(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", " ")


def _face_safe_margin(face: dict[str, float] | None, canvas_h: int = 1920, default: int = 330) -> int:
    if not face:
        return default
    bottom = float(face.get("y", 0)) + float(face.get("h", 0))
    if bottom < 0.56:
        return 300
    if float(face.get("y", 0)) > 0.55:
        return 1120
    return default


def render_ass(
    transcript: dict[str, Any],
    timeline: Any | None,
    out: Path,
    preset: str = "karaoke",
    font: str | None = None,
    face_samples: list[dict[str, Any]] | None = None,
    canvas_w: int = 1080,
    canvas_h: int = 1920,
) -> Path:
    style = PRESETS.get(preset, PRESETS["karaoke"])
    chosen_font = font or style["font"]
    face_samples = face_samples or []

    def face_at(t: float) -> dict[str, float] | None:
        best = None
        best_d = 999999.0
        for sample in face_samples:
            d = abs(float(sample.get("time", 0)) - t)
            if d < best_d and sample.get("faces"):
                best = sample["faces"][0]
                best_d = d
        return best

    events: list[str] = []
    for seg in transcript.get("segments", []):
        words = seg.get("words") or []
        if not words:
            continue
        if timeline is not None:
            mapped = []
            for w in words:
                rw = timeline.source_to_output(float(w.get("start", 0)))
                ew = timeline.source_to_output(float(w.get("end", 0)))
                if rw is not None and ew is not None and ew > rw:
                    mapped.append({"word": w.get("word", ""), "start": rw, "end": ew})
            words = mapped
        phrases = phrases_from_words(words)
        for phrase in phrases:
            margin = _face_safe_margin(face_at(phrase.start), canvas_h, style["margin_v"])
            active = phrase.words[0]
            phrase_text = []
            for w in phrase.words:
                txt = _escape(w.text.upper())
                norm = _norm(w.text)
                is_kw = norm in KEYWORDS or any(norm and norm in _norm(k) for k in KEYWORDS)
                if preset == "deep_diver" and not is_kw:
                    tag = ""
                elif w is active and preset in {"karaoke", "pop_line"}:
                    tag = f"{{\\c{style['highlight']}\\fs{style['size']+5}\\t(0,90,\\fscx108\\fscy108)}}"
                elif is_kw:
                    tag = f"{{\\c{style['highlight']}}}"
                else:
                    tag = f"{{\\c{style['primary']}}}"
                phrase_text.append(f"{tag}{txt}")
            events.append(
                f"Dialogue: 0,{_ts(phrase.start)},{_ts(phrase.end)},Caption,,0,0,{margin},,{''.join(phrase_text)}"
            )

    header = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1080",
        "PlayResY: 1920",
        "WrapStyle: 2",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Caption,{chosen_font},{style['size']},{style['primary']},{style['highlight']},{style['outline']},&H80000000,{1 if style['bold'] else 0},0,0,0,100,100,0,0,1,{style['outline_width']},2,2,70,70,{style['margin_v']},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    out.write_text("\n".join(header + events), encoding="utf-8")
    return out
