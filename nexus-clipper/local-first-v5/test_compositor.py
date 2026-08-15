from __future__ import annotations

from pathlib import Path

from compositor import camera_crop_expressions
from captions import render_ass
from timeline import EditTimeline, KeepRange
from virtual_camera import CameraPoint


def test_camera_expression_contains_time_segments() -> None:
    points = [
        CameraPoint(0.0, 0.50, 0.50, 0.60, 1.0, 1.0),
        CameraPoint(2.0, 0.60, 0.48, 0.60, 1.0, 1.0),
    ]
    crop_w, crop_h, x, y = camera_crop_expressions(points, 1920, 1080)
    assert int(crop_w) > 0
    assert int(crop_h) > 0
    assert "if(lt(t," in x
    assert "if(lt(t," in y


def test_single_range_labels_are_normalized() -> None:
    timeline = EditTimeline(0.0, 10.0, 10.0, 10.0, (), (KeepRange(0.0, 10.0, 0.0, 10.0),))
    from timeline import ffmpeg_filter_for_timeline
    graph, _ = ffmpeg_filter_for_timeline(timeline)
    assert "[vout]" in graph
    assert "[aout]" in graph


def test_caption_contains_headline_and_emoji(tmp_path: Path) -> None:
    transcript = {
        "segments": [{
            "start": 0.0,
            "end": 1.0,
            "text": "Ini rahasia bisnis",
            "words": [
                {"word": "Ini", "start": 0.0, "end": 0.3},
                {"word": "rahasia", "start": 0.3, "end": 0.7},
                {"word": "bisnis", "start": 0.7, "end": 1.0},
            ],
        }]
    }
    out = tmp_path / "caption.ass"
    render_ass(transcript, None, out, headline="3 RAHASIA BISNIS", emoji=["🔥"])
    text = out.read_text(encoding="utf-8")
    assert "3 RAHASIA BISNIS" in text
    assert "🔥" in text
