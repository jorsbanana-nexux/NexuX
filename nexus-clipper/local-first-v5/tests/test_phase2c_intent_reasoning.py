from __future__ import annotations

from analysis_world import build_analysis_world
from editorial_intent import EditorialIntent
from editorial_reasoning import reason_about_candidate
from intent_aware_selection import select_diverse_from_world_with_intent


def _candidate(cid: str, text: str, payoff: float, tension: float) -> dict:
    return {
        "id": cid,
        "start": 10.0,
        "end": 50.0,
        "duration": 40.0,
        "text": text,
        "scores": {"hook": 80.0},
        "narrative": {"payoff": payoff, "tension": tension},
        "editorial": {"semantic": {"payoff_strength": payoff, "context_completeness": .9, "standalone_quality": .9, "specificity": .8, "novelty_proxy": .7, "topic_coherence": .9}},
    }


def test_intent_reasoning_rewards_required_topic() -> None:
    intent = EditorialIntent(objective="educational", required_topics=("quantum",))
    hit = reason_about_candidate(_candidate("a", "quantum computing changes everything", .8, .2), intent=intent)
    miss = reason_about_candidate(_candidate("b", "cooking changes everything", .8, .2), intent=intent)
    assert hit["intent_score"] > miss["intent_score"]
    assert hit["required_topic_match"] == 1.0


def test_excluded_topic_is_penalized() -> None:
    intent = EditorialIntent(excluded_topics=("politics",))
    result = reason_about_candidate(_candidate("a", "politics and business", .8, .8), intent=intent)
    assert result["excluded_topic_match"] == 1.0
    assert result["intent_score"] < 0.75


def test_world_selection_persists_intent_lineage() -> None:
    intent = EditorialIntent(objective="storytelling", required_topics=("launch",), limit=1)
    world = build_analysis_world(
        job_id="job-intent",
        transcript={"segments": []},
        candidates=[
            _candidate("a", "the launch changed our company", .9, .8),
            _candidate("b", "the office was renovated", .9, .8),
        ],
        editorial={"intent": intent.to_dict()},
        provenance={"world": "analysis_world:v2", "intent": "editorial_intent:v1"},
        confidence={"world": .9},
    )
    selected = select_diverse_from_world_with_intent(world, limit=1)
    assert selected
    assert selected[0]["id"] == "a"
    assert selected[0]["intent"]["objective"] == "storytelling"
    assert selected[0]["analysis_world"]["job_id"] == "job-intent"
