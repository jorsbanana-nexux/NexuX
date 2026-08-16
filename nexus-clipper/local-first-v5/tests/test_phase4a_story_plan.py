from story_plan import SCHEMA_VERSION, build_story_plan


def test_story_plan_is_versioned_immutable_and_serializable():
    plan = build_story_plan(
        plan_id="p1",
        job_id="job1",
        objective="viral",
        platform="youtube_shorts",
        opening={"candidate_id": "c1", "start": 10.0, "end": 16.0},
        setup=[{"candidate_id": "c2"}],
        core=[{"candidate_id": "c3"}],
        payoff={"candidate_id": "c4"},
        ending={"candidate_id": "c5"},
        total_duration=42,
        narrative_coherence=0.9,
        promise_payoff_integrity=0.88,
        context_integrity=0.86,
        retention_estimate=0.82,
        visual_feasibility=0.95,
        audio_feasibility=0.92,
        intent_match=0.9,
        diversity=0.8,
        confidence=0.84,
        evidence={"world_schema": "2.0"},
        decision="DRAFT",
    )
    assert plan.schema_version == SCHEMA_VERSION
    assert plan.setup[0]["candidate_id"] == "c2"
    assert plan.to_dict()["plan_id"] == "p1"


def test_story_plan_rejects_invalid_decision_and_out_of_range_scores():
    try:
        build_story_plan(plan_id="p", job_id="j", objective="x", decision="NOPE")
        assert False
    except ValueError as exc:
        assert "decision" in str(exc)

    try:
        build_story_plan(plan_id="p", job_id="j", objective="x", confidence=1.5)
        assert False
    except ValueError as exc:
        assert "quality" in str(exc)
