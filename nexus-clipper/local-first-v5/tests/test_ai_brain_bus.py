from __future__ import annotations

import os

from ai_brain_config import AI_BRAINS, selected_brain
from ai_editorial import evaluate_with_provider
from editorial_ranker import _ai_rejudge


class StubProvider:
    def evaluate(self, packet):
        assert packet["schema_version"] == "nexux.editorial.v1"
        return {
            "verdict": "KEEP",
            "confidence": 0.91,
            "scores": {
                "hook": 0.92,
                "context": 0.88,
                "tension": 0.84,
                "payoff": 0.90,
                "retention": 0.87,
                "novelty": 0.81,
                "shareability": 0.89,
            },
            "adjustments": {"start": -1.2, "end": 0.8},
            "evidence": ["strong opening", "complete payoff"],
            "summary": "Keep this candidate.",
        }


def test_ai_decision_schema_is_safe():
    decision = evaluate_with_provider(StubProvider(), {"candidate": {"id": "x"}, "schema_version": "nexux.editorial.v1"})
    assert decision.verdict == "KEEP"
    assert decision.confidence == 0.91
    assert 0.0 <= decision.scores["hook"] <= 1.0
    assert -15.0 <= decision.adjustments["start"] <= 15.0


def test_ai_rejudge_works_without_provider_key():
    old = {k: os.environ.pop(k, None) for brain in AI_BRAINS for k in (brain.endpoint_env, brain.api_key_env, brain.model_env)}
    try:
        item = _ai_rejudge({"id": "demo", "text": "A strong hook and payoff."})
        assert item["ai_editorial"]["verdict"] == "REVIEW"
        assert item["ai_rejudge_active"] is False
    finally:
        for key, value in old.items():
            if value is not None:
                os.environ[key] = value


def test_selected_brain_is_never_secret_exposed():
    brain = selected_brain()
    if brain is None:
        assert all(not getattr(item, "api_key", "") for item in AI_BRAINS)
    else:
        assert brain.name in {item.name for item in AI_BRAINS}
