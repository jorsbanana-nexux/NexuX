from analysis_world import build_analysis_world
from intent_aware_selection import select_diverse_from_world_with_intent


def test_selection_contains_adaptive_context_reasoning() -> None:
    world = build_analysis_world(
        job_id="phase3c-job",
        media={"duration": 90},
        transcript={"segments": [
            {"start": 0, "end": 5, "text": "Why did we nearly fail?"},
            {"start": 5, "end": 20, "text": "Our acquisition costs were too high."},
            {"start": 20, "end": 32, "text": "We changed the model and reduced waste."},
            {"start": 32, "end": 48, "text": "Finally our margins recovered because of that change."},
        ]},
        candidates=[{
            "id": "candidate-1",
            "start": 0,
            "end": 32,
            "duration": 32,
            "text": "Why did we nearly fail? Our acquisition costs were too high. We changed the model and reduced waste.",
            "scores": {"hook": 90},
            "editorial": {"semantic": {"payoff_strength": 0.7, "context_completeness": 0.8, "standalone_quality": 0.8, "specificity": 0.7, "novelty_proxy": 0.6, "topic_coherence": 0.8}},
        }],
        editorial={"intent": {"objective": "storytelling", "target_duration": 32, "limit": 1}},
        confidence={"transcript": 0.9, "candidates": 0.7, "world": 0.8},
    )
    selected = select_diverse_from_world_with_intent(world, limit=1, target_duration=32)
    assert selected
    assert "adaptive_context_reasoning" in selected[0]
    assert selected[0]["adaptive_context_reasoning"]["final_radius"] >= 12
