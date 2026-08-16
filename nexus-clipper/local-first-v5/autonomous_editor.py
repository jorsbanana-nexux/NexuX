from __future__ import annotations

from typing import Any, Callable, Mapping

from autonomous_edit_session import AutonomousEditSession, run_autonomous_edit_session
from edit_quality_gate import evaluate_render_quality
from revision_engine import build_revision_actions


def run_editorial_revision_loop(
    *,
    session_id: str,
    plan_id: str,
    render_state: Mapping[str, Any],
    critic: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    renderer: Callable[[Mapping[str, Any], list[dict[str, Any]], int], Mapping[str, Any]],
    max_attempts: int = 2,
    threshold: float = 0.80,
) -> AutonomousEditSession:
    def guarded_critic(state: Mapping[str, Any]) -> Mapping[str, Any]:
        report = dict(critic(state) or {})
        gate = evaluate_render_quality(report, threshold=threshold)
        return {**report, **gate, "actions": [action.to_dict() for action in build_revision_actions(report)]}

    def revise(state: Mapping[str, Any], actions: Any, attempt: int) -> Mapping[str, Any]:
        return dict(renderer(dict(state), [action.to_dict() for action in actions], attempt) or state)

    return run_autonomous_edit_session(
        session_id=session_id,
        plan_id=plan_id,
        initial_render=render_state,
        critic=guarded_critic,
        revise=revise,
        max_attempts=max_attempts,
        success_threshold=threshold,
    )
