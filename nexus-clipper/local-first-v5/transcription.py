from __future__ import annotations

import json
import os
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Any

from process_supervisor import run as supervised_run

_MODEL_CACHE: dict[tuple[str, str, str], Any] = {}
_MODEL_LOCK = threading.Lock()


def _model() -> Any:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("faster-whisper belum terpasang") from exc
    device = os.getenv("WHISPER_DEVICE", "cpu")
    compute = os.getenv("WHISPER_COMPUTE", "int8" if device == "cpu" else "float16")
    model_name = os.getenv("WHISPER_MODEL", "small")
    key = (model_name, device, compute)
    with _MODEL_LOCK:
        model = _MODEL_CACHE.get(key)
        if model is None:
            model = WhisperModel(model_name, device=device, compute_type=compute)
            _MODEL_CACHE[key] = model
        return model


def _probe_duration(video: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(video)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1200:] or "Unable to read media duration")
    try:
        return max(0.0, float(result.stdout.strip()))
    except ValueError as exc:
        raise RuntimeError("FFprobe returned invalid media duration") from exc


def _chunk_audio(video: Path, start: float, duration: float, target: Path) -> None:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{start:.3f}", "-i", str(video), "-t", f"{duration:.3f}", "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(target)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=max(900, int(duration * 4)))
    if result.returncode != 0 or not target.exists() or target.stat().st_size == 0:
        raise RuntimeError(result.stderr[-1500:] or "Unable to extract transcription chunk")


def _transcribe_file(model: Any, media: Path, language: str | None, offset: float, id_start: int) -> tuple[list[dict[str, Any]], str | None]:
    segments, info = model.transcribe(str(media), word_timestamps=True, vad_filter=True, language=language or None)
    out: list[dict[str, Any]] = []
    for idx, seg in enumerate(segments, id_start):
        words = [{"word": w.word, "start": float(w.start) + offset, "end": float(w.end) + offset} for w in (seg.words or [])]
        out.append({"id": idx, "start": float(seg.start) + offset, "end": float(seg.end) + offset, "text": seg.text.strip(), "words": words})
    return out, getattr(info, "language", None)


def transcribe(video: Path, language: str | None = None) -> dict[str, Any]:
    duration = _probe_duration(video)
    chunk_seconds = max(300, min(1800, int(os.getenv("WHISPER_CHUNK_SECONDS", "900"))))
    model = _model()
    all_segments: list[dict[str, Any]] = []
    detected_language: str | None = language
    with tempfile.TemporaryDirectory(prefix="nexus-whisper-") as tmp:
        tmp_root = Path(tmp)
        start = 0.0
        next_id = 0
        while start < duration:
            length = min(float(chunk_seconds), duration - start)
            chunk = tmp_root / f"chunk-{next_id:06d}.wav"
            _chunk_audio(video, start, length, chunk)
            segments, detected = _transcribe_file(model, chunk, language, start, next_id)
            if detected_language is None and detected:
                detected_language = detected
            next_id += len(segments)
            all_segments.extend(segments)
            start += length
    return {"language": detected_language, "segments": all_segments}


def transcribe_external(video: Path, language: str | None = None, *, job_id: str | None = None) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile(prefix="nexus-transcript-", suffix=".json", delete=False) as handle:
        output = Path(handle.name)
    try:
        cmd = ["python", "transcription_worker.py", "--input", str(video), "--output", str(output)]
        if language:
            cmd.extend(["--language", language])
        key = f"transcribe:{job_id or video.parent.name}"
        result = supervised_run(cmd, key=key, timeout=int(os.getenv("WHISPER_PROCESS_TIMEOUT_SECONDS", "21600")))
        if result.returncode != 0:
            raise RuntimeError(result.stderr[-2500:] or "Whisper worker failed")
        if not output.exists():
            raise RuntimeError("Whisper worker produced no transcript")
        return json.loads(output.read_text(encoding="utf-8"))
    finally:
        output.unlink(missing_ok=True)
