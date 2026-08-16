from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass
class CanonicalRuntime:
    """Explicit dependency boundary for the canonical V5/V6 pipeline.

    The adapter intentionally bridges to existing implementations during migration.
    New canonical code should depend on this contract rather than importing server.py.
    """

    data_dir: Path
    jobs_dir: Path
    outputs_dir: Path
    cancel_flags: dict[str, bool]
    read_job: Callable[[str], dict[str, Any]]
    write_job: Callable[[dict[str, Any]], dict[str, Any]]
    set_job: Callable[..., dict[str, Any]]
    ffprobe: Callable[[Path], dict[str, Any]]
    transcribe_local: Callable[[Path, str | None], dict[str, Any]]
    detect_scene_changes: Callable[..., list[dict[str, Any]]]
    detect_face_subjects: Callable[..., list[dict[str, Any]]]
    build_timeline: Callable[..., Any]
    render_with_spec: Callable[..., dict[str, Any]]


def default_runtime() -> CanonicalRuntime:
    """Compatibility bridge used until legacy orchestration is fully extracted."""
    import server

    return CanonicalRuntime(
        data_dir=server.DATA,
        jobs_dir=server.JOBS,
        outputs_dir=server.OUTPUTS,
        cancel_flags=server.CANCEL_FLAGS,
        read_job=server._read,
        write_job=server._write,
        set_job=server._set,
        ffprobe=server.ffprobe,
        transcribe_local=server.transcribe_local,
        detect_scene_changes=server.detect_scene_changes,
        detect_face_subjects=server.detect_face_subjects,
        build_timeline=server.build_timeline,
        render_with_spec=server._render_with_spec,
    )
