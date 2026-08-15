from __future__ import annotations

import subprocess
from pathlib import Path

from vision_quality import detect_scene_changes, detect_face_subjects, inspect_render, media_stream_summary, visual_quality


def _fixture(path: Path) -> None:
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=black:size=640x360:rate=24",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
            "-t", "3", "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", str(path),
        ], capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr[-2000:]


def test_media_summary_reads_real_fixture(tmp_path: Path):
    source = tmp_path / "fixture.mp4"
    _fixture(source)
    info = media_stream_summary(source)
    assert info["width"] == 640
    assert info["height"] == 360
    assert info["audio_present"] is True
    assert info["duration"] > 2.5


def test_scene_detection_returns_real_time_ranges(tmp_path: Path):
    source = tmp_path / "fixture.mp4"
    _fixture(source)
    scenes = detect_scene_changes(source, 0, 3, sample_fps=2)
    assert scenes
    assert scenes[0]["start"] >= 0
    assert scenes[-1]["end"] <= 3.01
    assert all(item["end"] > item["start"] for item in scenes)


def test_subject_detection_is_media_driven(tmp_path: Path):
    source = tmp_path / "fixture.mp4"
    _fixture(source)
    observations = detect_face_subjects(source, 0, 3, sample_fps=2)
    assert isinstance(observations, list)
    assert all("timestamp" in item and "faces" in item for item in observations)


def test_visual_quality_flags_low_quality_fixture(tmp_path: Path):
    source = tmp_path / "fixture.mp4"
    _fixture(source)
    result = visual_quality(source, 0, 3, sample_fps=2)
    assert result["score"] < 100
    assert "low_resolution" in result["issues"]


def test_render_inspector_requires_audio_and_dimensions(tmp_path: Path):
    source = tmp_path / "fixture.mp4"
    _fixture(source)
    result = inspect_render(source, expected_width=640, expected_height=360, min_duration=2, max_duration=4)
    assert result["checks"]["resolution_check"]["passed"] is True
    assert result["checks"]["audio_check"]["passed"] is True
    assert result["verdict"] in {"APPROVED", "NEEDS_FIX"}
