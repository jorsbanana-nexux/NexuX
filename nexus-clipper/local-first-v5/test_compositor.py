from __future__ import annotations

import subprocess
from pathlib import Path

from compositor import CompositionSpec, build_final_filter, camera_crop_expressions, run_ffmpeg
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


def test_real_ffmpeg_compositor(tmp_path: Path) -> None:
    source = tmp_path / "fixture.mp4"
    output = tmp_path / "final.mp4"
    ass = tmp_path / "caption.ass"
    fixture = subprocess.run(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", "3",
            "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", str(source),
        ], capture_output=True, text=True, timeout=120,
    )
    assert fixture.returncode == 0, fixture.stderr[-2000:]

    render_ass(
        {"segments": [{"start": 0, "end": 3, "words": [{"word": "NexuX", "start": 0, "end": 3}]}]},
        None, ass, headline="NEXUX LOCAL-FIRST", emoji=["🔥"],
    )
    graph = (
        "[0:v]trim=start=0:end=1,setpts=PTS-STARTPTS[v0];"
        "[0:v]trim=start=1.5:end=3,setpts=PTS-STARTPTS[v1];"
        "[0:a]atrim=start=0:end=1,asetpts=PTS-STARTPTS[a0];"
        "[0:a]atrim=start=1.5:end=3,asetpts=PTS-STARTPTS[a1];"
        "[v0][a0][v1][a1]concat=n=2:v=1:a=1[vout][aout]"
    )
    points = [CameraPoint(0.0, 0.50, 0.50, 0.75, 1.0, 1.0), CameraPoint(2.0, 0.58, 0.48, 0.75, 1.0, 1.0)]
    final_filter = build_final_filter(graph, points, ass, 1280, 720, CompositionSpec())
    run_ffmpeg(source, output, final_filter)
    assert output.exists() and output.stat().st_size > 10_000

    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height", "-of", "default=noprint_wrappers=1", str(output)],
        capture_output=True, text=True, timeout=60,
    )
    assert probe.returncode == 0, probe.stderr
    assert "codec_type=video" in probe.stdout
    assert "codec_type=audio" in probe.stdout
    assert "width=1080" in probe.stdout
    assert "height=1920" in probe.stdout
