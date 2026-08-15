from editorial_intelligence import generate_candidates, narrative_signals
from editorial_ranker import select_diverse


def _segments():
    return [
        {"start": i * 3.0, "end": (i + 1) * 3.0, "text": text}
        for i, text in enumerate([
            "Have you ever wondered why creators fail?",
            "The problem is they optimize for views instead of retention.",
            "But there is one mistake that makes it much worse.",
            "Actually, I discovered the reason after testing hundreds of clips.",
            "The answer is to build the payoff before the viewer leaves.",
            "That is why the opening must create a question immediately.",
            "In the end, the best clips resolve the promise they make.",
            "And that is the lesson most people miss.",
        ])
    ]


def test_narrative_signals_detect_story_markers():
    signals = narrative_signals(_segments())
    assert signals.question == 1.0
    assert signals.tension == 1.0
    assert signals.revelation == 1.0
    assert signals.payoff == 1.0


def test_generation_is_overlapping_and_strategy_aware():
    candidates = generate_candidates(_segments(), max_candidates=100)
    assert candidates
    assert all(18.0 <= c["duration"] <= 70.0 for c in candidates)
    assert any(c["generation_strategy"] == "narrative" for c in candidates)


def test_ranker_exposes_evidence_and_confidence():
    candidates = generate_candidates(_segments(), max_candidates=100)
    selected = select_diverse(candidates, limit=3)
    assert selected
    for candidate in selected:
        assert 0.0 <= candidate["editorial_evidence"]["confidence"] <= 1.0
        assert "narrative" in candidate["editorial_evidence"]
