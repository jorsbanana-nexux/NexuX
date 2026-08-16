from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app import (
    app,
    DATA,
    JOBS,
    OUTPUTS,
    build_candidates,
    download_youtube,
    rerank_candidates,
    transcribe_local,
)
from contracts import CompatJob, GenerateRequest
from engine_media import ffprobe
from job_service import JobStateService
from publishing_analytics import aggregate_analytics, record_analytics_event
from render_service import render_with_spec
from runtime_adapter import CanonicalRuntime, default_runtime
from timeline import build_timeline
from vision_quality import visual_quality
from vision_service import vision_service
from fastapi import BackgroundTasks


router = APIRouter(prefix="/api")
runtime: CanonicalRuntime = default_runtime()
service = __import__("application_service").application_service.CanonicalApplicationService(runtime)
job_state = JobStateService(JOBS)

# Compatibility exports. Canonical code should import the owning service instead.
CANCEL_FLAGS = runtime.cancel_flags
_read = runtime.read_job
_write = runtime.write_job
_set = runtime.set_job
_render_with_spec = render_with_spec
detect_scene_changes = vision_service.scenes
detect_face_subjects = vision_service.subjects


def _relative_output(path: Path) -> str:
    return f"/output/{path.name}"


async def _run_generation(job_id: str, req: GenerateRequest) -> None:
    """Compatibility runner delegating to the canonical pipeline."""
    from canonical_v6_pipeline import run_generation

    await run_generation(job_id, req, runtime)


@router.post("/generate", response_model=CompatJob)
async def generate(req: GenerateRequest, bg: BackgroundTasks) -> CompatJob:
    return service.enqueue(req, bg)


@router.get("/job/{job_id}", response_model=CompatJob)
async def job_status(job_id: str) -> CompatJob:
    return CompatJob(**runtime.read_job(job_id))


@router.get("/jobs")
async def jobs(status: str | None = None) -> dict[str, object]:
    items = [CompatJob(**item).model_dump() for item in job_state.list(status)]
    return {"total": len(items), "jobs": items}


@router.delete("/job/{job_id}")
async def cancel(job_id: str) -> dict[str, str]:
    return service.cancel(job_id)


@router.get("/vision/{job_id}")
async def vision(job_id: str) -> dict[str, object]:
    job = runtime.read_job(job_id)
    bundle = job.get("analysis_bundle")
    if isinstance(bundle, dict):
        return {
            "job_id": job_id,
            "analysis_bundle": bundle,
            "media": job.get("meta") or {},
            "source": "persisted-analysis-bundle",
        }
    video = Path(job.get("video_path", ""))
    if not video.exists():
        raise HTTPException(404, "Video artifact not found")
    media = ffprobe(video)
    duration = float(media.get("format", {}).get("duration") or 0.0)
    return {
        "job_id": job_id,
        "media": media,
        "scenes": vision_service.scenes(video, 0.0, duration or None),
        "subjects": vision_service.subjects(video, 0.0, min(duration, 600.0) if duration else None),
        "quality": visual_quality(video, 0.0, min(duration, 600.0) if duration else None),
        "source": "on-demand-fallback",
    }


@router.get("/download/{job_id}")
async def download(job_id: str) -> FileResponse:
    job = runtime.read_job(job_id)
    output = Path(job.get("output_path", ""))
    if not output.is_absolute():
        output = OUTPUTS / output.name
    if not output.exists():
        raise HTTPException(404, "Output not found")
    record_analytics_event(runtime.data_dir / "analytics", job_id, {"event": "download"})
    return FileResponse(output, media_type="video/mp4", filename=output.name)


@router.get("/render-qa/{job_id}")
async def render_qa(job_id: str) -> dict[str, object]:
    from vision_quality import inspect_render

    job = runtime.read_job(job_id)
    output = Path(job.get("output_path", ""))
    if not output.is_absolute():
        output = OUTPUTS / output.name
    if not output.exists():
        raise HTTPException(404, "Output not found")
    return inspect_render(output)


@router.get("/analytics/{job_id}")
async def analytics(job_id: str) -> dict[str, object]:
    runtime.read_job(job_id)
    return aggregate_analytics(runtime.data_dir / "analytics", job_id)


app.include_router(router)
