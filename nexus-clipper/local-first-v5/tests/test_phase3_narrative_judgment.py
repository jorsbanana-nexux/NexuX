from __future__ import annotations

from analysis_world import build_analysis_world
from intent_aware_selection import select_diverse_from_world_with_intent
from narrative_model import assess_narrative


def _candidate(text: str) -> dict:
    return {
        "id": "story-1",
        "start": 0.0,
        "end": 40.0,
        "duration": 40.0,
        "text": text,
        "scores": {"hook": 90},
        "editorial": {"semantic": {"payoff_strength": 0.9, "context_completeness": 0.85, "standalone_quality": 0.85, "specificity": 0.8, "novelty_proxy": 0.8, "topic_coherence": 0.9}},
        "narrative": {"tension": 0.8, "revelation": 0.8, "payoff": 0.8},
    }


def test_narrative_detects_promise_and_payoff() -> None:
    candidate = _candidate("How did we recover? Here's how. We lost everything, but then we realized the mistake. The answer is simple, and that's why we finally recovered.")
    result = assess_narrative(candidate, {"segments": [{"start": 0, "end": 20, "text": candidate["text"]}]})
    assert result.promise_strength >= 0.5
    assert result.payoff_strength >= 0.7
    assert result.continuity_risk < 0.8
    assert result.recommendation in {"KEEP", "REFINE"}


def test_narrative_flags_unresolved_question() -> None:
    candidate = _candidate("Why did the company fail? It looked successful for years, but the real problem was hidden.")
    result = assess_narrative(candidate, {"segments": [{"start": 0, "end": 20, "text": candidate["text"]}]})
    assert result.unresolved_question_risk > 0.5
    assert result.premature_cut_risk > 0.3


def test_intent_selection_carries_narrative_reasoning() -> None:
    world = build_analysis_world(
        job_id="phase3-test",
        transcript={"segments": [{"start": 0, "end": 50, "text": "How did we recover? Here's how. We failed, but then we realized the problem. The answer is to fix the root cause, and that's why we recovered."}]},
        audio_profiles={"story-1": {"rhythm": 90, "speech_density": 80, "clarity": 95}},
        scenes=[{"start": 0, "end": 25}, {"start": 25, "end": 50}],
        candidates=[_candidate("How did we recover? Here's how. We failed, but then we realized the problem. The answer is to fix the root cause, and that's why we recovered.")],
        editorial={"intent": {"objective": "storytelling", "target_duration": 40, "limit": 1}},
        provenance={"world": "analysis_world:v2"},
        confidence={"world": 0.9},
    )
    selected = select_diverse_from_world_with_intent(world, limit=1, target_duration=40)
    assert selected
    assert selected[0]["narrative_reasoning"]["score"] > 0.0
    assert "analysis_world" in selected[0]
