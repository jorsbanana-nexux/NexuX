from pathlib import Path

from multimodal_editorial import apply_editorial_intelligence, critic, detect_filler_segments, dynamic_layout_plan, parse_prompt, score_virality
from publishing_analytics import aggregate_analytics, build_publish_plan, record_analytics_event


def test_prompt_and_genre_drive_editorial_metadata():
    candidates = [{"id":"c1","text":"The founder explains the biggest mistake and why it changed everything.","editorial_rank":70,"editorial_signals":{"hook":80,"payoff":75,"standalone":80,"novelty":70,"pacing":80}}]
    terms = parse_prompt("find the biggest mistake")
    assert "biggest" in terms and "mistake" in terms
    enriched, decision = apply_editorial_intelligence(candidates, prompt="find the biggest mistake", genre="education")
    assert decision.genre == "education"
    assert enriched[0]["prompt_relevance"] > 0
    assert 0 <= enriched[0]["virality_score"] <= 100
    assert score_virality(enriched[0], prompt_terms=terms, genre=decision.genre) >= 0


def test_cleanup_and_dynamic_layout_are_deterministic():
    cuts = detect_filler_segments([{"start":0,"end":1,"text":"um this is important"},{"start":2,"end":3,"text":"the answer"}], min_pause=0.5)
    assert any(item["reason"] == "filler" for item in cuts)
    assert any(item["reason"] == "pause" for item in cuts)
    layout = dynamic_layout_plan(aspect_ratio="9:16", genre="gaming", face_tracking=True, auto_zoom=True)
    assert layout["layout"] == "kinetic"


def test_critic_and_publish_analytics(tmp_path: Path):
    report = critic([{"clip_id":"c1","quality":{"verdict":"APPROVED","score":95},"output_dimensions":{"width":1080,"height":1920}}], requested_duration=45, expected_aspect="9:16")
    assert report["revision_required"] is False
    plan = build_publish_plan("job1", {"text":"A useful creator lesson about retention"})
    assert plan["targets"]
    record_analytics_event(tmp_path, "job1", {"event":"test"})
    assert aggregate_analytics(tmp_path, "job1")["event_count"] == 1
