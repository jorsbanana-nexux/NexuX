from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from contextual_narrative import ContextualNarrativeAssessment, verify_context

SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class AdaptiveContextAssessment:
    schema_version: str
    candidate_id: str
    initial_radius: float
    final_radius: float
    expansions: int
    max_radius: float
    assessment: ContextualNarrativeAssessment
    semantic_promise: str
    semantic_payoff: str
    semantic_match: float
    uncertainty: float
    stop_reason: str
    confidence: float
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "candidate_id": self.candidate_id,
            "initial_radius": self.initial_radius,
            "final_radius": self.final_radius,
            "expansions": self.expansions,
            "max_radius": self.max_radius,
            "assessment": self.assessment.to_dict(),
            "semantic_promise": self.semantic_promise,
            "semantic_payoff": self.semantic_payoff,
            "semantic_match": round(self.semantic_match, 3),
            "uncertainty": round(self.uncertainty, 3),
            "stop_reason": self.stop_reason,
            "confidence": round(self.confidence, 3),
            "reasons": list(self.reasons),
        }


def _tokens(text: str) -> set[str]:
    return {token for token in text.casefold().split() if token}


def _semantic_relation(promise: str, payoff: str) -> float:
    if not promise or not payoff:
        return 0.0
    a, b = _tokens(promise), _tokens(payoff)
    if not a or not b:
        return 0.0
    overlap = len(a & b) / max(1, len(a | b))
    resolution_terms = {"because", "therefore", "so", "result", "resulted", "finally", "reason", "why", "answer", "means"}
    resolution_bonus = min(0.25, len(b & resolution_terms) / 20.0)
    return max(0.0, min(1.0, overlap + resolution_bonus))


def _uncertainty(assessment: ContextualNarrativeAssessment, semantic_match: float) -> float:
    return max(
        0.0,
        min(
            1.0,
            0.45 * assessment.unresolved_question_risk
            + 0.30 * assessment.premature_cut_risk
            + 0.15 * (1.0 - assessment.context_integrity)
            + 0.10 * (1.0 - semantic_match),
        ),
    )


def adaptive_verify_context(
    candidate: Mapping[str, Any],
    transcript: Mapping[str, Any] | None = None,
    *,
    initial_radius: float = 12.0,
    expansion_step: float = 12.0,
    max_radius: float = 72.0,
    min_confidence: float = 0.78,
    min_semantic_match: float = 0.55,
) -> AdaptiveContextAssessment:
    transcript = transcript or {}
    radius = max(4.0, float(initial_radius))
    expansions = 0
    reasons: list[str] = []
    assessment: ContextualNarrativeAssessment | None = None
    semantic_match = 0.0
    stop_reason = "max_radius_reached"

    while True:
        assessment = verify_context(candidate, transcript, radius=radius)
        semantic_promise = assessment.promise_text or assessment.candidate.text
        semantic_payoff = assessment.payoff_text
        semantic_match = _semantic_relation(semantic_promise, semantic_payoff)
        uncertainty = _uncertainty(assessment, semantic_match)
        confidence = max(0.0, min(1.0, 0.55 * assessment.confidence + 0.45 * (1.0 - uncertainty)))

        if semantic_match >= min_semantic_match and confidence >= min_confidence and assessment.context_integrity >= 0.72:
            stop_reason = "sufficient_evidence"
            break
        if radius >= max_radius:
            stop_reason = "max_radius_reached"
            break
        if assessment.payoff_text and semantic_match >= min_semantic_match and uncertainty < 0.30:
            stop_reason = "resolved_with_low_uncertainty"
            break
        radius = min(max_radius, radius + max(4.0, expansion_step))
        expansions += 1

    assert assessment is not None
    if expansions:
        reasons.append(f"expanded context {expansions} time(s)")
    if assessment.payoff_text:
        reasons.append("located downstream payoff candidate")
    if semantic_match >= min_semantic_match:
        reasons.append("semantic promise-payoff relation cleared threshold")
    else:
        reasons.append("semantic promise-payoff relation remains uncertain")

    uncertainty = _uncertainty(assessment, semantic_match)
    confidence = max(0.0, min(1.0, 0.55 * assessment.confidence + 0.45 * (1.0 - uncertainty)))
    return AdaptiveContextAssessment(
        schema_version=SCHEMA_VERSION,
        candidate_id=str(candidate.get("id", "")),
        initial_radius=float(initial_radius),
        final_radius=float(radius),
        expansions=expansions,
        max_radius=float(max_radius),
        assessment=assessment,
        semantic_promise=assessment.promise_text or assessment.candidate.text,
        semantic_payoff=assessment.payoff_text,
        semantic_match=semantic_match,
        uncertainty=uncertainty,
        stop_reason=stop_reason,
        confidence=confidence,
        reasons=tuple(reasons),
    )
