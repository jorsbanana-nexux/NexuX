from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field

import server as engine
from advanced_render import render_with_spec as advanced_render_with_spec
from canonical_v6_pipeline import run_generation as run_v6_generation
from publishing_analytics import aggregate_analytics, record_analytics_event
from sequential_vision import detect_face_subjects, detect_scene_changes, visual_quality
from server import CompatJob, GenerateRequest
from ui_contract import ASPECT_RATIOS, ANIMATIONS, POSITIONS, canonicalize_fronted_values
from ui_contract_validation import validate_generate_request
from vision_quality import inspect_render, media_stream_summary, tool_state

engine.detect_scene_changes = detect_scene_changes
engine.detect_face_subjects = detect_face_subjects
engine.visual_quality = visual_quality
engine._run_generation = run_v6_generation
engine._render_with_spec = advanced_render_with_spec


class AdvancedGenerateRequest(GenerateRequest):
    clip_prompt: str | None = Field(default=None, max_length=500)
    genre: str = Field(default="auto", max_length=40)
    remove_fillers_pauses: bool = True
    pause_threshold: float = Field(default=0.42, ge=0.20, le=2.0)
    voice_over: bool = False
    voice_over_text: str | None = Field(default=None, max_length=1200)
    voice_style: str = Field(default="male_narrator", max_length=40)
    publish_platforms: list[str] | None = None


app = FastAPI(
    title="NexuX Local-First Canonical",
    version="6.4.0",
    description="Canonical local-first clipping API with multimodal editorial intelligence. No B-roll.",
)

