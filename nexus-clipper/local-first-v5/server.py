from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from analysis_bundle import build_analysis_bundle
from app import (
    JOBS,
    OUTPUTS,
    app,
    build_candidates,
    build_timeline,
    detect_scene_changes,
    download_youtube,
    ffprobe,
    render,
    rerank_candidates,
    transcribe_local,
)
from caption_runtime import render_ass_safe
from captions import PRESETS
from job_store import read as atomic_read, recover_interrupted, update as atomic_update
from process_supervisor import terminate as terminate_process


class GenerateRequest(BaseModel):
    youtube_url: str = Field(..., min_length=10, max_length=2000)
    target_duration: int = Field(45, ge=20, le=60)
    aspect_ratio: str = Field("9:16")
    subtitle_style: str = Field("hormozi")
    font: str = Field("Arial", max_length=160)
    font_size: int = Field(48, ge=20, le=96)
    primary_color: str = Field("#FFFFFF", pattern=r"^#[0-9A-Fa-f]{6}$")
    highlight_color: str = Field("#FFD700", pattern=r"^#[0-9A-Fa-f]{6}$")
    stroke_color: str = Field("#000000", pattern=r"^#[0-9A-Fa-f]{6}$")
    stroke_width: int = Field(3, ge=1, le=12)
    position: str = Field("center", pattern=r"^(top|center|bottom)$")
    animation: str = Field("pop", max_length=32)
    auto_zoom: bool = True
    face_tracking: bool = True
    clip_count: int = Field(3, ge=1, le=10)
    language: str | None = Field(None, max_length=20)
    normalize_audio: bool = True
    emoji_enabled: bool = False


class CompatJob(BaseModel):
    job_id: str
    status: str
    progress: float = 0.0
    stage: str = "queued"
    output_path: str | None = None
    error: str | None = None
    clips: list[str] = Field(default_factory=list)
    broll: bool = False
    render_meta: list[dict[str, Any]] = Field(default_factory=list)
    analysis_bundle: dict[str, Any] | None = None


def _read(job_id: str) -> dict[str, Any]:
    if not job_id or not all(c in "0123456789abcdef" for c in job_id) or len(job_id) != 32:
        raise HTTPException(422, "Invalid job_id")
    path = JOBS / f"{job_id}.json"
    if not path.exists():
        raise HTTPException(404, "Job not found")
    return atomic_read(JOBS, job_id)


def _write(job: dict[str, Any]) -> dict[str, Any]:
    return atomic_update(JOBS, job)


def _set(job: dict[str, Any], **updates: Any) -> dict[str, Any]:
    current = atomic_update(JOBS, job, **updates)
    job.clear()
    job.update(current)
    return job


def _relative_output(path: Path) -> str:
    return f"/output/{path.name}"


class CancellationRegistry(dict[str, bool]):
    def __setitem__(self, job_id: str, value: bool) -> None:
        super().__setitem__(job_id, value)
        if value:
            terminate_process(f"download:{job_id}")
            terminate_process(f"transcribe:{job_id}")
            terminate_process(f"render:{job_id}")


CANCEL_FLAGS = CancellationRegistry()


def _render_candidate(video: Path, job: dict[str, Any], candidate: dict[str, Any], output: Path, req: GenerateRequest) -> dict[str, Any]:
    timeline = build_timeline(video, job["transcript"], candidate)
    info = render(
        video,
        job,
        candidate,
        output,
        timeline,
        req.subtitle_style if req.subtitle_style in PRESETS else "hormozi",
        req.font,
        req.emoji_enabled,
        bool(req.face_tracking and req.auto_zoom),
    )
    return {"timeline": timeline.to_dict(), "render": info}


