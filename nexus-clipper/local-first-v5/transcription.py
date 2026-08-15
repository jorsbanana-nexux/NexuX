from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def transcribe(video: Path, language: str | None = None) -> dict[str, Any]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("faster-whisper belum terpasang") from exc

    device = os.getenv("WHISPER_DEVICE", "cpu")
    compute = os.getenv("WHISPER_COMPUTE", "int8" if device == "cpu" else "float16")
    model_name = os.getenv("WHISPER_MODEL", "small")
    model = WhisperModel(model_name, device=device, compute_type=compute)
    segments, info = model.transcribe(
        str(video),
        word_timestamps=True,
        vad_filter=True,
        language=language or None,
    )
    out: list[dict[str, Any]] = []
    for idx, seg in enumerate(segments):
        words = [
            {"word": w.word, "start": float(w.start), "end": float(w.end)}
            for w in (seg.words or [])
        ]
        out.append({
            "id": idx,
            "start": float(seg.start),
            "end": float(seg.end),
            "text": seg.text.strip(),
            "words": words,
        })
    return {"language": info.language, "segments": out}
