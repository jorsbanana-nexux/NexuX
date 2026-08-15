from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path


EMOJI_RULES = {
    "uang": "💰", "money": "💰", "gaji": "💰", "profit": "💰",
    "tumbuh": "🚀", "growth": "🚀", "naik": "🚀",
    "cepat": "⚡", "quick": "⚡", "fast": "⚡",
    "gagal": "❌", "failure": "❌", "salah": "❌",
    "sukses": "✅", "berhasil": "✅", "success": "✅",
    "rahasia": "🔥", "secret": "🔥", "hack": "🔥",
    "ide": "💡", "idea": "💡", "strategi": "💡",
    "target": "🎯", "goal": "🎯", "tujuan": "🎯",
    "peringatan": "⚠️", "warning": "⚠️", "bahaya": "⚠️",
}

KEYWORDS = {
    "curiosity": ["rahasia", "secret", "ternyata", "ternyata", "belum tahu", "you won't believe"],
    "benefit": ["cara", "how to", "tips", "trik", "benefit", "manfaat", "bisa", "helps"],
    "controversy": ["salah", "wrong", "bohong", "lie", "mitos", "myth", "tidak setuju", "disagree"],
    "numbers": [r"\b\d+(?:[.,]\d+)?\s*%", r"\b\d+(?:[.,]\d+)?\s*(?:jt|juta|rb|ribu|m|million|billion)\b"],
}

@dataclass(frozen=True)
class VisualSignal:
    term: str
    kind: str
    score: float

@dataclass(frozen=True)
class Headline:
    text: str
    confidence: float
    reason: str


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip()


def signals(text: str) -> list[VisualSignal]:
    value = normalize(text)
    found: list[VisualSignal] = []
    for kind, terms in KEYWORDS.items():
        for term in terms:
            if term.startswith(r"\\b"):
                if re.search(term, value):
                    found.append(VisualSignal(term, kind, 1.0))
            elif term in value:
                found.append(VisualSignal(term, kind, 0.9))
    return found


def local_broll_matches(text: str, broll_dir: Path) -> list[dict]:
    """Keyword matcher only. Never scrapes or downloads stock footage."""
    value = normalize(text)
    if not broll_dir.exists():
        return []
    ranked: list[tuple[float, Path, str]] = []
    for path in broll_dir.iterdir():
        if not path.is_file() or path.suffix.lower() not in {".mp4", ".mov", ".mkv", ".webm"}:
            continue
        stem = normalize(path.stem).replace("_", " ").replace("-", " ")
        tokens = [t for t in re.split(r"[^\w]+", stem) if t]
        hits = sum(1 for token in tokens if token in value)
        if hits:
            ranked.append((min(1.0, hits / max(1, len(tokens))), path, "keyword"))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [{"path": str(path), "confidence": round(score, 3), "reason": reason} for score, path, reason in ranked if score >= 0.5][:3]


def headline_from_text(text: str) -> Headline | None:
    sentence = re.split(r"(?<=[.!?])\s+", text.strip())[0].strip()
    if not sentence:
        return None
    words = re.findall(r"\b[\w%'-]+\b", sentence, flags=re.UNICODE)
    if len(words) < 4:
        return None
    compact = " ".join(words[:12]).upper()
    return Headline(compact, 0.65 if len(words) <= 12 else 0.5, "first-sentence-baseline")


def emoji_for_text(text: str, enabled: bool = True, max_count: int = 2) -> list[str]:
    if not enabled:
        return []
    value = normalize(text)
    out: list[str] = []
    for term, emoji in EMOJI_RULES.items():
        if term in value and emoji not in out:
            out.append(emoji)
        if len(out) >= max_count:
            break
    return out


def visual_plan(text: str, broll_dir: Path, emoji_enabled: bool = False) -> dict:
    sig = [asdict(x) for x in signals(text)]
    broll = local_broll_matches(text, broll_dir)
    headline = headline_from_text(text)
    return {
        "signals": sig,
        "broll": broll,
        "headline": asdict(headline) if headline else None,
        "emoji": emoji_for_text(text, enabled=emoji_enabled),
        "broll_insert_threshold": 0.65,
    }
