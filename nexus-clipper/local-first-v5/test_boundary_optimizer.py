from boundary_optimizer import optimize_boundaries, optimize_candidates


def _segments(start: float, end: float):
    return [{"start": start, "end": end, "text": "This is a complete sentence with enough words to represent a useful editorial boundary."}]


def test_optimizer_keeps_valid_candidate_and_records_evidence():
    candidate = {
        "id": "c1",
        "start": 100.0,
        "end": 145.0,
        "duration": 45.0,
        "text": "A complete thought.",
    }
    result = optimize_boundaries(candidate, segment_lookup=_segments, search_radius=2.0, step=1.0)
    assert result["boundary_optimization"]["status"] == "optimized"
    assert result["end"] > result["start"]
    assert result["duration"] >= 18.0
    assert result["boundary_optimization"]["selected"]["reasons"]


def test_optimizer_never_returns_negative_start():
    candidate = {"id": "c2", "start": 1.0, "end": 30.0, "duration": 29.0, "text": "enough words here"}
    result = optimize_boundaries(candidate, search_radius=8.0, step=2.0)
    assert result["start"] >= 0.0
    assert result["end"] > result["start"]


def test_batch_optimizer_is_deterministic_shape():
    candidates = [
        {"id": "a", "start": 50.0, "end": 90.0, "duration": 40.0, "text": "a"},
        {"id": "b", "start": 120.0, "end": 170.0, "duration": 50.0, "text": "b"},
    ]
    result = optimize_candidates(candidates, search_radius=1.0, step=1.0, limit=2)
    assert [item["id"] for item in result] == ["a", "b"]
    assert all("boundary_optimization" in item for item in result)
