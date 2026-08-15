from __future__ import annotations

import re
from copy import deepcopy
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


# All presets exposed by the React UI are real V5 caption presets.
# ASS colours are AABBGGRR.
PRESETS: dict[str, dict[str, Any]] = {
    "hormozi": {"font": "Arial", "size": 78, "primary": "&H00FFFFFF", "highlight": "&H0000D7FF", "outline": "&H00000000", "outline_width": 6, "margin_v": 330, "bold": True, "position": "center", "animation": "pop"},
    "mrbeast": {"font": "Impact", "size": 84, "primary": "&H00FFFFFF", "highlight": "&H0088FF00", "outline": "&H00000000", "outline_width": 10, "margin_v": 330, "bold": True, "position": "center", "animation": "pop_fast"},
    "aliabdaal": {"font": "Helvetica", "size": 64, "primary": "&H00F5F5F5", "highlight": "&H0000D7FF", "outline": "&H002E2E1A", "outline_width": 3, "margin_v": 340, "bold": False, "position": "center", "animation": "fade"},
    "minimalist": {"font": "Helvetica", "size": 54, "primary": "&H00CCCCCC", "highlight": "&H00FFFFFF", "outline": "&H00000000", "outline_width": 2, "margin_v": 150, "bold": False, "position": "bottom", "animation": "none"},
    "gaming": {"font": "Impact", "size": 86, "primary": "&H004444FF", "highlight": "&H0000FFFF", "outline": "&H00000000", "outline_width": 9, "margin_v": 330, "bold": True, "position": "center", "animation": "bounce"},
    "cinematic": {"font": "Georgia", "size": 68, "primary": "&H00EEEEFF", "highlight": "&H00FF8888", "outline": "&H00110000", "outline_width": 5, "margin_v": 170, "bold": False, "position": "bottom", "animation": "fade_slow"},
    "neon": {"font": "Arial", "size": 74, "primary": "&H00FF00FF", "highlight": "&H00FFFF00", "outline": "&H0072004A", "outline_width": 6, "margin_v": 330, "bold": True, "position": "center", "animation": "flicker"},
    "typewriter": {"font": "Courier New", "size": 66, "primary": "&H0088FF88", "highlight": "&H00AAFFAA", "outline": "&H00330000", "outline_width": 3, "margin_v": 150, "bold": False, "position": "bottom", "animation": "typewriter"},
    "tiktok_viral": {"font": "Arial", "size": 76, "primary": "&H000066FF", "highlight": "&H0000D7FF", "outline": "&H00000000", "outline_width": 7, "margin_v": 330, "bold": True, "position": "center", "animation": "pop"},
    "documentary": {"font": "Georgia", "size": 58, "primary": "&H00AACCDD", "highlight": "&H00DDEEFF", "outline": "&H000A0A1A", "outline_width": 3, "margin_v": 160, "bold": False, "position": "bottom", "animation": "fade_slow"},
    "comedy": {"font": "Comic Sans MS", "size": 74, "primary": "&H0000CCFF", "highlight": "&H000066FF", "outline": "&H00000000", "outline_width": 6, "margin_v": 330, "bold": True, "position": "center", "animation": "bounce"},
    "horror": {"font": "Impact", "size": 78, "primary": "&H000000FF", "highlight": "&H004444FF", "outline": "&H00000033", "outline_width": 9, "margin_v": 330, "bold": True, "position": "center", "animation": "flicker"},
    "motivational": {"font": "Helvetica", "size": 70, "primary": "&H00FFFFFF", "highlight": "&H00EEEEEE", "outline": "&H00000000", "outline_width": 5, "margin_v": 330, "bold": True, "position": "center", "animation": "slow_reveal"},
    "educational": {"font": "Verdana", "size": 60, "primary": "&H00FFBB66", "highlight": "&H0000D7FF", "outline": "&H00A1470D", "outline_width": 3, "margin_v": 1280, "bold": True, "position": "top", "animation": "fade"},
    "custom": {"font": "Arial", "size": 72, "primary": "&H00FFFFFF", "highlight": "&H0000D7FF", "outline": "&H00000000", "outline_width": 5, "margin_v": 330, "bold": True, "position": "center", "animation": "pop"},
    # Canonical V5 names remain available for API/advanced users.
    "karaoke": {"font": "Arial", "size": 78, "primary": "&H00FFFFFF", "highlight": "&H0000D7FF", "outline": "&H00000000", "outline_width": 6, "margin_v": 330, "bold": True, "position": "center", "animation": "pop"},
    "pop_line": {"font": "Arial", "size": 82, "primary": "&H00FFFFFF", "highlight": "&H0000D7FF", "outline": "&H00000000", "outline_width": 7, "margin_v": 360, "bold": True, "position": "center", "animation": "pop_fast"},
    "deep_diver": {"font": "Arial", "size": 62, "primary": "&H00F5F5F5", "highlight": "&H0000C8FF", "outline": "&H00111111", "outline_width": 4, "margin_v": 350, "bold": False, "position": "center", "animation": "fade"},
}

