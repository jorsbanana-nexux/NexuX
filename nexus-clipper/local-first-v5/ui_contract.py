from __future__ import annotations

from typing import Final

ASPECT_RATIOS: Final[tuple[str, ...]] = ("9:16", "1:1", "16:9", "4:5", "2:3", "21:9")
SUBTITLE_STYLES: Final[tuple[str, ...]] = (
    "hormozi", "mrbeast", "aliabdaal", "minimalist", "gaming", "cinematic",
    "neon", "typewriter", "tiktok_viral", "documentary", "comedy", "horror",
    "motivational", "educational", "custom", "karaoke", "pop_line", "deep_diver",
)
ANIMATIONS: Final[tuple[str, ...]] = (
    "none", "pop", "pop_fast", "fade", "fade_slow", "slow_reveal", "flicker",
    "bounce", "typewriter",
)
POSITIONS: Final[tuple[str, ...]] = ("top", "center", "bottom")

FRONTED_PRESET_ALIASES: Final[dict[str, str]] = {
    "minimal-aesthetic": "minimalist",
    "gamer-comic": "gaming",
    "neon-cyberpunk": "neon",
    "iman-gadzhi": "motivational",
    "anime-impact": "mrbeast",
}

FRONTED_ANIMATION_ALIASES: Final[dict[str, str]] = {
    "word-by-word": "pop",
    "line-by-line": "pop_fast",
    "bounce-zoom": "bounce",
    "typewriter-glitch": "typewriter",
    "kinetic-slide": "pop_fast",
    "pulse-glow": "flicker",
    "flip-rotate": "bounce",
    "fade-drift": "fade_slow",
}


def canonicalize_fronted_values(subtitle_style: str, animation: str) -> tuple[str, str]:
    style = FRONTED_PRESET_ALIASES.get(str(subtitle_style).strip(), str(subtitle_style).strip())
    effect = FRONTED_ANIMATION_ALIASES.get(str(animation).strip(), str(animation).strip())
    return style, effect


def require_choice(value: str, allowed: tuple[str, ...], field: str) -> str:
    normalized = str(value).strip()
    if normalized not in allowed:
        raise ValueError(f"Unsupported {field}: {normalized!r}. Allowed: {', '.join(allowed)}")
    return normalized


def require_color(value: str, field: str) -> str:
    normalized = str(value).strip()
    if len(normalized) != 7 or normalized[0] != "#":
        raise ValueError(f"Invalid {field}: expected #RRGGBB")
    try:
        int(normalized[1:], 16)
    except ValueError as exc:
        raise ValueError(f"Invalid {field}: expected #RRGGBB") from exc
    return normalized.upper()