DEFAULT_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
allowed_origins = [item.strip() for item in os.getenv("NEXUX_ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",") if item.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=False, allow_methods=["GET", "POST", "DELETE", "OPTIONS"], allow_headers=["*"])

OUTPUTS = engine.OUTPUTS
JOBS = engine.JOBS
ANALYTICS_ROOT = engine.DATA / "analytics"
app.mount("/output", StaticFiles(directory=str(OUTPUTS)), name="output")


def _read(job_id: str) -> dict:
    return engine._read(job_id)


def _write(job: dict) -> None:
    engine._write(job)


@app.get("/")
async def root() -> dict:
    return {"name":"NexuX Local-First Canonical","version":"6.4.0","canonical_runtime":True,"canonical_engine":"local-first-v5","broll":False,"multimodal_editorial":True,"prompt_clipping":True,"genre_intelligence":True,"virality_model":True,"cleanup":True,"dynamic_layouts":True,"voice_over":True,"critic_revision":True,"publishing_analytics":True,"ui_contract":"strict"}


@app.get("/api/health")
async def health() -> dict:
    return {"status":"ok","canonical_runtime":True,"canonical_engine":"local-first-v5","broll":False,"runtime_module":"canonical_api","vision_scanner":"sequential","editorial_engine":"v6.4-multimodal","retrieval_strategy":"caption-first-targeted","ui_contract":"strict","fronted_alias_mapping":True,"multimodal_editorial":True,"prompt_clipping":True,"genre_intelligence":True,"virality_model":True,"filler_pause_editing":True,"dynamic_layouts":True,"voice_over":True,"critic_revision":True,"publishing_analytics":True,**tool_state(),"whisper_model":os.getenv("WHISPER_MODEL","small")}


@app.get("/api/styles")
async def styles() -> dict:
    return {"subtitle_styles":[{"id":key,"name":key.replace("_"," ").title(),"preview":{"font":value.get("font"),"font_size":value.get("size"),"animation":value.get("animation")}} for key,value in engine.PRESETS.items()],"aspect_ratios":list(ASPECT_RATIOS),"animations":list(ANIMATIONS),"positions":list(POSITIONS),"broll":False}


@app.post("/api/generate", response_model=CompatJob)
async def generate(req: AdvancedGenerateRequest, bg: BackgroundTasks) -> CompatJob:
    req.subtitle_style, req.animation = canonicalize_fronted_values(req.subtitle_style, req.animation)
    validate_generate_request(req)
    job_id = uuid.uuid4().hex
    job = {"job_id":job_id,"status":"queued","progress":0.0,"stage":"queued","output_path":None,"error":None,"clips":[],"broll":False,"render_meta":[],"analysis_bundle":None,"revision":0,"critic":None,"publish_plan":None,"editorial_decision":None}
    _write(job)
    engine.CANCEL_FLAGS[job_id] = False
    bg.add_task(engine._run_generation, job_id, req)
    record_analytics_event(ANALYTICS_ROOT, job_id, {"event":"generation_queued","clip_count":req.clip_count,"aspect_ratio":req.aspect_ratio,"genre":req.genre,"prompt":bool(req.clip_prompt),"voice_over":req.voice_over})
    return CompatJob(**job)


@app.get("/api/job/{job_id}", response_model=CompatJob)
async def job_status(job_id: str) -> CompatJob:
    return CompatJob(**_read(job_id))


@app.get("/api/jobs")
async def jobs(status: str | None = None) -> dict:
    items=[]
    for path in JOBS.glob("*.json"):
        try:
            item=json.loads(path.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError):
            continue
        if status and item.get("status") != status:
            continue
        items.append(CompatJob(**item).model_dump())
    items.sort(key=lambda item:item.get("job_id",""), reverse=True)
    return {"total":len(items),"jobs":items}


@app.delete("/api/job/{job_id}")
async def cancel(job_id: str) -> dict:
    job=_read(job_id)
    if job.get("status") in {"completed","failed","cancelled"}:
        raise HTTPException(400,f"Job already {job['status']}")
    engine.CANCEL_FLAGS[job_id]=True
    engine._set(job,status="cancelled",stage="cancelled",error="Cancelled by user")
    record_analytics_event(ANALYTICS_ROOT, job_id, {"event":"generation_cancelled"})
    return {"job_id":job_id,"status":"cancelled"}


@app.get("/api/vision/{job_id}")
async def vision(job_id: str) -> dict:
    job=_read(job_id)
    bundle=job.get("analysis_bundle")
    if isinstance(bundle,dict):
        return {"job_id":job_id,"analysis_bundle":bundle,"media":job.get("meta") or {},"source":"persisted-analysis-bundle"}
    video=Path(job.get("video_path", ""))
    if not video.exists():
        raise HTTPException(404,"Video artifact not found")
    media=media_stream_summary(video)
    duration=float(media.get("duration") or 0.0)
    return {"job_id":job_id,"media":media,"scenes":detect_scene_changes(video,0.0,duration or None),"subjects":detect_face_subjects(video,0.0,min(duration,600.0) if duration else None),"quality":visual_quality(video,0.0,min(duration,600.0) if duration else None),"source":"on-demand-fallback"}


@app.get("/api/download/{job_id}")
async def download(job_id: str):
    job=_read(job_id)
    output=Path(job.get("output_path", ""))
    if not output.is_absolute():
        output=OUTPUTS/output.name
    if not output.exists():
        raise HTTPException(404,"Output not found")
    record_analytics_event(ANALYTICS_ROOT, job_id, {"event":"download"})
    return FileResponse(output,media_type="video/mp4",filename=output.name)


@app.get("/api/render-qa/{job_id}")
async def render_qa(job_id: str) -> dict:
    job=_read(job_id)
    output=Path(job.get("output_path", ""))
    if not output.is_absolute():
        output=OUTPUTS/output.name
    if not output.exists():
        raise HTTPException(404,"Output not found")
    return inspect_render(output)


@app.get("/api/critic/{job_id}")
async def critic_result(job_id: str) -> dict:
    job=_read(job_id)
    return {"job_id":job_id,"critique":job.get("critique") or {"revision_required":False,"issues":[]},"revision":job.get("revision") or {}}


@app.get("/api/publish/{job_id}")
async def publish_plan(job_id: str) -> dict:
    job=_read(job_id)
    plan=job.get("publish_plan")
    if not plan:
        raise HTTPException(404,"Publish plan not available")
    record_analytics_event(ANALYTICS_ROOT, job_id, {"event":"publish_plan_viewed"})
    return {"job_id":job_id,"publish_plan":plan}


@app.post("/api/publish/{job_id}/{platform}")
async def publish_event(job_id: str, platform: str) -> dict:
    job=_read(job_id)
    if job.get("status") != "completed":
        raise HTTPException(409,"Job is not completed")
    event={"event":"publish_requested","platform":platform}
    record_analytics_event(ANALYTICS_ROOT,job_id,event)
    return {"job_id":job_id,"platform":platform,"status":"planned","note":"Publishing adapter records the destination; OAuth/platform credentials are required for live upload."}


@app.get("/api/analytics/{job_id}")
async def analytics(job_id: str) -> dict:
    _read(job_id)
    return aggregate_analytics(ANALYTICS_ROOT, job_id)
