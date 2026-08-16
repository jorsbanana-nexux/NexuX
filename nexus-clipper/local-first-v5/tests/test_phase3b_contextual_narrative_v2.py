from analysis_world import build_analysis_world
from contextual_narrative import verify_context
from contextual_reasoning import contextual_score, enrich_world_with_context
from intent_aware_selection import select_diverse_from_world_with_intent


def transcript():
    return {"segments": [
        {"start": 0, "end": 6, "text": "Why did we almost fail?"},
        {"start": 6, "end": 12, "text": "The reason was our acquisition costs."},
        {"start": 12, "end": 18, "text": "We kept spending without measuring the return."},
        {"start": 18, "end": 24, "text": "Then we changed the model."},
        {"start": 24, "end": 30, "text": "As a result, our margin recovered."},
        {"start": 30, "end": 36, "text": "That was the turning point."},
    ]}


def test_context_verification_finds_later_payoff():
    candidate = {"id": "c1", "start": 0.0, "end": 18.0, "text": "Why did we almost fail? The reason was our acquisition costs."}
    assessment = verify_context(candidate, transcript(), radius=18.0)
    assert assessment.payoff_text
    assert assessment.to_dict()["after"]


def test_world_gets_contextual_evidence():
    world = build_analysis_world(
        job_id="ctx-1", transcript=transcript(),
        candidates=[{"id": "c1", "start": 0.0, "end": 18.0, "duration": 18.0, "text": "Why did we almost fail?"}],
        editorial={"intent": {"objective": "storytelling"}},
        provenance={"world": "analysis_world:v2"}, confidence={"world": 0.8},
    )
    enriched = enrich_world_with_context(world)
    contextual = enriched.candidates[0]["contextual_narrative"]
    assert contextual["candidate_id"] == "c1"
    assert contextual["payoff_text"]
    assert "contextual_narrative" in enriched.provenance


def test_contextual_score_penalizes_premature_ending():
    candidate = {"contextual_narrative": {"context_integrity": 0.55, "promise_payoff_match": 0.1, "premature_cut_risk": 0.9}}
    assert contextual_score(candidate) < 0.3


def test_selection_preserves_contextual_lineage():
    world = build_analysis_world(
        job_id="ctx-2", transcript=transcript(),
        candidates=[
            {"id": "c1", "start": 0.0, "end": 18.0, "duration": 18.0, "text": "Why did we almost fail?"},
            {"id": "c2", "start": 18.0, "end": 36.0, "duration": 18.0, "text": "As a result, our margin recovered. That was the turning point."},
        ],
        editorial={"intent": {"objective": "storytelling"}},
        provenance={"world": "analysis_world:v2"}, confidence={"world": 0.8},
    )
    selected = select_diverse_from_world_with_intent(world, limit=1, target_duration=18.0)
    assert len(selected) == 1
    assert "contextual_reasoning" in selected[0]
    assert "analysis_world" in selected[0]
