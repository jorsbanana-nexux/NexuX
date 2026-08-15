from __future__ import annotations

import asyncio
import json
import shutil
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import (
    app,
    DATA,
    JOBS,
    OUTPUTS,
    build_candidates,
    ffprobe,
    editorial_metadata,
    to_dict,
    sample_faces,
    SubjectObservation,
    build_camera_path,
    path_to_dict,
    transcribe_local,
    download_youtube,
)
from captions import PRESETS, render_ass
from compositor import build_final_filter, run_ffmpeg, spec_for_aspect_ratio
from timeline import build_timeline, ffmpeg_filter_for_timeline


router = APIRouter(prefix="/api")
CANCEL_FLAGS: dict[str, bool] = {}


class GenerateRequest(BaseModel):
    youtube_url: str = Field(..., min_length=10, max_length=2000)
    target_duration: int = Field(60, ge=15, le=300)
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


def _job_path(job_id: str) -> Path:
    if not job_id or not all(c in "0123456789abcdef" for c in job_id) or len(job_id) != 32:
        raise HTTPException(422, "Invalid job_id")
    return JOBS / f"{job_id}.json"


def _read(job_id: str) -> dict[str, Any]:
    path = _job_path(job_id)
    if not path.exists():
        raise HTTPException(404, "Job not found")
    return json.loads(path.read_text(encoding="utf-8"))


def _write(job: dict[str, Any]) -> None:
    _job_path(job["job_id"]).write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")


def _set(job: dict[str, Any], **updates: Any) -> dict[str, Any]:
    job.update(updates)
    _write(job)
    return job


def _relative_output(path: Path) -> str:
    return f"/output/{path.name}"


def _hex_to_ass(value: str, fallback: str) -> str:
    candidate = value.strip() if isinstance(value, str) else ""
    if len(candidate) != 7 or not candidate.startswith("#"):
        candidate = fallback
    rgb = candidate[1:]
    r, g, b = rgb[0:2], rgb[2:4], rgb[4:6]
    return f"&H00{b}{g}{r}".upper()


def _style_overrides(req: GenerateRequest) -> dict[str, Any]:
    return {
        "font": req.font,
        "size": req.font_size,
        "primary": _hex_to_ass(req.primary_color, "#FFFFFF"),
        "highlight": _hex_to_ass(req.highlight_color, "#FFD700"),
        "outline": _hex_to_ass(req.stroke_color, "#000000"),
        "outline_width": req.stroke_width,
        "position": req.position,
        "animation": req.animation,
    }


