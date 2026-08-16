from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence


@dataclass(frozen=True)
class RevisionAction:
    action: str
    target: str = ""
    reason: str = ""
    priority: float = 0.0
    parameters: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "target": self.target,
            "reason": self.reason,
            "priority": round(float(self.priority), 3),
            "parameters": dict(self.parameters),
        }


@dataclass(frozen=True)
class EditIteration:
    attempt: int
    verdict: str
    quality: float
    critique: Mapping[str, Any]
    actions: tuple[RevisionAction, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt": self.attempt,
            "verdict": self.verdict,
            "quality": round(float(self.quality), 4),
            "critique": dict(self.critique),
            "actions": [action.to_dict() for action in self.actions],
        }


@dataclass(frozen=True)
class AutonomousEditSession:
    schema_version: str
    session_id: str
    plan_id: str
    max_attempts: int
    success_threshold: float
    iterations: tuple[EditIteration, ...] = ()
    final_verdict: str = "REVIEW"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "session_id": self.session_id,
            "plan_id": self.plan_id,
            "max_attempts": self.max_attempts,
            "success_threshold": self.success_threshold,
            "iterations": [item.to_dict() for item in self.iterations],
            "final_verdict": self.final_verdict,
        }


SCHEMA_VERSION = "1.0"


def _normalize_actions(raw: Sequence[Mapping[str, Any]] | None) -> tuple[RevisionAction, ...]:
    actions: list[RevisionAction] = []
    for item in raw or ():
        actions.append(
            RevisionAction(
                action=str(item.get("action", "review")),
                target=str(item.get("target", "")),
                reason=str(item.get("reason", "")),
                priority=float(item.get("priority", 0.0) or 0.0),
                parameters=dict(item.get("parameters", {}) or {}),
            )
        )
    return tuple(actions)


def run_autonomous_edit_session(
    *,
    session_id: str,
    plan_id: str,
    initial_render: Mapping[str, Any],
    critic: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    revise: Callable[[Mapping[str, Any], Sequence[RevisionAction], int], Mapping[str, Any]],
    max_attempts: int = 2,
    success_threshold: float = 0.80,
) -> AutonomousEditSession:
    """Bounded render -> critic -> revise loop. The callbacks own actual media work."""
    current = dict(initial_render)
    iterations: list[EditIteration] = []

    for attempt in range(max(1, int(max_attempts)) + 1):
        report = dict(critic(current) or {})
        quality = max(0.0, min(1.0, float(report.get("quality", report.get("score", 0.0)) or 0.0)))
        verdict = str(report.get("verdict", "PASS" if quality >= success_threshold else "REFINE"))
        actions = _normalize_actions(report.get("actions"))
        iterations.append(EditIteration(attempt=attempt, verdict=verdict, quality=quality, critique=report, actions=actions))

        if quality >= success_threshold or verdict in {"PASS", "KEEP"}:
            return AutonomousEditSession(SCHEMA_VERSION, session_id, plan_id, max_attempts, success_threshold, tuple(iterations), "PASS")
        if attempt >= max_attempts:
            return AutonomousEditSession(SCHEMA_VERSION, session_id, plan_id, max_attempts, success_threshold, tuple(iterations), "REVIEW")
        if not actions:
            return AutonomousEditSession(SCHEMA_VERSION, session_id, plan_id, max_attempts, success_threshold, tuple(iterations), "REVIEW")
        current = dict(revise(current, actions, attempt + 1) or current)

    return AutonomousEditSession(SCHEMA_VERSION, session_id, plan_id, max_attempts, success_threshold, tuple(iterations), "REVIEW")