async def _run_generation(job_id: str, req: GenerateRequest) -> None:
    job = _read(job_id)
    try:
        CANCEL_FLAGS.setdefault(job_id, False)
        if CANCEL_FLAGS.get(job_id):
            return
        _set(job, status="processing", stage="downloading", progress=5)
        job_dir = Path(job["job_dir"])
        video, meta = await asyncio.to_thread(download_youtube, req.youtube_url, job_dir, 1080, job_id)
        media = ffprobe(video)
        _set(job, stage="transcribing", progress=25, video_path=str(video), meta=media)
        if CANCEL_FLAGS.get(job_id):
            _set(job, status="cancelled", stage="cancelled")
            return
        transcript = await asyncio.to_thread(transcribe_local, video, req.language)
        _set(job, stage="analyzing", progress=45, transcript=transcript)
        candidates = build_candidates(transcript["segments"])
        if not candidates:
            raise RuntimeError("No viable 20-60 second candidates found")
        duration = float(media.get("format", {}).get("duration") or 0.0)
        scenes = await asyncio.to_thread(detect_scene_changes, video, 0.0, duration or None)
        ranked = await asyncio.to_thread(
            rerank_candidates,
            candidates,
            scenes,
            float(req.target_duration),
            min(20, max(req.clip_count * 4, 10)),
            video,
            transcript,
        )
        ranked.sort(key=lambda item: float(item.get("editorial_rank", item.get("viral_score", 0.0))), reverse=True)
        selected = ranked[: req.clip_count]
        bundle = build_analysis_bundle(transcript, selected, scenes, [])
        _set(
            job,
            stage="rendering",
            progress=65,
            candidates=selected,
            selected_candidate_id=selected[0]["id"],
            analysis_bundle=bundle.to_dict(),
            vision={"scene_count": len(scenes), "scenes": scenes},
        )
        rendered: list[str] = []
        render_meta: list[dict[str, Any]] = []
        for index, candidate in enumerate(selected, 1):
            if CANCEL_FLAGS.get(job_id):
                _set(job, status="cancelled", stage="cancelled")
                return
            output = OUTPUTS / f"{job_id}_clip_{index:02d}.mp4"
            result = await asyncio.to_thread(_render_candidate, video, {**job, "transcript": transcript, "meta": media}, candidate, output, req)
            rendered.append(_relative_output(output))
            render_meta.append({
                "candidate_id": candidate["id"],
                "editorial_rank": candidate.get("editorial_rank", candidate.get("viral_score")),
                "editorial_signals": candidate.get("editorial_signals"),
                "audio_profile": candidate.get("audio_profile"),
                **result,
            })
            _set(job, progress=65 + int(30 * index / len(selected)), stage=f"rendering {index}/{len(selected)}", render_meta=render_meta)
        if not rendered:
            raise RuntimeError("No clips were rendered")
        _set(job, status="completed", stage="completed", progress=100, output_path=rendered[0], clips=rendered, broll=False, render_meta=render_meta)
    except Exception as exc:
        if CANCEL_FLAGS.get(job_id):
            _set(job, status="cancelled", stage="cancelled", error="Job cancelled")
        else:
            _set(job, status="failed", stage="failed", error=str(exc))
    finally:
        CANCEL_FLAGS.pop(job_id, None)


@app.post("/api/generate", response_model=CompatJob)
async def generate(req: GenerateRequest, bg: BackgroundTasks) -> CompatJob:
    job_id = uuid.uuid4().hex
    job = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0.0,
        "stage": "queued",
        "output_path": None,
        "error": None,
        "clips": [],
        "broll": False,
        "render_meta": [],
        "analysis_bundle": None,
        "job_dir": str(Path(JOBS).parent / "uploads" / job_id),
        "revision": 0,
    }
    _write(job)
    CANCEL_FLAGS[job_id] = False
    bg.add_task(_run_generation, job_id, req)
    return CompatJob(**job)


@app.get("/api/job/{job_id}", response_model=CompatJob)
async def job_status(job_id: str) -> CompatJob:
    return CompatJob(**_read(job_id))


@app.get("/api/jobs")
async def jobs(status: str | None = None) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
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
async def cancel(job_id: str) -> dict[str, str]:
    job = _read(job_id)
    if job.get("status") in {"completed", "failed", "cancelled"}:
        raise HTTPException(400, f"Job already {job['status']}")
    CANCEL_FLAGS[job_id] = True
    _set(job, status="cancelled", stage="cancelled", error="Job cancelled by user")
    return {"job_id": job_id, "status": "cancelled"}


@app.on_event("startup")
def _recover_jobs() -> None:
    recovered = recover_interrupted(JOBS)
    if recovered:
        print(f"NexuX recovery: marked {recovered} interrupted job(s) after process restart")


# Compatibility export used by canonical_api.
render_ass = render_ass_safe
