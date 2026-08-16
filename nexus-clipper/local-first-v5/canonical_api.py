from __future__ import annotations

import os
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from application_service import CanonicalApplicationService
from captions import PRESETS
from contracts import CompatJob, GenerateRequest
from publishing_analytics import aggregate_analytics, record_analytics_event
from runtime_adapter import CanonicalRuntime, default_runtime
from ui_contract import ANIMATIONS, ASPECT_RATIOS, POSITIONS
from vision_quality import inspect_render, media_stream_summary, tool_state, visual_quality

runtime: CanonicalRuntime = default_runtime()
service = CanonicalApplicationService(runtime)

app = FastAPI(title="NexuX Local-First Canonical", version="6.4.0", description="Canonical local-first clipping API with multimodal editorial intelligence. No B-roll.")
DEFAULT_ORIGINS = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
allowed_origins = [item.strip() for item in os.getenv("NEXUX_ALLOWED_ORIGINS", DEFAULT_ORIGINS).split(",") if item.strip()]
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins, allow_credentials=False, allow_methods=["GET", "POST", "DELETE", "OPTIONS"], allow_headers=["*"])
OUTPUTS = runtime.outputs_dir
JOBS = runtime.jobs_dir
ANALYTICS_ROOT = runtime.data_dir / "analytics"
app.mount("/output", StaticFiles(directory=str(OUTPUTS)), name="output")

@app.get("/")
async def root() -> dict[str, object]:
    return {"name":"NexuX Local-First Canonical","version":"6.4.0","canonical_runtime":True,"canonical_engine":"local-first-v5","broll":False,"multimodal_editorial":True,"prompt_clipping":True,"genre_intelligence":True,"virality_model":True,"cleanup":True,"dynamic_layouts":True,"voice_over":True,"critic_revision":True,"publishing_analytics":True,"ui_contract":"strict","analysis_world":"v2"}

@app.get("/api/health")
async def health() -> dict[str, object]:
    return {"status":"ok","canonical_runtime":True,"canonical_engine":"local-first-v5","runtime_module":"canonical_api","vision_scanner":"sequential","editorial_engine":"v6.4-multimodal","retrieval_strategy":"caption-first-targeted","ui_contract":"strict","multimodal_editorial":True,"prompt_clipping":True,"genre_intelligence":True,"virality_model":True,"filler_pause_editing":True,"dynamic_layouts":True,"voice_over":True,"critic_revision":True,"publishing_analytics":True,"analysis_world":"v2",**tool_state(),"whisper_model":os.getenv("WHISPER_MODEL","small")}

@app.get("/api/styles")
async def styles() -> dict[str, object]:
    return {"subtitle_styles":[{"id":key,"name":key.replace("_"," ").title(),"preview":{"font":value.get("font"),"font_size":value.get("size"),"animation":value.get("animation")}} for key,value in PRESETS.items()],"aspect_ratios":list(ASPECT_RATIOS),"animations":list(ANIMATIONS),"positions":list(POSITIONS),"broll":False}

@app.post("/api/generate", response_model=CompatJob)
async def generate(req: GenerateRequest, bg: BackgroundTasks) -> CompatJob:
    return service.enqueue(req, bg)

@app.get("/api/job/{job_id}", response_model=CompatJob)
async def job_status(job_id: str) -> CompatJob:
    return CompatJob(**service.read_job(job_id))

@app.get("/api/jobs")
async def jobs(status: str | None = None) -> dict[str, object]:
    return service.list_jobs(status)

@app.delete("/api/job/{job_id}")
async def cancel(job_id: str) -> dict[str, str]:
    return service.cancel(job_id)

@app.get("/api/analysis-world/{job_id}")
async def analysis_world(job_id: str) -> dict[str, object]:
    try:
        return service.get_analysis_world(job_id)
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@app.get("/api/vision/{job_id}")
async def vision(job_id: str) -> dict[str, object]:
    job = service.read_job(job_id)
    world = job.get("analysis_world")
    if isinstance(world, dict):
        try:
            persisted = service.get_analysis_world(job_id)
            return {"job_id":job_id,"analysis_world":persisted,"source":"persisted-analysis-world"}
        except (HTTPException, FileNotFoundError, ValueError):
            pass
    bundle = job.get("analysis_bundle")
    if isinstance(bundle, dict):
        return {"job_id":job_id,"analysis_bundle":bundle,"media":job.get("meta") or {},"source":"persisted-analysis-bundle"}
    video = Path(job.get("video_path", ""))
    if not video.exists():
        raise HTTPException(404, "Video artifact not found")
    media = media_stream_summary(video)
    duration = float(media.get("duration") or 0.0)
    return {"job_id":job_id,"media":media,"scenes":runtime.detect_scene_changes(video,0.0,duration or None),"subjects":runtime.detect_face_subjects(video,0.0,min(duration,600.0) if duration else None),"quality":visual_quality(video,0.0,min(duration,600.0) if duration else None),"source":"on-demand-fallback"}

@app.get("/api/download/{job_id}")
async def download(job_id: str) -> FileResponse:
    job = service.read_job(job_id)
    output = Path(job.get("output_path", ""))
    if not output.is_absolute(): output = OUTPUTS / output.name
    if not output.exists(): raise HTTPException(404, "Output not found")
    record_analytics_event(ANALYTICS_ROOT, job_id, {"event":"download"})
    return FileResponse(output, media_type="video/mp4", filename=output.name)

@app.get("/api/render-qa/{job_id}")
async def render_qa(job_id: str) -> dict[str, object]:
    job = service.read_job(job_id)
    output = Path(job.get("output_path", ""))
    if not output.is_absolute(): output = OUTPUTS / output.name
    if not output.exists(): raise HTTPException(404, "Output not found")
    return inspect_render(output)

@app.get("/api/critic/{job_id}")
async def critic_result(job_id: str) -> dict[str, object]:
    job = service.read_job(job_id)
    return {"job_id":job_id,"critique":job.get("critique") or {"revision_required":False,"issues":[]},"revision":job.get("revision") or {}}

@app.get("/api/publish/{job_id}")
async def publish_plan(job_id: str) -> dict[str, object]:
    job = service.read_job(job_id)
    plan = job.get("publish_plan")
    if not plan: raise HTTPException(404, "Publish plan not available")
    record_analytics_event(ANALYTICS_ROOT, job_id, {"event":"publish_plan_viewed"})
    return {"job_id":job_id,"publish_plan":plan}

@app.post("/api/publish/{job_id}/{platform}")
async def publish_event(job_id: str, platform: str) -> dict[str, object]:
    job = service.read_job(job_id)
    if job.get("status") != "completed": raise HTTPException(409, "Job is not completed")
    record_analytics_event(ANALYTICS_ROOT,job_id,{"event":"publish_requested","platform":platform})
    return {"job_id":job_id,"platform":platform,"status":"planned","note":"Publishing adapter records the destination; OAuth/platform credentials are required for live upload."}

@app.get("/api/analytics/{job_id}")
async def analytics(job_id: str) -> dict[str, object]:
    service.read_job(job_id)
    return aggregate_analytics(ANALYTICS_ROOT, job_id)
