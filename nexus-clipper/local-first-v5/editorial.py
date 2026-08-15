from __future__ import annotations

import re
from dataclasses import dataclass, asdict

EMOJI_RULES = {
    "uang": "💰", "money": "💰", "profit": "💰",
    "tumbuh": "🚀", "growth": "🚀", "naik": "🚀",
    "cepat": "⚡", "fast": "⚡",
    "gagal": "❌", "failure": "❌", "salah": "❌",
    "sukses": "✅", "berhasil": "✅", "success": "✅",
    "rahasia": "🔥", "secret": "🔥", "hack": "🔥",
    "ide": "💡", "idea": "💡", "strategi": "💡",
    "target": "🎯", "goal": "🎯", "tujuan": "🎯",
}

@dataclass(frozen=True)
class EditorialMetadata:
    headline: str | None
    headline_confidence: float
    emoji: list[str]
    headline_zone: str
    subtitle_zone: str


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def make_headline(text: str, max_words: int = 9) -> tuple[str | None, float]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", _normalise(text)) if s.strip()]
    if not sentences:
        return None, 0.0
    first = sentences[0]
    words = re.findall(r"[\w%'-]+", first, flags=re.UNICODE)
    if len(words) < 4:
        return None, 0.0
    chosen = words[:max_words]
    confidence = 0.70
    if "?" in first:
        confidence += 0.10
    if re.search(r"\d", first):
        confidence += 0.08
    return " ".join(chosen).upper(), min(0.95, confidence)


def emoji_for_text(text: str, enabled: bool = False, max_count: int = 2) -> list[str]:
    if not enabled:
        return []
    lower = text.casefold()
    result: list[str] = []
    for term, emoji in EMOJI_RULES.items():
        if term in lower and emoji not in result:
            result.append(emoji)
        if len(result) >= max_count:
            break
    return result


def editorial_metadata(text: str, emoji_enabled: bool = False) -> EditorialMetadata:
    headline, confidence = make_headline(text)
    return EditorialMetadata(
        headline=headline,
        headline_confidence=confidence,
        emoji=emoji_for_text(text, emoji_enabled),
        # Zones are semantic layout contracts consumed by the future compositor.
        # Headline stays upper-safe; captions stay lower-safe. Face avoidance can move them inward.
        headline_zone="top-safe",
        subtitle_zone="bottom-safe",
    )


def to_dict(metadata: EditorialMetadata) -> dict:
    return asdict(metadata)
