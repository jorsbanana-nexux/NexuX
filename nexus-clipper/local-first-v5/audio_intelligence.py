from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class AudioProfile:
    duration: float
    speech_duration: float
    silence_duration: float
    speech_ratio: float
    avg_rms_db: float
    peak_rms_db: float
    energy_variance: float
    speech_density: float
    rhythm_score: float
    filler_count: int
    filler_ratio: float
    silence_ratio: float

    def to_dict(self) -> dict[str, float | int]:
        return {k: round(v, 4) if isinstance(v, float) else v for k, v in asdict(self).items()}


FILLERS = {
    "um", "uh", "hmm", "hm", "eee", "aaa", "eh", "anu", "kayak", "like",
    "you know", "youknow", "actually", "basically", "maksud saya", "gitu", "jadi", "nah",
}


def _db(rms: float) -> float:
    return 20.0 * float(np.log10(max(rms, 1e-8)))


def _decode_mono(video: Path, start: float, end: float, sample_rate: int = 16000) -> np.ndarray:
    duration = max(0.0, end - start)
    if duration <= 0:
        return np.empty(0, dtype=np.float32)
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{start:.3f}",
        "-i", str(video), "-t", f"{duration:.3f}", "-vn", "-ac", "1",
        "-ar", str(sample_rate), "-f", "f32le", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=900)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode("utf-8", errors="ignore")[-1500:] or "Audio decode failed")
    return np.frombuffer(result.stdout, dtype=np.float32)


def _envelope(samples: np.ndarray, sample_rate: int, window_ms: float = 50.0) -> np.ndarray:
    window = max(1, int(sample_rate * window_ms / 1000.0))
    count = len(samples) // window
    if count <= 0:
        return np.empty(0, dtype=np.float32)
    frames = samples[: count * window].reshape(count, window)
    return np.sqrt(np.mean(np.square(frames), axis=1) + 1e-12)


def analyze_audio(
    video: Path,
    start: float,
    end: float,
    *,
    silence_db: float = -36.0,
    frame_ms: float = 50.0,
    speech_segments: list[dict[str, Any]] | None = None,
) -> AudioProfile:
    samples = _decode_mono(video, start, end)
    duration = max(0.0, end - start)
    env = _envelope(samples, 16000, frame_ms)
    if env.size == 0:
        return AudioProfile(duration, 0.0, duration, 0.0, -80.0, -80.0, 0.0, 0.0, 0.0, 0, 0.0, 1.0)

    db = 20.0 * np.log10(np.maximum(env, 1e-8))
    active = db >= silence_db
    silence_ratio = float(1.0 - active.mean())
    speech_duration = duration * float(active.mean())
    silence_duration = max(0.0, duration - speech_duration)
    avg_rms_db = _db(float(np.sqrt(np.mean(np.square(samples)) + 1e-12)))
    peak_rms_db = float(np.max(db))
    energy_variance = float(np.var(db))

    density = 0.0
    filler_count = 0
    if speech_segments:
        total_words = 0
        for segment in speech_segments:
            if float(segment.get("end", 0)) < start or float(segment.get("start", 0)) > end:
                continue
            for word in segment.get("words", []) or []:
                ws = float(word.get("start", 0))
                we = float(word.get("end", 0))
                if we < start or ws > end:
                    continue
                total_words += 1
                norm = re.sub(r"[^\w']+", "", str(word.get("word", "")).casefold())
                if norm in FILLERS:
                    filler_count += 1
        density = total_words / max(duration, 1e-6)

    filler_ratio = filler_count / max(1, int(round(density * max(speech_duration, 1e-6))))
    pause_balance = max(0.0, 1.0 - abs(silence_ratio - 0.18) / 0.35)
    energy_balance = max(0.0, 1.0 - abs(min(1.0, energy_variance / 250.0) - 0.45) / 0.55)
    rhythm_score = max(0.0, min(100.0, 100.0 * (0.65 * pause_balance + 0.35 * energy_balance)))

    return AudioProfile(
        duration=duration,
        speech_duration=speech_duration,
        silence_duration=silence_duration,
        speech_ratio=1.0 - silence_ratio,
        avg_rms_db=avg_rms_db,
        peak_rms_db=peak_rms_db,
        energy_variance=energy_variance,
        speech_density=density,
        rhythm_score=rhythm_score,
        filler_count=filler_count,
        filler_ratio=min(1.0, filler_ratio),
        silence_ratio=silence_ratio,
    )


def audio_signals(profile: AudioProfile) -> dict[str, float]:
    speech = min(100.0, profile.speech_density * 3.2)
    rhythm = profile.rhythm_score
    clarity = max(0.0, 100.0 - profile.filler_ratio * 100.0)
    pause_penalty = min(100.0, profile.silence_ratio * 100.0)
    energy = max(0.0, min(100.0, 50.0 + profile.energy_variance * 0.35))
    return {
        "speech_density": round(speech, 3),
        "rhythm": round(rhythm, 3),
        "clarity": round(clarity, 3),
        "pause_penalty": round(pause_penalty, 3),
        "energy": round(energy, 3),
    }
