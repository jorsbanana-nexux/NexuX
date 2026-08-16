from __future__ import annotations

import importlib
from pathlib import Path


def test_extracted_services_import_without_server() -> None:
    runtime = importlib.import_module("runtime_adapter")
    render = importlib.import_module("render_service")
    vision = importlib.import_module("vision_service")
    jobs = importlib.import_module("job_service")
    ingest = importlib.import_module("media_ingest")
    transcription = importlib.import_module("transcription_service")
    audio = importlib.import_module("audio_service")

    assert runtime.CanonicalRuntime is not None
    assert callable(render.render_with_spec)
    assert callable(vision.vision_service.scenes)
    assert callable(vision.vision_service.subjects)
    assert jobs.JobStateService is not None
    assert ingest.media_ingest is not None
    assert transcription.transcription_service is not None
    assert audio.audio_service is not None


def test_runtime_uses_extracted_service_owners() -> None:
    from audio_service import audio_service
    from render_service import render_with_spec
    from runtime_adapter import default_runtime
    from vision_service import vision_service
    from media_ingest import media_ingest
    from transcription_service import transcription_service

    runtime = default_runtime()
    assert runtime.render_with_spec is render_with_spec
    assert runtime.detect_scene_changes is vision_service.scenes
    assert runtime.detect_face_subjects is vision_service.subjects
    assert runtime.ingest_youtube == media_ingest.download_youtube
    assert runtime.probe_youtube == media_ingest.probe_youtube
    assert runtime.transcribe_local == transcription_service.transcribe
    assert runtime.analyze_audio == audio_service.analyze
    assert runtime.audio_signals == audio_service.signals
    assert isinstance(runtime.jobs_dir, Path)


def test_compatibility_server_exposes_same_canonical_render_and_vision() -> None:
    server = importlib.import_module("server")
    from render_service import render_with_spec
    from vision_service import vision_service

    assert server._render_with_spec is render_with_spec
    assert server.detect_scene_changes is vision_service.scenes
    assert server.detect_face_subjects is vision_service.subjects


def test_service_contracts_are_explicit() -> None:
    from media_ingest import IngestedMedia
    from audio_intelligence import AudioProfile

    assert IngestedMedia.__annotations__["source_type"] is str
    assert AudioProfile.__annotations__["duration"] is float
