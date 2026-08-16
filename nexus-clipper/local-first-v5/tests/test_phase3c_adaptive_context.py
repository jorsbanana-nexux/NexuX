from adaptive_context import adaptive_verify_context


def test_adaptive_context_expands_until_payoff_is_found() -> None:
    transcript = {
        "segments": [
            {"start": 0, "end": 4, "text": "Why did we almost fail?"},
            {"start": 4, "end": 20, "text": "The problem was our acquisition strategy."},
            {"start": 20, "end": 32, "text": "We changed the model and reduced waste."},
            {"start": 32, "end": 48, "text": "Finally, our margins recovered because of the change."},
        ]
    }
    candidate = {"id": "c1", "start": 0, "end": 32, "text": "Why did we almost fail? The problem was our acquisition strategy. We changed the model and reduced waste."}
    result = adaptive_verify_context(candidate, transcript, initial_radius=6, expansion_step=12, max_radius=48, min_confidence=0.60, min_semantic_match=0.10)
    assert result.expansions >= 1
    assert result.final_radius > result.initial_radius
    assert result.semantic_payoff


def test_adaptive_context_reports_uncertainty_without_payoff() -> None:
    transcript = {
        "segments": [
            {"start": 0, "end": 6, "text": "Why did this happen?"},
            {"start": 6, "end": 22, "text": "We were unsure what to do next."},
            {"start": 22, "end": 40, "text": "The discussion continued without a conclusion."},
        ]
    }
    candidate = {"id": "c2", "start": 0, "end": 22, "text": "Why did this happen? We were unsure what to do next."}
    result = adaptive_verify_context(candidate, transcript, initial_radius=6, expansion_step=12, max_radius=24)
    assert result.uncertainty > 0
    assert result.stop_reason == "max_radius_reached"
