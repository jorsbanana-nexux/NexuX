from __future__ import annotations

import subprocess
from pathlib import Path

from audio_intelligence import analyze_audio, audio_signals


def _fixture(path: Path) -> None:
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000",
        "-af", "volume=0.2",
        "-t", "2",
        "-c:a", "aac", str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr[-1500:]


def test_audio_profile_reads_real_media(tmp_path: Path):
    source = tmp_path / "tone.m4a"
    _fixture(source)
    profile = analyze_audio(source, 0, 2)
    assert profile.duration > 1.9
    assert profile.speech_ratio > 0.9
    assert profile.silence_ratio < 0.1
    assert profile.peak_rms_db < 0


def test_audio_signals_are_bounded(tmp_path: Path):
    source = tmp_path / "tone.m4a"
    _fixture(source)
    signals = audio_signals(analyze_audio(source, 0, 2))
    assert all(0 <= value <= 100 for value in signals.values())
