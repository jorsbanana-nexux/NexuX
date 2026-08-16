from __future__ import annotations

from pathlib import Path
from typing import Any

from transcription import transcribe


class TranscriptionService:
    """Canonical transcription boundary over the existing local Whisper implementation."""

    def transcribe(self, media: Path, language: str | None = None) -> dict[str, Any]:
        result = transcribe(media, language=language)
        if not isinstance(result, dict) or "segments" not in result:
            raise RuntimeError("Transcription backend returned an invalid transcript contract")
        result.setdefault("source", "local-whisper")
        result.setdefault("language", language)
        return result


transcription_service = TranscriptionService()
