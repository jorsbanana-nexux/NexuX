from __future__ import annotations

import re
from typing import Any

from editorial_intent import EditorialIntent, normalize_intent


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[\w']+", text.casefold()))


def _topic_match(text: str, topics: tuple[str, ...]) -> float:
    if not topics:
        return 0.5
    words = _tokens(text)
    hits = sum(bool(_tokens(topic) & words) for topic in topics)
    return min(1.0, hits / max(1, len(topics)))


def reason_about_candidate(
    candidate: dict[str, Any],
    *,
    intent: EditorialIntent | dict[str, Any] | None = None,
) -> dict[str, Any]:
    intent = normalize_intent(intent)
    text = str(candidate.get("text", ""))
    editorial = candidate.get("editorial", {}).get("semantic", {}) or {}
    narrative = candidate.get("narrative", {}) or {}

    required = _topic_match(text, intent.required_topics)
    excluded = _topic_match(text, intent.excluded_topics) if intent.excluded_topics else 0.0
    duration = float(candidate.get("duration", 0.0))
    duration_fit = max(0.0, min(1.0, 1.0 - abs(duration - intent.target_duration) / max(10.0, intent.target_duration)))

    objective_weights = {
        "viral": {"hook": .30, "retention": .20, "payoff": .15, "novelty": .15, "tension": .20},
        "educational": {"context": .30, "coherence": .25, "specificity": .20, "payoff": .15, "retention": .10},
        "storytelling": {"tension": .25, "payoff": .25, "context": .20, "retention": .15, "novelty": .15},
        "emotional": {"tension": .25, "payoff": .20, "retention": .20, "novelty": .15, "hook": .20},
        "authority": {"specificity": .30, "context": .25, "coherence": .20, "payoff": .15, "novelty": .10},
    }
    weights = objective_weights.get(intent.objective.casefold(), {"hook": .20, "context": .20, "payoff": .20, "retention": .20, "novelty": .20})

    values = {
        "hook": float((candidate.get("scores") or {}).get("hook", 0.0)) / 100.0,
        "context": float(editorial.get("context_completeness", 0.0)),
        "coherence": float(editorial.get("topic_coherence", 0.0)),
        "specificity": float(editorial.get("specificity", 0.0)),
        "novelty": float(editorial.get("novelty_proxy", 0.0)),
        "payoff": float(editorial.get("payoff_strength", 0.0)),
        "tension": float(narrative.get("tension", 0.0)),
        "retention": float(candidate.get("ai_editorial", {}).get("scores", {}).get("retention", 0.0)) / 100.0,
    }
    base = sum(weights[key] * max(0.0, min(1.0, values[key])) for key in weights)
    score = max(0.0, min(1.0, base * 0.75 + required * 0.15 + duration_fit * 0.10 - excluded * 0.35))

    reasons: list[str] = []
    if required > 0.0:
        reasons.append("matches required topics")
    if excluded > 0.0:
        reasons.append("contains excluded-topic evidence")
    if duration_fit >= 0.8:
        reasons.append("fits target duration")
    if values["payoff"] >= 0.7:
        reasons.append("has strong payoff")
    if values["tension"] >= 0.7:
        reasons.append("contains narrative tension")
    if not reasons:
        reasons.append("matches general editorial objective")

    return {
        "intent_score": round(score, 6),
        "required_topic_match": round(required, 6),
        "excluded_topic_match": round(excluded, 6),
        "duration_fit": round(duration_fit, 6),
        "objective": intent.objective,
        "reason": reasons,
        "weights": dict(weights),
    }


def reason_candidates(
    candidates: list[dict[str, Any]],
    *,
    intent: EditorialIntent | dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    result = []
    for candidate in candidates:
        item = dict(candidate)
        item["intent_reasoning"] = reason_about_candidate(item, intent=intent)
        result.append(item)
    return sorted(result, key=lambda item: float(item["intent_reasoning"]["intent_score"]), reverse=True)
