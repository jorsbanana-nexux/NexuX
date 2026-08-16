from editorial_rejudge import rejudge_candidate


def test_rejudge_keeps_strong_candidate():
    candidate = {
        "id": "strong",
        "start": 10.0,
        "end": 45.0,
        "editorial_signals": {
            "hook": 0.9,
            "context": 0.9,
            "payoff": 0.9,
            "coherence": 0.9,
        },
        "score": 0.9,
    }
    result = rejudge_candidate(candidate)
    assert result["rejudge"]["selected"] == "original"


def test_rejudge_records_refinement_decision():
    candidate = {
        "id": "weak",
        "start": 10.0,
        "end": 30.0,
        "editorial_signals": {
            "hook": 0.2,
            "context": 0.2,
            "payoff": 0.2,
            "coherence": 0.8,
        },
        "score": 0.2,
    }
    result = rejudge_candidate(candidate)
    assert result["rejudge"]["selected"] in {"original", "refined"}
    assert "critic" in result["rejudge"]
