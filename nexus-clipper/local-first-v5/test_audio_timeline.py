from __future__ import annotations

import subprocess
from pathlib import Path

from timeline import build_timeline


def _fixture(path: Path) -> None:
    result = subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=size=640x360:rate=24",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000",
        "-t", "3", "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(path)
    ], capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr[-1500:]


def test_timeline_persists_audio_profile(tmp_path: Path):
    source = tmp_path / "fixture.mp4"
    _fixture(source)
    timeline = build_timeline(source, {"segments": []}, {"start": 0.0, "end": 3.0})
    assert timeline.audio_profile is not None
    assert timeline.audio_profile["duration"] > 2.5
    payload = timeline.to_dict()
    assert "audio_profile" in payload
    assert payload["audio_profile"]["speech_ratio"] >= 0.0
