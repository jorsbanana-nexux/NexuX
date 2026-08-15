from __future__ import annotations

import math
import re
from dataclasses import dataclass, asdict


_STOP = {
    "yang", "dan", "atau", "di", "ke", "dari", "ini", "itu", "untuk", "dengan", "the", "and", "or", "to", "of", "a", "an", "is", "are", "in"
}

@dataclass(frozen=True)
class SemanticFeatures:
    topic_coherence: float
    opening_strength: float
    payoff_strength: float
    specificity: float
    novelty_proxy: float
    context_completeness: float
    standalone_quality: float
    retention_risk: float

    def to_dict(self) -> dict[str, float]:
        return {k: round(v, 3) for k, v in asdict(self).items()}


def _tokens(text: str) -> list[str]:
    words = re.findall(r"[\w%'-]+", text.casefold(), flags=re.UNICODE)
    return [w for w in words if w not in _STOP and len(w) > 1]


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / max(1, len(union))


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def analyze_semantics(text: str, opening: str = "") -> SemanticFeatures:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]
    toks = _tokens(text)
    open_toks = set(_tokens(opening or (sentences[0] if sentences else "")))

    if len(sentences) <= 1:
        coherence = 0.55
    else:
        sets = [set(_tokens(s)) for s in sentences]
        pair_scores = [_jaccard(sets[i - 1], sets[i]) for i in range(1, len(sets))]
        coherence = sum(pair_scores) / len(pair_scores)

    first = sentences[0] if sentences else text
    last = sentences[-1] if sentences else text
    question = 1.0 if "?" in first else 0.0
    direct = 1.0 if re.search(r"\b(kamu|you|cara|how|why|kenapa|what|ternyata)\b", first.casefold()) else 0.0
    opening_strength = _clamp(0.55 * question + 0.45 * direct + min(0.25, len(_tokens(first)) / 32))

    payoff_terms = re.findall(r"\b(jadi|hasilnya|intinya|akhirnya|berarti|so|therefore|because|kesimpulannya|the result)\b", last.casefold())
    payoff_strength = _clamp((0.6 if payoff_terms else 0.25) + min(0.4, len(_tokens(last)) / 25))

    numeric = len(re.findall(r"\b\d+(?:[.,]\d+)?%?\b", text))
    specificity = _clamp(min(1.0, numeric / 3) * 0.5 + min(0.5, len(set(toks)) / 40))

    freq: dict[str, int] = {}
    for token in toks:
        freq[token] = freq.get(token, 0) + 1
    unique_ratio = len(set(toks)) / max(1, len(toks))
    novelty_proxy = _clamp(0.45 * unique_ratio + 0.55 * (1.0 - min(1.0, max(freq.values(), default=1) / 8)))

    pronoun_start = bool(re.search(r"\b(it|this|that|he|she|they|dia|itu|ini|mereka|dia)\b", first.casefold()))
    context_completeness = _clamp(0.75 - (0.35 if pronoun_start else 0.0) + (0.25 if len(sentences) >= 3 else 0.0))
    standalone_quality = _clamp(0.45 * context_completeness + 0.3 * opening_strength + 0.25 * payoff_strength)

    retention_risk = _clamp(
        0.45 * (1.0 - opening_strength)
        + 0.3 * (1.0 - payoff_strength)
        + 0.25 * (1.0 - coherence)
    )

    return SemanticFeatures(
        topic_coherence=_clamp(coherence),
        opening_strength=_clamp(opening_strength),
        payoff_strength=_clamp(payoff_strength),
        specificity=_clamp(specificity),
        novelty_proxy=_clamp(novelty_proxy),
        context_completeness=_clamp(context_completeness),
        standalone_quality=_clamp(standalone_quality),
        retention_risk=_clamp(retention_risk),
    )


def semantic_bonus(features: SemanticFeatures) -> float:
    return 100.0 * (
        0.20 * features.topic_coherence
        + 0.20 * features.opening_strength
        + 0.18 * features.payoff_strength
        + 0.10 * features.specificity
        + 0.10 * features.novelty_proxy
        + 0.14 * features.context_completeness
        + 0.08 * features.standalone_quality
        - 0.08 * features.retention_risk
    )
