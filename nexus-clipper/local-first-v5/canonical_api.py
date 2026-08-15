from __future__ import annotations

import json
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import server as engine
from caption_runtime import render_ass_safe
from sequential_vision import detect_face_subjects, detect_scene_changes, visual_quality
from server import CompatJob, GenerateRequest
from vision_quality import inspect_render, media_stream_summary, tool_state

# Canonical runtime adapters. The compatibility runner remains an internal implementation detail.
engine.detect_scene_changes = detect_scene_changes
engine.detect_face_subjects = detect_face_subjects
engine.visual_quality = visual_quality
engine.render_ass = render_ass_safe

app = FastAPI(
    title="NexuX Local-First V5",
    version="5.9.0",
    description="Canonical local-first clipping API. No B-roll. One public runtime surface.",
)

OUTPUTS = engine.OUTPUTS
JOBS = engine.JOBS
app.mount("/output", StaticFiles(directory=str(OUTPUTS)), name="output")


def _read(job_id: str) -> dict:
    return engine._read(job_id)


def _write(job: dict) -> None:
    engine._write(job)


@app.get("/")
async def root() -> dict:
    return {"name": "NexuX Local-First V5", "version": "5.9.0", "canonical_runtime": True, "broll": False}


@app.get("/api/health")
async def health() -> dict:
    return {
        "status": "ok",
        "canonical_runtime": True,
        "broll": False,
        "runtime_module": "canonical_api",
        "vision_scanner": "sequential",
        "caption_boundary_remap": True,
        **tool_state(),
        "whisper_model": engine.WHISPER_MODEL,
    }


@app.get("/api/styles")
async def styles() -> dict:
    return {
        "subtitle_styles": [
            {"id": key, "name": key.replace("_", " ").title(), "preview": {"font": value.get("font"), "font_size": value.get("size"), "animation": value.get("animation")}}
            for key, value in engine.PRESETS.items()
        ],
        "aspect_ratios": ["9:16", "1:1", "16:9", "4:5", "2:3", "21:9"],
        "broll": False,
    }


@app.post("/api/generate", response_model=CompatJob)
async def generate(req: GenerateRequest, bg: BackgroundTasks) -> CompatJob:
    job_id = uuid.uuid4().hex
    job = {"job_id": job_id, "status": "queued", "progress": 0.0, "stage": "queued", "output_path": None, "error": None, "clips": [], "broll": False, "render_meta": []}
    _write(job)
    engine.CANCEL_FLAGS[job_id] = False
    bg.add_task(engine._run_generation, job_id, req)
    return CompatJob(**job)


@app.get("/api/job/{job_id}", response_model=CompatJob)
async def job_status(job_id: str) -> CompatJob:
    return CompatJob(**_read(job_id))


@app.get("/api/jobs")
async def jobs(status: str | None = None) -> dict:
    items: list[dict] = []
    for path in JOBS.glob("*.json"):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if status and item.get("status") != status:
            continue
        items.append(CompatJob(**item).model_dump())
    items.sort(key=lambda item: item.get("job_id", ""), reverse=True)
    return {"total": len(items), "jobs": items}


@app.delete("/api/job/{job_id}")
async def cancel(job_id: str) -> dict:
    job = _read(job_id)
    if job.get("status") in {"completed", "failed", "cancelled"}:
        raise HTTPException(400, f"Job already {job['status']}")
    engine.CANCEL_FLAGS[job_id] = True
    engine._set(job, status="cancelled", stage="cancelled", error="Cancelled by user")
    return {"job_id": job_id, "status": "cancelled"}


@app.get("/api/vision/{job_id}")
async def vision(job_id: str) -> dict:
    job = _read(job_id)
    video = Path(job.get("video_path", ""))
    if not video.exists():
        raise HTTPException(404, "Video artifact not found")
    media = media_stream_summary(video)
    duration = float(media.get("duration") or 0.0)
    return {"job_id": job_id, "media": media, "scenes": detect_scene_changes(video, 0.0, duration or None), "subjects": detect_face_subjects(video, 0.0, duration or None), "quality": visual_quality(video, 0.0, duration or None)}


@app.get("/api/download/{job_id}")
async def download(job_id: str):
    job = _read(job_id)
    output = Path(job.get("output_path", ""))
    if not output.is_absolute():
        output = OUTPUTS / output.name
    if not output.exists():
        raise HTTPException(404, "Output not found")
    return FileResponse(output, media_type="video/mp4", filename=output.name)


@app.get("/api/render-qa/{job_id}")
async def render_qa(job_id: str) -> dict:
    job = _read(job_id)
    output = Path(job.get("output_path", ""))
    if not output.is_absolute():
        output = OUTPUTS / output.name
    if not output.exists():
        raise HTTPException(404, "Output not found")
    return inspect_render(output)
