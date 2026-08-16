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