KEYWORDS = {
    "money", "uang", "growth", "tumbuh", "gagal", "failure", "success", "sukses", "secret", "rahasia",
    "mistake", "kesalahan", "never", "jangan", "why", "kenapa", "how", "cara", "important", "penting",
    "warning", "bahaya", "100", "10x", "million", "juta",
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
        sentence_break = current[-1].text.rstrip().endswith((".", "!", "?", ":"))
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


def _face_safe_margin(face: dict[str, float] | None, default: int = 330, position: str = "center") -> int:
    if position == "top":
        return 130
    if position == "bottom":
        return 150 if not face else 1180
    if not face:
        return default
    bottom = float(face.get("y", 0)) + float(face.get("h", 0))
    if bottom < 0.56:
        return 300
    if float(face.get("y", 0)) > 0.55:
        return 1120
    return default


def _anim_tag(animation: str, index: int = 0) -> str:
    if animation == "pop":
        return r"{\t(0,90,\fscx108\fscy108)}"
    if animation == "pop_fast":
        return r"{\t(0,55,\fscx112\fscy112)}"
    if animation == "fade":
        return r"{\fad(90,90)}"
    if animation == "fade_slow" or animation == "slow_reveal":
        return r"{\fad(240,180)}"
    if animation == "flicker":
        return r"{\t(0,70,\alpha&H30&)\t(70,140,\alpha&H00&)}"
    if animation == "bounce":
        return r"{\t(0,80,\fscy116)\t(80,160,\fscy100)}"
    if animation == "typewriter":
        return ""
    return ""


def render_ass(
    transcript: dict[str, Any], timeline: Any | None, out: Path, preset: str = "karaoke", font: str | None = None,
    face_samples: list[dict[str, Any]] | None = None, canvas_w: int = 1080, canvas_h: int = 1920,
    headline: str | None = None, emoji: list[str] | None = None, overrides: dict[str, Any] | None = None,
) -> Path:
    style = deepcopy(PRESETS.get(preset, PRESETS["karaoke"]))
    if overrides:
        style.update({k: v for k, v in overrides.items() if v not in (None, "")})
    chosen_font = font or style["font"]
    face_samples = face_samples or []
    position_map = {"top": 8, "center": 5, "bottom": 2}

    def face_at(t: float) -> dict[str, float] | None:
        best = None
        best_d = float("inf")
        for sample in face_samples:
            d = abs(float(sample.get("time", 0)) - t)
            if d < best_d and sample.get("faces"):
                best = sample["faces"][0]
                best_d = d
        return best

    events: list[str] = []
    if headline:
        title = _escape(headline.upper())
        if emoji:
            title = f"{_escape(' '.join(emoji))}  {title}"
        events.append(f"Dialogue: 10,0:00:00.00,9:59:59.99,Headline,,0,0,110,,{{\\an8}}{title}")

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

        phrase_groups = phrases_from_words(words)
        for phrase in phrase_groups:
            margin = _face_safe_margin(face_at(phrase.start), style["margin_v"], style.get("position", "center"))
            align = position_map.get(style.get("position", "center"), 5)
            if style.get("animation") == "typewriter":
                phrase_events = phrase.words
            else:
                phrase_events = (phrase,)

            for item in phrase_events:
                if isinstance(item, Phrase):
                    items = item.words
                    start_time, end_time = item.start, item.end
                else:
                    items = (item,)
                    start_time, end_time = item.start, item.end
                active = items[0]
                phrase_text = []
                for w in items:
                    txt = _escape(w.text.upper())
                    norm = _norm(w.text)
                    is_kw = norm in KEYWORDS or any(norm and norm in _norm(k) for k in KEYWORDS)
                    if style.get("deep_clean") and not is_kw:
                        tag = ""
                    elif w is active and style["animation"] in {"pop", "pop_fast", "bounce"}:
                        tag = f"{{\\c{style['highlight']}\\fs{style['size']+5}}}"
                    elif is_kw:
                        tag = f"{{\\c{style['highlight']}}}"
                    else:
                        tag = f"{{\\c{style['primary']}}}"
                    phrase_text.append(f"{tag}{txt}")
                anim = _anim_tag(style.get("animation", "none"))
                text = anim + "".join(phrase_text)
                events.append(f"Dialogue: 0,{_ts(start_time)},{_ts(end_time)},Caption,,0,0,{margin},,{text}")

    header = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {canvas_w}", f"PlayResY: {canvas_h}", "WrapStyle: 2", "ScaledBorderAndShadow: yes", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Headline,{chosen_font},62,&H00FFFFFF,&H00FFFFFF,&H00000000,&H90000000,{1 if style['bold'] else 0},0,0,0,100,100,0,0,1,5,2,8,70,70,110,1",
        f"Style: Caption,{chosen_font},{style['size']},{style['primary']},{style['highlight']},{style['outline']},&H80000000,{1 if style['bold'] else 0},0,0,0,100,100,0,0,1,{style['outline_width']},2,{position_map.get(style.get('position', 'center'), 5)},70,70,{style['margin_v']},1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    out.write_text("\n".join(header + events), encoding="utf-8")
    return out