def _render_with_spec(video: Path, job: dict[str, Any], clip: dict[str, Any], output: Path, timeline: Any, req: GenerateRequest) -> dict[str, Any]:
    spec = spec_for_aspect_ratio(req.aspect_ratio)
    ass = output.with_suffix(".ass")
    editorial = editorial_metadata(clip["text"], emoji_enabled=req.emoji_enabled)
    style = PRESETS.get(req.subtitle_style, PRESETS["hormozi"])
    selected_animation = req.animation or style.get("animation", "pop")
    overrides = {**_style_overrides(req), "animation": selected_animation}
    render_ass(
        job["transcript"], timeline, ass,
        preset=req.subtitle_style if req.subtitle_style in PRESETS else "hormozi",
        font=req.font,
        headline=editorial.headline,
        emoji=editorial.emoji,
        canvas_w=spec.width,
        canvas_h=spec.height,
        overrides=overrides,
    )
    media = job.get("meta") or ffprobe(video)
    video_stream = next((s for s in media.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video_stream:
        raise RuntimeError("Video stream dimensions unavailable")
    source_w, source_h = int(video_stream["width"]), int(video_stream["height"])

    camera_points: list[Any] = []
    if req.face_tracking and req.auto_zoom:
        observations = sample_faces(video, float(clip["start"]), float(clip["end"]), sample_fps=3.0)
        mapped: list[SubjectObservation] = []
        for obs in observations:
            output_time = timeline.source_to_output(obs.time)
            if output_time is not None:
                mapped.append(SubjectObservation(output_time, obs.x, obs.y, obs.w, obs.h, obs.confidence, obs.kind))
        camera_points = build_camera_path(mapped)

    edl_graph = ffmpeg_filter_for_timeline(timeline)[0]
    filter_complex = build_final_filter(edl_graph, camera_points, ass, source_w, source_h, spec)
    run_ffmpeg(video, output, filter_complex, spec=spec)
    return {
        "editorial": to_dict(editorial),
        "caption_preset": req.subtitle_style,
        "caption_animation": selected_animation,
        "camera": {"enabled": bool(req.face_tracking and req.auto_zoom), "points": path_to_dict(camera_points), "point_count": len(camera_points)},
        "source_dimensions": {"width": source_w, "height": source_h},
        "output_dimensions": {"width": spec.width, "height": spec.height},
        "broll": False,
    }


async def _run_generation(job_id: str, req: GenerateRequest) -> None:
    job = _read(job_id)
    try:
        CANCEL_FLAGS[job_id] = False
        _set(job, status="processing", stage="downloading", progress=5)
        job_dir = DATA / "uploads" / job_id
        video, meta = await asyncio.to_thread(download_youtube, req.youtube_url, job_dir, 1080)
        media = ffprobe(video)
        _set(job, stage="transcribing", progress=25, video_path=str(video), meta=media)
        if CANCEL_FLAGS.get(job_id):
            _set(job, status="cancelled", stage="cancelled")
            return

        transcript = await asyncio.to_thread(transcribe_local, video)
        _set(job, stage="analyzing", progress=55, transcript=transcript)
        if CANCEL_FLAGS.get(job_id):
            _set(job, status="cancelled", stage="cancelled")
            return

        candidates = build_candidates(transcript["segments"])
        # Keep the canonical heuristic score, but bias selection toward the user's requested duration.
        target = float(req.target_duration)
        candidates.sort(key=lambda c: (float(c.get("viral_score", 0)) - abs(float(c.get("duration", target)) - target) * 0.35), reverse=True)
        candidates = candidates[: req.clip_count]
        if not candidates:
            raise RuntimeError("No viable 20-60 second candidates found")
        _set(job, stage="rendering", progress=70, candidates=candidates, selected_candidate_id=candidates[0]["id"])

        rendered: list[str] = []
        render_meta: list[dict[str, Any]] = []
        for idx, candidate in enumerate(candidates):
            if CANCEL_FLAGS.get(job_id):
                _set(job, status="cancelled", stage="cancelled")
                return
            timeline = await asyncio.to_thread(build_timeline, video, transcript, candidate)
            output = OUTPUTS / f"{job_id}_clip_{idx + 1:02d}.mp4"
            info = await asyncio.to_thread(_render_with_spec, video, {**job, "transcript": transcript, "meta": media}, candidate, output, timeline, req)
            rendered.append(_relative_output(output))
            render_meta.append({"candidate_id": candidate["id"], "timeline": timeline.to_dict(), "render": info})
            _set(job, progress=70 + int(25 * (idx + 1) / len(candidates)), stage=f"rendering {idx + 1}/{len(candidates)}")

        _set(job, status="completed", stage="completed", progress=100, output_path=rendered[0], clips=rendered, render_meta=render_meta, broll=False)
    except Exception as exc:
        _set(job, status="failed", stage="failed", error=str(exc))
    finally:
        CANCEL_FLAGS.pop(job_id, None)


@router.post("/generate", response_model=CompatJob)
async def generate(req: GenerateRequest, bg: BackgroundTasks):
    job_id = uuid.uuid4().hex
    job = {"job_id": job_id, "status": "queued", "progress": 0.0, "stage": "queued", "output_path": None, "error": None, "clips": [], "broll": False}
    _write(job)
    bg.add_task(_run_generation, job_id, req)
    return CompatJob(**job)


@router.get("/job/{job_id}", response_model=CompatJob)
async def job_status(job_id: str):
    return CompatJob(**_read(job_id))


@router.get("/jobs")
async def jobs(status: str | None = None):
    items = []
    for path in JOBS.glob("*.json"):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if status and item.get("status") != status:
            continue
        items.append(CompatJob(**item).model_dump())
    items.sort(key=lambda x: x.get("job_id", ""), reverse=True)
    return {"total": len(items), "jobs": items}


@router.delete("/job/{job_id}")
async def cancel(job_id: str):
    job = _read(job_id)
    if job.get("status") in {"completed", "failed", "cancelled"}:
        raise HTTPException(400, f"Job already {job['status']}")
    CANCEL_FLAGS[job_id] = True
    _set(job, status="cancelled", stage="cancelled")
    return {"job_id": job_id, "status": "cancelled"}


@router.get("/health")
async def compat_health():
    return {
        "status": "ok",
        "broll": False,
        "canonical_engine": "local-first-v5",
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "ffprobe": shutil.which("ffprobe") is not None,
        "yt_dlp": shutil.which("yt-dlp") is not None,
    }


@router.get("/styles")
async def styles():
    # Return exactly the presets the renderer accepts. This keeps UI and engine contracts aligned.
    ids = [
        "hormozi", "mrbeast", "aliabdaal", "minimalist", "gaming", "cinematic", "neon",
        "typewriter", "tiktok_viral", "documentary", "comedy", "horror", "motivational", "educational", "custom",
        "karaoke", "pop_line", "deep_diver",
    ]
    return {
        "subtitle_styles": [
            {"id": key, "name": key.replace("_", " ").title(), "preview": {"font": PRESETS[key]["font"], "font_size": PRESETS[key]["size"], "animation": PRESETS[key]["animation"]}}
            for key in ids
        ],
        "aspect_ratios": ["9:16", "1:1", "16:9", "4:5", "2:3", "21:9"],
        "color_grades": ["none"],
        "video_codecs": ["h264"],
        "audio_codecs": ["aac"],
        "broll": False,
    }


@router.get("/download/{job_id}")
async def compat_download(job_id: str):
    job = _read(job_id)
    output = Path(job.get("output_path", "")).name
    path = OUTPUTS / output
    if not path.exists():
        raise HTTPException(404, "Output not found")
    return FileResponse(path, media_type="video/mp4", filename=path.name)


app.mount("/output", StaticFiles(directory=str(OUTPUTS)), name="canonical-output")
app.include_router(router)
