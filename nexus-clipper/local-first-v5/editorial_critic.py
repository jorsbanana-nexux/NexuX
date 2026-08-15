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
        return {"candidate_id": self.candidate_id, "verdict": self.verdict, "issues": list(self.issues), "adjustments": dict(self.adjustments), "confidence": self.confidence}


def _norm(value: Any) -> float:
    try:
        x = float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0
    return x / 100.0 if x > 1.0 else x


def critique_candidate(candidate: dict[str, Any]) -> Critique:
    start = float(candidate.get("start", 0.0))
    end = float(candidate.get("end", start))
    duration = max(0.0, end - start)
    issues: list[str] = []
    adjustments: dict[str, float] = {}
    signals = candidate.get("editorial_signals") or {}
    hook = _norm(signals.get("hook", candidate.get("hook")))
    payoff = _norm(signals.get("payoff", candidate.get("payoff")))
    context = _norm(signals.get("context", candidate.get("context")))
    coherence = _norm(signals.get("coherence", candidate.get("coherence")))

    if duration < 15.0: issues.append("too_short_for_reliable_context")
    if duration > 75.0: issues.append("long_clip_requires_stronger_retention_signal")
    if hook < 0.45:
        issues.append("weak_opening"); adjustments["start"] = -2.5
    if context < 0.45:
        issues.append("insufficient_context"); adjustments["start"] = min(adjustments.get("start", 0.0), -3.5)
    if payoff < 0.45:
        issues.append("weak_or_missing_payoff"); adjustments["end"] = max(adjustments.get("end", 0.0), 3.5)
    if coherence < 0.45: issues.append("low_coherence")

    verdict = "KEEP" if not issues else ("REFINE" if any(x in issues for x in ("weak_opening", "insufficient_context", "weak_or_missing_payoff")) else "REVIEW")
    confidence = max(0.0, min(1.0, 0.45 + 0.1 * (4 - min(4, len(issues)))))
    return Critique(str(candidate.get("id", "unknown")), verdict, tuple(issues), adjustments, confidence)


def apply_critique(candidate: dict[str, Any], critique: Critique) -> dict[str, Any]:
    refined = dict(candidate)
    start = max(0.0, float(candidate.get("start", 0.0)) + critique.adjustments.get("start", 0.0))
    end = max(start + 1.0, float(candidate.get("end", start)) + critique.adjustments.get("end", 0.0))
    refined.update(start=start, end=end, critic=critique.to_dict(), refined=critique.verdict == "REFINE")
    return refined
