from editorial_ranker import rank_candidate, select_diverse


def _candidate(start, text, hook=80, payoff=0.8, context=0.8):
    return {
        "id": f"c{start}",
        "start": float(start),
        "end": float(start + 40),
        "duration": 40.0,
        "text": text,
        "scores": {"hook": hook},
        "editorial": {
            "semantic": {
                "payoff_strength": payoff,
                "context_completeness": context,
                "standalone_quality": 0.85,
                "specificity": 0.7,
                "novelty_proxy": 0.75,
                "topic_coherence": 0.85,
            }
        },
    }


def test_ranker_rewards_payoff_and_boundary_alignment():
    candidate = _candidate(20, "Here is the setup. Here is the result.", hook=70, payoff=0.95)
    signals = rank_candidate(
        candidate,
        target_duration=40,
        scene_boundaries=[{"start": 20, "end": 60}],
    )
    assert signals.payoff > 90
    assert signals.boundary_alignment > 90
    assert signals.total > 70


def test_selection_penalizes_repetition_and_keeps_diverse_candidates():
    candidates = [
        _candidate(0, "same story same result same context"),
        _candidate(50, "same story same result same context"),
        _candidate(110, "different topic with a distinct conclusion"),
    ]
    selected = select_diverse(candidates, limit=3, target_duration=40)
    assert len(selected) == 3
    assert selected[0]["editorial_rank"] >= selected[1]["editorial_rank"] or selected[0]["editorial_signals"]["diversity"] >= 90
    assert any("different topic" in item["text"] for item in selected)


def test_ranker_is_transparent():
    candidate = _candidate(0, "A useful explanation with a concrete result.")
    signals = rank_candidate(candidate, target_duration=45)
    report = signals.to_dict()
    required = {"hook", "payoff", "context", "standalone", "pacing", "boundary_alignment", "diversity", "repetition_penalty", "total"}
    assert required.issubset(report)
