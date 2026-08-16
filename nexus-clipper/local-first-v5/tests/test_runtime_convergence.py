from __future__ import annotations

import inspect

import canonical_api
from application_service import CanonicalApplicationService
from canonical_v6_pipeline import run_generation
from contracts import CompatJob, GenerateRequest
from runtime_adapter import CanonicalRuntime


def test_canonical_api_uses_application_service() -> None:
    assert isinstance(canonical_api.service, CanonicalApplicationService)
    assert canonical_api.app.title == "NexuX Local-First Canonical"


def test_pipeline_accepts_explicit_runtime_adapter() -> None:
    signature = inspect.signature(run_generation)
    assert "runtime" in signature.parameters
    assert signature.parameters["runtime"].default is None


def test_runtime_adapter_exposes_required_canonical_dependencies() -> None:
    runtime = canonical_api.runtime
    assert isinstance(runtime, CanonicalRuntime)
    for name in (
        "read_job",
        "write_job",
        "set_job",
        "ffprobe",
        "transcribe_local",
        "detect_scene_changes",
        "detect_face_subjects",
        "build_timeline",
        "render_with_spec",
    ):
        assert callable(getattr(runtime, name))


def test_contracts_are_single_source_for_request_and_job_models() -> None:
    import server

    assert server.GenerateRequest is GenerateRequest
    assert server.CompatJob is CompatJob
