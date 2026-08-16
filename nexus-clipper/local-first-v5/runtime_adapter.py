from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from audio_service import AudioIntelligenceService
from job_service import JobStateService
from media_ingest import IngestedMedia, MediaIngestService
from render_service import render_with_spec
from transcription_service import TranscriptionService
from vision_service import vision_service


@dataclass
class CanonicalRuntime:
    """Explicit dependency boundary for the canonical V5/V6 pipeline."""

    data_dir: Path
    jobs_dir: Path
    outputs_dir: Path
    cancel_flags: dict[str, bool]
    read_job: Callable[[str], dict[str, Any]]
    write_job: Callable[[dict[str, Any]], dict[str, Any]]
    set_job: Callable[..., dict[str, Any]]
    ffprobe: Callable[[Path], dict[str, Any]]
    ingest_youtube: Callable[[str, Path, int, str | None], IngestedMedia]
    probe_youtube: Callable[[str], IngestedMedia]
    transcribe_local: Callable[[Path, str | None], dict[str, Any]]
    analyze_audio: Callable[..., Any]
    audio_signals: Callable[[Any], dict[str, float]]
    detect_scene_changes: Callable[..., list[dict[str, Any]]]
    detect_face_subjects: Callable[..., list[dict[str, Any]]]
    build_timeline: Callable[..., Any]
    render_with_spec: Callable[..., dict[str, Any]]


def default_runtime() -> CanonicalRuntime:
    """Bind canonical runtime to extracted services and stable low-level primitives."""
    import app
    from engine_media import ffprobe
    from timeline import build_timeline

    jobs = JobStateService(app.JOBS)
    jobs.recover()
    ingest = MediaIngestService()
    transcription = TranscriptionService()
    audio = AudioIntelligenceService()

    return CanonicalRuntime(
        data_dir=app.DATA,
        jobs_dir=app.JOBS,
        outputs_dir=app.OUTPUTS,
        cancel_flags=jobs.cancel_flags,
        read_job=jobs.read,
        write_job=jobs.write,
        set_job=jobs.set,
        ffprobe=ffprobe,
        ingest_youtube=ingest.download_youtube,
        probe_youtube=ingest.probe_youtube,
        transcribe_local=transcription.transcribe,
        analyze_audio=audio.analyze,
        audio_signals=audio.signals,
        detect_scene_changes=vision_service.scenes,
        detect_face_subjects=vision_service.subjects,
        build_timeline=build_timeline,
        render_with_spec=render_with_spec,
    )
