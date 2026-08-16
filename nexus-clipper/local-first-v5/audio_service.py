from __future__ import annotations

from pathlib import Path
from typing import Any

from audio_intelligence import AudioProfile, analyze_audio, audio_signals


class AudioIntelligenceService:
    """Canonical ownership of audio analysis and editorial audio features."""

    def analyze(
        self,
        media: Path,
        start: float,
        end: float,
        *,
        speech_segments: list[dict[str, Any]] | None = None,
    ) -> AudioProfile:
        return analyze_audio(media, start, end, speech_segments=speech_segments)

    def signals(self, profile: AudioProfile) -> dict[str, float]:
        return audio_signals(profile)

    def analyze_with_signals(
        self,
        media: Path,
        start: float,
        end: float,
        *,
        speech_segments: list[dict[str, Any]] | None = None,
    ) -> tuple[AudioProfile, dict[str, float]]:
        profile = self.analyze(media, start, end, speech_segments=speech_segments)
        return profile, self.signals(profile)


audio_service = AudioIntelligenceService()
