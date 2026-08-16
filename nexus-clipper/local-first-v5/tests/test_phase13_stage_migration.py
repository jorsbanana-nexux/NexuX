from __future__ import annotations

from pathlib import Path

from stage_adapters import CONCRETE_STAGES, analyze_stage, ingest_stage, plan_stage, reason_stage, render_stage, transcribe_stage


def test_all_phase12_stages_have_concrete_adapter():
    expected = {"ingest", "transcribe", "analyze", "reason", "plan", "direct", "render", "critic", "revise", "publish", "feedback"}
    assert set(CONCRETE_STAGES) == expected


def test_ingest_is_fail_closed():
    try:
        ingest_stage({})
    except ValueError:
        pass
    else:
        raise AssertionError("ingest must reject incomplete context")


def test_analysis_requires_transcript():
    try:
        analyze_stage({})
    except ValueError:
        pass
    else:
        raise AssertionError("analysis must reject missing transcript")


def test_plan_requires_viable_candidates():
    try:
        plan_stage({"candidates": []})
    except RuntimeError:
        pass
    else:
        raise AssertionError("plan must reject an empty candidate set")


def test_render_requires_explicit_renderer():
    try:
        render_stage({})
    except RuntimeError:
        pass
    else:
        raise AssertionError("render must not fabricate success")


def test_reason_preserves_editorial_decision_shape():
    candidates = [{"id": "c1", "text": "This is why the result changed. The answer is simple."}]
    result = reason_stage({"candidates": candidates, "clip_prompt": None, "genre": "auto"})
    assert result["candidates"]
    assert "editorial_decision" in result
