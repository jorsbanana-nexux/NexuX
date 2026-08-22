r"""
NexuX V9.6 — Hook Lab
=====================
Two capabilities that go beyond Opus Clip's single-score approach:

1. ``generate_hook_variants`` — instead of one "best hook", produce N ranked
   hook candidates for the clip opening, each with its archetype, score and
   suggested start-shift. Creators pick the hook that fits their audience.
2. ``predict_title_ctr`` — a transparent CTR prediction for any title string,
   with per-factor strengths/weaknesses and concrete rewrite suggestions.

Both are deterministic, local and fully explainable — no black box.
"""
import logging
import math
import re
from typing import Dict, List, Optional

from .hook_detection import (
    HOOK_ARCHETYPES, _get_text_at_time, _identify_archetype, _score_hook_text,
)

log = logging.getLogger("nexus.hook_lab")

# ── CTR prediction lexicons (EN + ID) ──
_POWER_WORDS = [
    "secret", "truth", "never", "always", "stop", "mistake", "warning", "free",
    "proven", "shocking", "exposed", "banned", "illegal", "honest", "brutal",
    "rahasia", "terbongkar", "jangan", "ternyata", "kesalahan", "gratis",
    "bahaya", "dilarang", "jujur", "gila",
]
_CURIOSITY_PATTERNS = [
    r"\b(this is (why|how)|what (nobody|no one)|you (won'?t|will not) believe)\b",
    r"\b(the real reason|what happens|here'?s what)\b",
    r"\b(ini (kenapa|gimana)|yang (tidak|tak)|tak akan percaya)\b",
    r"\b(alasan sebenarnya|apa yang terjadi|begini caranya)\b",
]
_VAGUE_WORDS = {
    "video", "stuff", "things", "something", "clip", "content", "watch",
    "video", "hal", "sesuatu", "konten", "tonton",
}


def generate_hook_variants(
    clip: Dict,
    transcript: Dict,
    n: int = 5,
    scan_window: float = 20.0,
) -> List[Dict]:
    """Generate N ranked hook variants for a clip's opening.

    Scans the first ``scan_window`` seconds of the clip at multiple offsets
    and durations, scores each candidate and returns the top ``n`` unique
    variants, best first.
    """
    segments = transcript.get("segments", []) or []
    try:
        cs = float(clip.get("start", 0))
        ce = float(clip.get("end", cs + 60))
    except (TypeError, ValueError):
        return []

    scan_end = min(ce, cs + scan_window)
    candidates: List[Dict] = []

    offset = 0.0
    while offset < scan_end - cs:
        at = cs + offset
        for dur in (2.5, 4.0, 6.0):
            text = _get_text_at_time(segments, at, min(dur, ce - at))
            if len(text) < 12:
                continue
            score = _score_hook_text(text)
            archetype = _identify_archetype(text)
            candidates.append({
                "text": text[:120],
                "start_offset": round(offset, 2),
                "duration": dur,
                "score": round(score, 1),
                "archetype": archetype or "direct",
                "description": (
                    HOOK_ARCHETYPES.get(archetype, {}).get("description", "")
                    if archetype else "Straight into the content"
                ),
            })
        offset += 1.5

    # Dedupe on normalized text, keep the highest-scoring instance
    seen: Dict[str, Dict] = {}
    for c in sorted(candidates, key=lambda x: -x["score"]):
        key = re.sub(r"\W+", " ", c["text"].lower())[:60]
        if key not in seen:
            seen[key] = c

    variants = list(seen.values())[: max(1, n)]
    for rank, v in enumerate(variants, 1):
        v["rank"] = rank
    return variants


def predict_title_ctr(
    title: str,
    clip_text: str = "",
    language: str = "auto",
) -> Dict:
    """Predict relative CTR for a title (0-100) with full reasoning.

    Deterministic model over 7 factors: length, power words, curiosity gap,
    specificity, capitalization, punctuation, and vagueness penalty.
    Returns strengths, weaknesses and concrete rewrite suggestions.
    """
    title = (title or "").strip()
    if not title:
        return {"score": 0.0, "grade": "D", "strengths": [],
                "weaknesses": ["Empty title"], "suggestions": ["Write a title"]}

    lower = title.lower()
    words = re.findall(r"[\w']+", lower)
    strengths: List[str] = []
    weaknesses: List[str] = []
    suggestions: List[str] = []
    score = 40.0

    # ── 1. Length (ideal 35-65 chars, 5-10 words) ──
    n_chars, n_words = len(title), len(words)
    if 35 <= n_chars <= 65 and 5 <= n_words <= 10:
        score += 12
        strengths.append(f"Optimal length ({n_chars} chars, {n_words} words)")
    elif n_chars < 25:
        weaknesses.append(f"Too short ({n_chars} chars) — no context")
        suggestions.append("Expand to 35-65 characters with a concrete detail")
    else:
        score -= min(10, (n_chars - 65) * 0.15) if n_chars > 65 else 0
        if n_chars > 80:
            weaknesses.append(f"Too long ({n_chars} chars) — truncates on mobile")
            suggestions.append("Cut filler words; keep the hook under 65 chars")

    # ── 2. Power words ──
    power_hits = [w for w in _POWER_WORDS if re.search(rf"\b{re.escape(w)}\b", lower)]
    if power_hits:
        score += min(15, 6 + 3 * len(power_hits))
        strengths.append(f"Power words: {', '.join(power_hits[:3])}")
    else:
        weaknesses.append("No high-arousal power word")
        suggestions.append("Add one power word (e.g. 'secret', 'never', 'ternyata')")

    # ── 3. Curiosity gap ──
    if any(re.search(p, lower) for p in _CURIOSITY_PATTERNS):
        score += 12
        strengths.append("Open curiosity loop")
    elif "?" in title:
        score += 6
        strengths.append("Question format creates curiosity")
    else:
        suggestions.append("Open a curiosity loop ('This is why...', 'Ini kenapa...')")

    # ── 4. Specificity: numbers and named entities ──
    has_number = bool(re.search(r"\d", title))
    has_proper = any(w[:1].isupper() and len(w) > 2 for w in title.split())
    if has_number:
        score += 7
        strengths.append("Contains a number (specificity signal)")
    if has_proper:
        score += 3
    if not has_number and not has_proper and clip_text:
        suggestions.append("Add a number or name from the clip for specificity")

    # ── 5. Capitalization: one emphasized word, not ALL CAPS ──
    caps_words = [w for w in title.split() if len(w) > 1 and w.isupper()]
    if len(caps_words) == 1:
        score += 4
        strengths.append("One emphasized word (TENSION)")
    elif len(caps_words) > max(1, len(words) // 2):
        score -= 8
        weaknesses.append("ALL-CAPS reads as spam")
        suggestions.append("Emphasize ONE word in caps, not the whole title")

    # ── 6. Vagueness penalty ──
    vague = _VAGUE_WORDS & set(words)
    if vague and len(words) <= 8:
        score -= 6
        weaknesses.append(f"Vague filler: {', '.join(sorted(vague))[:40]}")

    score = max(0.0, min(100.0, score))
    grade = ("S" if score >= 85 else "A" if score >= 70 else
             "B" if score >= 55 else "C" if score >= 40 else "D")

    return {
        "score": round(score, 1),
        "grade": grade,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions[:3],
        "factors": {
            "length_chars": n_chars,
            "word_count": n_words,
            "power_words": power_hits,
            "has_number": has_number,
            "has_curiosity_gap": any(re.search(p, lower) for p in _CURIOSITY_PATTERNS),
        },
    }
