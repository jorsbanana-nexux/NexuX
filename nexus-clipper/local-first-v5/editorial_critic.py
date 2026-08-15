from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Critique:
    candidate_id: str
    verdict: str
    issues: tuple[str, ...] = ()
    adjustments: dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "verdict": self.verdict,
            "issues": list(self.issues),
            "adjustments": dict(self.adjustments),
            "confidence": self.confidence,
        }


def critique_candidate(candidate: dict[str, Any]) -> Critique:
    start = float(candidate.get("start", 0.0))
    end = float(candidate.get("end", start))
    duration = max(0.0, end - start)
    issues: list[str] = []
    adjustments: dict[str, float] = {}

    signals = candidate.get("editorial_signals") or {}
    hook = float(signals.get("hook", candidate.get("hook", 0.0)) or 0.0)
    payoff = float(signals.get("payoff", candidate.get("payoff", 0.0)) or 0.0)
    context = float(signals.get("context", candidate.get("context", 0.0)) or 0.0)
    coherence = float(signals.get("coherence", candidate.get("coherence", 0.0)) or 0.0)

    if duration < 15.0:
        issues.append("too_short_for_reliable_context")
    elif duration > 75.0:
        issues.append("long_clip_requires_stronger_retention_signal")

    if hook < 0.45:
        issues.append("weak_opening")
        adjustments["start"] = -2.5

    if context < 0.45:
        issues.append("insufficient_context")
        adjustments["start"] = min(adjustments.get("start", 0.0), -3.5)

    if payoff < 0.45:
        issues.append("weak_or_missing_payoff")
        adjustments["end"] = max(adjustments.get("end", 0.0), 3.5)

    if coherence < 0.45:
        issues.append("low_coherence")

    if not issues:
        verdict = "KEEP"
    elif any(x in issues for x in ("weak_opening", "insufficient_context", "weak_or_missing_payoff")):
        verdict = "REFINE"
    else:
        verdict = "REVIEW"

    confidence = max(0.0, min(1.0, 0.45 + 0.1 * (4 - min(4, len(issues)))))
    return Critique(
        candidate_id=str(candidate.get("id", "unknown")),
        verdict=verdict,
        issues=tuple(issues),
        adjustments=adjustments,
        confidence=confidence,
    )


def apply_critique(candidate: dict[str, Any], critique: Critique) -> dict[str, Any]:
    refined = dict(candidate)
    start = max(0.0, float(candidate.get("start", 0.0)) + critique.adjustments.get("start", 0.0))
    end = max(start + 1.0, float(candidate.get("end", start)) + critique.adjustments.get("end", 0.0))
    refined["start"] = start
    refined["end"] = end
    refined["critic"] = critique.to_dict()
    refined["refined"] = critique.verdict == "REFINE"
    return refined
