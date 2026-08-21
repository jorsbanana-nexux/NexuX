from __future__ import annotations

from autonomous_edit_session import run_autonomous_edit_session
from autonomous_editor import run_editorial_revision_loop
from edit_quality_gate import evaluate_render_quality


def test_quality_gate_passes_clean_render():
    result = evaluate_render_quality({"quality": 0.92, "issues": []})
    assert result["verdict"] == "PASS"
    assert result["eligible_for_publish"] is True


def test_session_revises_until_pass():
    seen = []

    def critic(state):
        seen.append(state["version"])
        if state["version"] == 0:
            return {"quality": 0.50, "verdict": "REFINE", "actions": [{"action": "tighten_cut", "priority": 1.0}]}
        return {"quality": 0.90, "verdict": "PASS", "actions": []}

    def revise(state, actions, attempt):
        return {**state, "version": attempt}

    session = run_autonomous_edit_session(
        session_id="s1",
        plan_id="p1",
        initial_render={"version": 0},
        critic=critic,
        revise=revise,
        max_attempts=2,
        success_threshold=0.80,
    )
    assert session.final_verdict == "PASS"
    assert len(session.iterations) == 2
    assert seen == [0, 1]


def test_editor_loop_uses_guarded_critic():
    state = {"version": 0}

    def critic(_state):
        return {"quality": 0.60, "verdict": "REFINE", "issues": []}

    def renderer(_state, _actions, attempt):
        return {"version": attempt + 1}

    session = run_editorial_revision_loop(
        session_id="s2",
        plan_id="p2",
        render_state=state,
        critic=critic,
        renderer=renderer,
        max_attempts=1,
        threshold=0.80,
    )
    assert session.final_verdict == "REVIEW"
    # REVIEW may stop after max_attempts==1 loop; verify the gate verdict.
    assert session.final_verdict == "REVIEW"
