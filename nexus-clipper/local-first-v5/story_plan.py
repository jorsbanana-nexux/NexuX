from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "1.0"
VALID_DECISIONS = frozenset({"DRAFT", "KEEP", "REFINE", "REJECT", "REVIEW"})


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _thaw(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw(v) for v in value]
    return value


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class StoryPlan:
    """Immutable editorial strategy; it describes a story structure, not a rendered edit."""

    schema_version: str
    plan_id: str
    job_id: str
    objective: str
    audience: str
    platform: str
    tone: str
    style: str
    opening: Mapping[str, Any]
    setup: tuple[Mapping[str, Any], ...]
    escalation: tuple[Mapping[str, Any], ...]
    core: tuple[Mapping[str, Any], ...]
    revelation: Mapping[str, Any]
    payoff: Mapping[str, Any]
    ending: Mapping[str, Any]
    total_duration: float
    narrative_coherence: float
    promise_payoff_integrity: float
    context_integrity: float
    retention_estimate: float
    visual_feasibility: float
    audio_feasibility: float
    intent_match: float
    diversity: float
    confidence: float
    evidence: Mapping[str, Any]
    reasons: tuple[str, ...] = field(default_factory=tuple)
    risks: tuple[str, ...] = field(default_factory=tuple)
    decision: str = "DRAFT"

    def validate(self) -> "StoryPlan":
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"unsupported StoryPlan schema: {self.schema_version}")
        if not self.plan_id or not self.job_id:
            raise ValueError("plan_id and job_id are required")
        if self.decision not in VALID_DECISIONS:
            raise ValueError(f"invalid StoryPlan decision: {self.decision}")
        if self.total_duration < 0:
            raise ValueError("total_duration cannot be negative")
        bounded = (
            self.narrative_coherence,
            self.promise_payoff_integrity,
            self.context_integrity,
            self.retention_estimate,
            self.visual_feasibility,
            self.audio_feasibility,
            self.intent_match,
            self.diversity,
            self.confidence,
        )
        if any(not 0.0 <= float(v) <= 1.0 for v in bounded):
            raise ValueError("StoryPlan quality fields must be in [0,1]")
        if any(not isinstance(item, Mapping) for item in (*self.setup, *self.escalation, *self.core)):
            raise ValueError("StoryPlan sequence entries must be mappings")
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "plan_id": self.plan_id,
            "job_id": self.job_id,
            "objective": self.objective,
            "audience": self.audience,
            "platform": self.platform,
            "tone": self.tone,
            "style": self.style,
            "opening": _thaw(self.opening),
            "setup": [_thaw(v) for v in self.setup],
            "escalation": [_thaw(v) for v in self.escalation],
            "core": [_thaw(v) for v in self.core],
            "revelation": _thaw(self.revelation),
            "payoff": _thaw(self.payoff),
            "ending": _thaw(self.ending),
            "total_duration": round(self.total_duration, 3),
            "narrative_coherence": round(self.narrative_coherence, 3),
            "promise_payoff_integrity": round(self.promise_payoff_integrity, 3),
            "context_integrity": round(self.context_integrity, 3),
            "retention_estimate": round(self.retention_estimate, 3),
            "visual_feasibility": round(self.visual_feasibility, 3),
            "audio_feasibility": round(self.audio_feasibility, 3),
            "intent_match": round(self.intent_match, 3),
            "diversity": round(self.diversity, 3),
            "confidence": round(self.confidence, 3),
            "evidence": _thaw(self.evidence),
            "reasons": list(self.reasons),
            "risks": list(self.risks),
            "decision": self.decision,
        }


def build_story_plan(
    *,
    plan_id: str,
    job_id: str,
    objective: str,
    audience: str = "",
    platform: str = "generic",
    tone: str = "",
    style: str = "",
    opening: Mapping[str, Any] | None = None,
    setup: Sequence[Mapping[str, Any]] = (),
    escalation: Sequence[Mapping[str, Any]] = (),
    core: Sequence[Mapping[str, Any]] = (),
    revelation: Mapping[str, Any] | None = None,
    payoff: Mapping[str, Any] | None = None,
    ending: Mapping[str, Any] | None = None,
    total_duration: float = 0.0,
    narrative_coherence: float = 0.0,
    promise_payoff_integrity: float = 0.0,
    context_integrity: float = 0.0,
    retention_estimate: float = 0.0,
    visual_feasibility: float = 0.0,
    audio_feasibility: float = 0.0,
    intent_match: float = 0.0,
    diversity: float = 0.0,
    confidence: float = 0.0,
    evidence: Mapping[str, Any] | None = None,
    reasons: Sequence[str] = (),
    risks: Sequence[str] = (),
    decision: str = "DRAFT",
) -> StoryPlan:
    plan = StoryPlan(
        schema_version=SCHEMA_VERSION,
        plan_id=plan_id,
        job_id=job_id,
        objective=objective,
        audience=audience,
        platform=platform,
        tone=tone,
        style=style,
        opening=_freeze(dict(opening or {})),
        setup=tuple(_freeze(dict(v)) for v in setup),
        escalation=tuple(_freeze(dict(v)) for v in escalation),
        core=tuple(_freeze(dict(v)) for v in core),
        revelation=_freeze(dict(revelation or {})),
        payoff=_freeze(dict(payoff or {})),
        ending=_freeze(dict(ending or {})),
        total_duration=float(total_duration),
        narrative_coherence=float(narrative_coherence),
        promise_payoff_integrity=float(promise_payoff_integrity),
        context_integrity=float(context_integrity),
        retention_estimate=float(retention_estimate),
        visual_feasibility=float(visual_feasibility),
        audio_feasibility=float(audio_feasibility),
        intent_match=float(intent_match),
        diversity=float(diversity),
        confidence=float(confidence),
        evidence=_freeze(dict(evidence or {})),
        reasons=tuple(str(v) for v in reasons),
        risks=tuple(str(v) for v in risks),
        decision=decision,
    )
    return plan.validate()
