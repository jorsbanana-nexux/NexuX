from __future__ import annotations

from analysis_world import build_analysis_world
from editorial_ranker import select_diverse_from_world
from editorial_world import build_editorial_evidence, ranking_context
from editorial_intent import EditorialIntent
from editorial_reasoning import reason_about_candidate, reason_candidates


def _world():
    return build_analysis_world(
        job_id="job-2b",
        media={"duration": 120},
        transcript={"language": "en", "segments": [{"start": 0, "end": 60, "text": "This is a complete story."}]},
        audio_profiles={
            "clip-a": {"rhythm": 90, "speech_density": 80, "clarity": 95},
            "clip-b": {"rhythm": 45, "speech_density": 50, "clarity": 60},
        },
        scenes=[{"start": 0, "end": 30}, {"start": 30, "end": 60}],
        subjects=[{"candidate_id": "clip-a", "confidence": 0.95}],
        candidates=[
            {"id": "clip-a", "start": 0.0, "end": 30.0, "duration": 30.0, "text": "A strong opening and payoff.", "scores": {"hook": 90}, "editorial": {"semantic": {"payoff_strength": 0.9, "context_completeness": 0.9, "standalone_quality": 0.9}}},
            {"id": "clip-b", "start": 60.0, "end": 90.0, "duration": 30.0, "text": "A weaker secondary point.", "scores": {"hook": 55}, "editorial": {"semantic": {"payoff_strength": 0.5, "context_completeness": 0.5, "standalone_quality": 0.5}}},
        ],
        editorial={"prompt": "find the strongest story", "genre": "storytelling"},
        provenance={"world": "analysis_world:v2", "audio": "audio_intelligence", "vision": "vision_service"},
        confidence={"transcript": 0.9, "audio": 0.85, "candidates": 0.8, "world": 0.85},
    )


def test_editorial_evidence_comes_from_world() -> None:
    world = _world()
    evidence = build_editorial_evidence(world)
    assert [item.candidate_id for item in evidence] == ["clip-a", "clip-b"]
    assert evidence[0].audio["rhythm"] == 90
    assert evidence[0].provenance


def test_ranking_context_is_world_scoped() -> None:
    context = ranking_context(_world())
    assert context["job_id"] == "job-2b"
    assert "audio" in context["modalities"]
    assert context["intent"]["prompt"] == "find the strongest story"


def test_final_selection_records_analysis_world_lineage() -> None:
    selected = select_diverse_from_world(_world(), limit=1, target_duration=30)
    assert len(selected) == 1
    assert selected[0]["id"] == "clip-a"
    assert selected[0]["analysis_world"]["job_id"] == "job-2b"
    assert selected[0]["analysis_world"]["schema_version"] == "2.0"


def _candidate(cid: str, text: str, start: float, payoff: float = 0.8) -> dict:
    return {
        "id": cid,
        "start": start,
        "end": start + 35,
        "duration": 35,
        "text": text,
        "editorial": {"semantic": {
            "payoff_strength": payoff,
            "context_completeness": 0.85,
            "standalone_quality": 0.85,
            "specificity": 0.8,
            "novelty_proxy": 0.7,
            "topic_coherence": 0.9,
        }},
        "scores": {"hook": 80},
        "narrative": {"tension": 0.7, "payoff": payoff, "revelation": 0.6},
    }


def test_intent_reasoning_prefers_required_topic():
    intent = EditorialIntent(objective="educational", required_topics=("python",), target_duration=35)
    wanted = _candidate("wanted", "Python solved the deployment problem", 0)
    other = _candidate("other", "The office was busy today", 40)
    ranked = reason_candidates([other, wanted], intent=intent)
    assert ranked[0]["id"] == "wanted"
    assert ranked[0]["intent_reasoning"]["required_topic_match"] > 0


def test_intent_reasoning_penalizes_excluded_topic():
    intent = EditorialIntent(objective="authority", excluded_topics=("politics",))
    clean = _candidate("clean", "We reduced latency by forty percent", 0)
    excluded = _candidate("excluded", "Politics changed the market", 40)
    clean_score = reason_about_candidate(clean, intent=intent)["intent_score"]
    excluded_score = reason_about_candidate(excluded, intent=intent)["intent_score"]
    assert clean_score > excluded_score


def test_world_selection_persists_explicit_intent_lineage():
    candidates = [
        _candidate("tech", "Python makes this workflow faster", 0),
        _candidate("general", "The meeting was interesting", 50),
    ]
    world = build_analysis_world(
        job_id="job-intent",
        transcript={"segments": []},
        candidates=candidates,
        editorial={
            "intent": {
                "objective": "educational",
                "required_topics": ["Python"],
                "target_duration": 35,
                "limit": 1,
            }
        },
        confidence={"world": 0.9},
    )
    selected = select_diverse_from_world(world, limit=1, target_duration=35)
    assert selected
    assert selected[0]["id"] == "tech"
    assert selected[0]["editorial_intent"]["required_topics"] == ["Python"]
    assert selected[0]["editorial_reasoning"]["required_topic_match"] > 0
