"""
Nexus-Clipper V6.4 — FastAPI Backend (Production)
===================================================
Canonical API matching the frontend V6.4 contract.

Fixes from V4 → V6.4:
- All 14 API endpoints the frontend expects
- GenerateRequest with V6 advanced fields
- JobResponse with render_meta, analysis_bundle, critique, broll
- CORS locked to known origins (no wildcard + credentials)
- Binds to 127.0.0.1 (local-first, not exposed to network)
- target_duration range corrected to 20-60 (canonical)
- Job store enriched with editorial/vision/critique data
- Health endpoint reports canonical_runtime + broll
- Download endpoint with proper streaming
- Vision, Render QA, Critic, Publish, Analytics endpoints
"""
import os, json, time, asyncio, uuid
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import (
    FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks,
    HTTPException, Request,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from urllib.parse import quote

from engine import (
    run_pipeline, get_video_info, search_youtube,
    STYLE_PRESETS, ASPECT_RATIOS, COLOR_GRADES,
    OUTPUT_DIR,
)
from engine.constants import MAX_CONCURRENT_JOBS

# ── Logger ──
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
log = logging.getLogger("nexus.api")

# ── Pydantic Models ──

class GenerateRequest(BaseModel):
    youtube_url: str = Field(..., min_length=10, max_length=500)
    target_duration: int = Field(45, ge=20, le=60)
    aspect_ratio: str = Field("9:16")
    subtitle_style: str = Field("hormozi")
    font: str = Field("Arial")
    font_size: int = Field(48, ge=20, le=80)
    primary_color: str = Field("#FFFFFF")
    highlight_color: str = Field("#FFD700")
    stroke_color: str = Field("#000000")
    stroke_width: int = Field(3, ge=1, le=10)
    position: str = Field("center")
    animation: str = Field("pop")
    auto_zoom: bool = Field(True)
    face_tracking: bool = Field(True)
    scene_detection: bool = Field(True)
    screen_detection: bool = Field(False)
    diarization: bool = Field(True)
    clip_count: int = Field(3, ge=1, le=10)
    language: Optional[str] = None
    color_grade: str = Field("none")
    video_codec: str = Field("h264")
    audio_codec: str = Field("aac")
    ai_scoring: bool = Field(False)
    normalize_audio: bool = Field(True)
    webhook_url: Optional[str] = None
    # V6 advanced fields
    emoji_enabled: bool = Field(True)
    clip_prompt: Optional[str] = None
    genre: Optional[str] = None
    remove_fillers_pauses: bool = Field(False)
    pause_threshold: float = Field(0.5, ge=0.1, le=2.0)
    voice_over: bool = Field(False)
    voice_over_text: Optional[str] = None
    voice_style: Optional[str] = None
    publish_platforms: Optional[List[str]] = None

class JobResponse(BaseModel):
    job_id: str
    status: str
    progress: float = 0.0
    stage: str = "queued"
    output_path: Optional[str] = None
    error: Optional[str] = None
    created_at: str = ""
    clips: List[str] = []
    # V6.4 fields
    broll: bool = False
    render_meta: List[Dict[str, Any]] = []
    analysis_bundle: Optional[Dict[str, Any]] = None
    critique: Optional[Dict[str, Any]] = None
    revision: Optional[Dict[str, Any]] = None
    publish_plan: Optional[Dict[str, Any]] = None
    editorial_decision: Optional[Dict[str, Any]] = None

class PreviewResponse(BaseModel):
    status: str
    video: dict

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=200)
    max_results: int = Field(10, ge=1, le=50)

# ── WebSocket Manager ──

class WSManager:
    def __init__(self):
        self._clients: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._clients.append(ws)

    async def disconnect(self, ws: WebSocket):
        async with self._lock:
            self._clients = [c for c in self._clients if c != ws]

    async def broadcast(self, data: dict):
        async with self._lock:
            snap = list(self._clients)
        dead = []
        for ws in snap:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        if dead:
            async with self._lock:
                for ws in dead:
                    if ws in self._clients:
                        self._clients.remove(ws)

    @property
    def count(self) -> int:
        return len(self._clients)

ws = WSManager()

# ── Job Store ──
# In-memory store enriched with V6.4 editorial data.
# Each job dict carries: status, progress, stage, clips, render_meta,
# analysis_bundle, critique, revision, publish_plan, editorial_decision.

jobs: Dict[str, dict] = {}
cancel_flags: Dict[str, bool] = {}
active_count = 0

def _new_job(jid: str) -> dict:
    """Create a fresh job dict with all V6.4 fields."""
    return {
        "job_id": jid,
        "status": "queued",
        "progress": 0.0,
        "stage": "queued",
        "output_path": None,
        "error": None,
        "clips": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "broll": False,
        "render_meta": [],
        "analysis_bundle": None,
        "critique": None,
        "revision": None,
        "publish_plan": None,
        "editorial_decision": None,
        # Internal fields (not in JobResponse, used by pipeline)
        "_stages": {},
        "_critiques": [],
    }

# ── App ──

ALLOWED_ORIGINS = os.environ.get(
    "NEXUX_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Nexus-Clipper V6.4 starting (local-first, no B-roll)...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    yield
    log.info("Shutting down...")

app = FastAPI(
    title="NexuX Local-First Canonical",
    version="6.4.0",
    description="Autonomous AI Video Repurposing Engine — Local-First, Zero Cloud Cost",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for rendered output
odir = OUTPUT_DIR if isinstance(OUTPUT_DIR, Path) else Path(str(OUTPUT_DIR))
odir.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(odir.absolute())), name="output")

# ── Helper: safe job → JobResponse ──

def _job_to_response(j: dict) -> JobResponse:
    """Convert internal job dict to JobResponse, stripping private fields."""
    public = {k: v for k, v in j.items() if not k.startswith("_")}
    # Ensure render_meta is a list
    if public.get("render_meta") is None:
        public["render_meta"] = []
    return JobResponse(**public)

# ── Routes ──

@app.get("/")
async def root():
    return {
        "name": "NexuX",
        "version": "6.4.0",
        "status": "operational",
        "canonical_runtime": True,
        "broll": False,
        "active_jobs": active_count,
        "total_jobs": len(jobs),
        "ws_clients": ws.count,
    }

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "canonical_runtime": True,
        "canonical_engine": "local-first-v6.4",
        "broll": False,
        "active_jobs": active_count,
        "queued_jobs": len([j for j in jobs.values() if j["status"] == "queued"]),
        "ws_clients": ws.count,
        "timestamp": time.time(),
    }

@app.get("/api/styles")
async def get_styles():
    return {
        "subtitle_styles": [
            {
                "id": k,
                "name": k.replace("_", " ").title(),
                "preview": {
                    "font": v.get("font", "Arial"),
                    "font_size": v.get("font_size", 48),
                    "primary": v.get("primary", "#FFF"),
                    "highlight": v.get("highlight", "#FFD700"),
                    "animation": v.get("animation", "pop"),
                }
            }
            for k, v in STYLE_PRESETS.items()
        ],
        "aspect_ratios": list(ASPECT_RATIOS.keys()),
        "animations": ["pop", "pop_fast", "bounce", "fade", "slide", "typewriter"],
        "positions": ["top", "center", "bottom", "random"],
        "color_grades": list(COLOR_GRADES.keys()),
        "video_codecs": ["h264", "h265"],
        "audio_codecs": ["aac", "mp3", "opus"],
        "broll": False,
    }

@app.post("/api/preview")
async def preview(url: str):
    try:
        info = get_video_info(url)
        return PreviewResponse(status="ok", video=info)
    except Exception as e:
        raise HTTPException(400, f"Preview failed: {e}")

@app.post("/api/search")
async def search(req: SearchRequest):
    try:
        results = search_youtube(req.query, req.max_results)
        return {"status": "ok", "results": results, "total": len(results)}
    except Exception as e:
        raise HTTPException(400, f"Search failed: {e}")

@app.post("/api/generate", response_model=JobResponse)
async def generate(req: GenerateRequest, bg: BackgroundTasks):
    global active_count

    if active_count >= MAX_CONCURRENT_JOBS:
        raise HTTPException(
            429,
            f"Max {MAX_CONCURRENT_JOBS} concurrent jobs. Try again shortly."
        )

    jid = f"nx-{uuid.uuid4().hex}"
    job = _new_job(jid)
    jobs[jid] = job
    cancel_flags[jid] = False
    active_count += 1

    style_kwargs = {
        "subtitle_style": req.subtitle_style,
        "font": req.font,
        "font_size": req.font_size,
        "primary_color": req.primary_color,
        "highlight_color": req.highlight_color,
        "stroke_color": req.stroke_color,
        "stroke_width": req.stroke_width,
        "position": req.position,
        "animation": req.animation,
        "aspect_ratio": req.aspect_ratio,
        "target_duration": req.target_duration,
        "clip_count": req.clip_count,
        "auto_zoom": req.auto_zoom,
        "face_tracking": req.face_tracking,
        "scene_detection": req.scene_detection,
        "screen_detection": req.screen_detection,
        "diarization": req.diarization,
        "language": req.language,
        "color_grade": req.color_grade,
        "video_codec": req.video_codec,
        "audio_codec": req.audio_codec,
        "ai_scoring": req.ai_scoring,
        "normalize_audio": req.normalize_audio,
        "emoji_enabled": req.emoji_enabled,
        "clip_prompt": req.clip_prompt,
        "genre": req.genre,
        "remove_fillers_pauses": req.remove_fillers_pauses,
        "pause_threshold": req.pause_threshold,
        "voice_over": req.voice_over,
        "voice_over_text": req.voice_over_text,
        "voice_style": req.voice_style,
        "publish_platforms": req.publish_platforms,
    }

    bg.add_task(_process_job, jid, req.youtube_url, style_kwargs)
    log.info(f"Job {jid} queued: {req.youtube_url[:80]}")

    return _job_to_response(job)

@app.get("/api/job/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    j = jobs.get(job_id)
    if not j:
        raise HTTPException(404, f"Job {job_id} not found")
    return _job_to_response(j)

@app.get("/api/jobs")
async def list_jobs(status: Optional[str] = None):
    filtered = jobs
    if status:
        filtered = {k: v for k, v in jobs.items() if v["status"] == status}
    return {
        "total": len(filtered),
        "jobs": [_job_to_response(v) for v in filtered.values()],
    }

@app.delete("/api/job/{job_id}")
async def cancel_job(job_id: str):
    global active_count
    j = jobs.get(job_id)
    if not j:
        raise HTTPException(404, f"Job {job_id} not found")
    if j["status"] in ("completed", "failed", "cancelled"):
        raise HTTPException(400, f"Job already {j['status']}")
    cancel_flags[job_id] = True
    j["status"] = "cancelled"
    active_count = max(0, active_count - 1)
    await ws.broadcast({"type": "job_cancelled", "job_id": job_id})
    return {"job_id": job_id, "status": "cancelled"}

# ── V6.4 Advanced Endpoints ──

@app.get("/api/vision/{job_id}")
async def get_vision(job_id: str):
    """Return vision analysis bundle for a job."""
    j = jobs.get(job_id)
    if not j:
        raise HTTPException(404, f"Job {job_id} not found")
    stages = j.get("_stages", {})
    return {
        "job_id": job_id,
        "analysis_bundle": j.get("analysis_bundle"),
        "media": stages.get("vision", {}),
        "scenes": stages.get("vision", {}).get("scene_changes", []),
        "subjects": stages.get("vision", {}).get("face_samples", []),
        "quality": stages.get("vision", {}).get("quality", {}),
        "source": j.get("_stages", {}).get("download", {}).get("path"),
    }

@app.get("/api/render-qa/{job_id}")
async def get_render_qa(job_id: str):
    """Return render quality assurance data for a job."""
    j = jobs.get(job_id)
    if not j:
        raise HTTPException(404, f"Job {job_id} not found")
    stages = j.get("_stages", {})
    critiques = j.get("_critiques", [])
    verdict = "pass"
    if critiques:
        has_reject = any(c.get("verdict") == "REJECT" for c in critiques)
        has_weak = any(c.get("verdict") in ("WEAK_BEST_AVAILABLE", "NEEDS_REVISION") for c in critiques)
        verdict = "fail" if has_reject else ("review" if has_weak else "pass")
    return {
        "job_id": job_id,
        "verdict": verdict,
        "clips_inspected": len(j.get("clips", [])),
        "critiques": critiques,
        "subtitle_qa": stages.get("subtitle_qa", {}),
        "render_info": stages.get("render", {}),
    }

@app.get("/api/critic/{job_id}")
async def get_critic(job_id: str):
    """Return editorial critique and revision data for a job."""
    j = jobs.get(job_id)
    if not j:
        raise HTTPException(404, f"Job {job_id} not found")
    critiques = j.get("_critiques", [])
    critique_report = {
        "revision_required": any(
            c.get("verdict") == "NEEDS_REVISION" for c in critiques
        ),
        "issues": [
            {"severity": "high" if c.get("verdict") == "REJECT" else "medium",
             "message": f"Clip {c.get('clip_index', '?')}: {c.get('verdict', 'unknown')}"}
            for c in critiques if c.get("verdict") not in ("GOLD", "ACCEPTABLE")
        ],
    }
    revision_data = {
        "requested": critique_report["revision_required"],
        "actions": [c.get("revision_directives", []) for c in critiques],
        "attempt": max((c.get("revision_count", 0) for c in critiques), default=0),
    }
    return {
        "job_id": job_id,
        "critique": critique_report,
        "revision": revision_data,
    }

@app.get("/api/publish/{job_id}")
async def get_publish_plan(job_id: str):
    """Return publish plan for a job."""
    j = jobs.get(job_id)
    if not j:
        raise HTTPException(404, f"Job {job_id} not found")
    # Build a publish plan from available data
    platforms = []
    publish_platforms = j.get("_publish_platforms", [])
    if publish_platforms:
        platforms = publish_platforms
    else:
        # Default platforms based on aspect ratio
        platforms = ["youtube", "tiktok", "instagram"]
    clips = j.get("clips", [])
    return {
        "job_id": job_id,
        "publish_plan": {
            "platforms": platforms,
            "metadata": {
                "clip_count": len(clips),
                "clips": clips,
                "aspect_ratio": j.get("_aspect_ratio", "9:16"),
                "broll": False,
            },
        },
    }

@app.post("/api/publish/{job_id}/{platform}")
async def publish_to_platform(job_id: str, platform: str):
    """Simulate publishing a clip to a platform (local-first, no actual upload)."""
    j = jobs.get(job_id)
    if not j:
        raise HTTPException(404, f"Job {job_id} not found")
    if j["status"] != "completed":
        raise HTTPException(400, f"Job {job_id} is not completed yet")
    # Local-first: we don't actually upload to any platform
    # Return a mock publish confirmation
    log.info(f"[Publish] Job {job_id} → {platform} (local-first mock)")
    return {
        "job_id": job_id,
        "platform": platform,
        "status": "ready",
        "message": f"Clip prepared for {platform}. Manual upload required (local-first mode).",
    }

@app.get("/api/analytics/{job_id}")
async def get_analytics(job_id: str):
    """Return analytics data for a job (local-first: editorial metrics only)."""
    j = jobs.get(job_id)
    if not j:
        raise HTTPException(404, f"Job {job_id} not found")
    critiques = j.get("_critiques", [])
    stages = j.get("_stages", {})
    return {
        "job_id": job_id,
        "clip_count": len(j.get("clips", [])),
        "gold_clips": sum(1 for c in critiques if c.get("verdict") == "GOLD"),
        "acceptable_clips": sum(1 for c in critiques if c.get("verdict") == "ACCEPTABLE"),
        "revised_clips": sum(1 for c in critiques if c.get("revised")),
        "avg_score": round(
            sum(c.get("score", 0) for c in critiques) / max(len(critiques), 1), 3
        ),
        "stages": list(stages.keys()),
        "broll": False,
    }

@app.get("/api/download/{job_id}")
async def download_clips(job_id: str):
    """Download rendered clips as a zip or individual file."""
    j = jobs.get(job_id)
    if not j:
        raise HTTPException(404, f"Job {job_id} not found")
    if j["status"] != "completed":
        raise HTTPException(400, f"Job {job_id} is not completed")

    clips = j.get("clips", [])
    if not clips:
        raise HTTPException(404, "No clips available for download")

    # If single clip, stream it directly
    if len(clips) == 1:
        clip_path = OUTPUT_DIR / job_id / Path(clips[0]).name
        if not clip_path.exists():
            # Try as-is (could be a full path or relative)
            alt = Path(clips[0])
            if alt.exists():
                clip_path = alt
            else:
                raise HTTPException(404, f"Clip file not found: {clips[0]}")
        return FileResponse(
            str(clip_path),
            media_type="video/mp4",
            filename=clip_path.name,
        )

    # Multiple clips: zip them
    import zipfile, io
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for clip_path_str in clips:
            clip_path = OUTPUT_DIR / job_id / Path(clip_path_str).name
            if not clip_path.exists():
                alt = Path(clip_path_str)
                if alt.exists():
                    clip_path = alt
                else:
                    log.warning(f"[Download] Clip not found: {clip_path_str}")
                    continue
            zf.write(str(clip_path), clip_path.name)
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=nexux_{job_id}.zip"},
    )

# ── WebSocket ──

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await ws.connect(websocket)
    try:
        await websocket.send_json({
            "type": "connected",
            "version": "6.4.0",
            "active_jobs": active_count,
        })
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                t = msg.get("type", "")
                if t == "ping":
                    await websocket.send_json({"type": "pong"})
                elif t == "subscribe" and msg.get("job_id") in jobs:
                    await websocket.send_json({
                        "type": "job_status",
                        **_job_to_response(jobs[msg["job_id"]]).model_dump()
                    })
                elif t == "get_status":
                    await websocket.send_json({
                        "type": "status",
                        "active_jobs": active_count,
                        "total_jobs": len(jobs),
                    })
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        await ws.disconnect(websocket)

# ── Pipeline Processor ──

async def _process_job(job_id: str, url: str, kwargs: dict):
    global active_count
    job = jobs[job_id]

    async def _progress(stage: str, pct: float, **data):
        if cancel_flags.get(job_id):
            raise asyncio.CancelledError()
        job["stage"] = stage
        job["progress"] = pct
        # Store stage data internally
        if stage and data:
            job["_stages"][stage] = data
        await ws.broadcast({
            "type": "job_progress",
            "job_id": job_id,
            "stage": stage,
            "progress": pct,
            **data,
        })

    try:
        job["status"] = "processing"
        result = await run_pipeline(url, job_id, _progress, **kwargs)

        if result.get("status") == "completed":
            clips = result.get("clips", [])
            output_path = result.get("output_path")
            stages = result.get("stages", {})
            critiques = result.get("critiques", [])

            # Build render_meta from critiques and stages
            render_meta = []
            for i, clip_path in enumerate(clips):
                critique = critiques[i] if i < len(critiques) else {}
                render_meta.append({
                    "candidate_id": f"{job_id}-c{i}",
                    "editorial_rank": i + 1,
                    "editorial_signals": critique.get("dimensions", {}),
                    "editorial_evidence": critique.get("issues", []),
                    "virality": critique.get("score", 0),
                    "genre": kwargs.get("genre", "auto"),
                    "timeline": stages.get("render", {}),
                    "render": {"path": clip_path},
                    "voiceover": kwargs.get("voice_over_text") if kwargs.get("voice_over") else None,
                })

            # Store analysis bundle from stages
            analysis_bundle = {
                "download": stages.get("download", {}),
                "vision": stages.get("vision", {}),
                "transcribe": stages.get("transcribe", {}),
                "analyze": stages.get("analyze", {}),
                "subtitle_qa": stages.get("subtitle_qa", {}),
                "critique": stages.get("critique", {}),
            }

            # Store critique summary
            critique_summary = {
                "revision_required": any(
                    c.get("verdict") == "NEEDS_REVISION" for c in critiques
                ),
                "issues": [
                    {"severity": "high" if c.get("verdict") == "REJECT" else "medium",
                     "message": f"Clip {c.get('clip_index', '?')}: {c.get('verdict', 'unknown')}"}
                    for c in critiques if c.get("verdict") not in ("GOLD", "ACCEPTABLE")
                ],
            }

            revision_summary = {
                "requested": critique_summary["revision_required"],
                "actions": [c.get("revision_directives", []) for c in critiques],
                "attempt": max((c.get("revision_count", 0) for c in critiques), default=0),
            }

            # Build publish plan if platforms were specified
            publish_plan = None
            if kwargs.get("publish_platforms"):
                publish_plan = {
                    "platforms": kwargs["publish_platforms"],
                    "metadata": {
                        "clip_count": len(clips),
                        "clips": clips,
                        "aspect_ratio": kwargs.get("aspect_ratio", "9:16"),
                        "broll": False,
                    },
                }

            # Editorial decision summary
            editorial_decision = {
                "total_clips": len(clips),
                "gold": sum(1 for c in critiques if c.get("verdict") == "GOLD"),
                "acceptable": sum(1 for c in critiques if c.get("verdict") == "ACCEPTABLE"),
                "revised": sum(1 for c in critiques if c.get("revised")),
                "weak": sum(1 for c in critiques if c.get("verdict") in ("WEAK_BEST_AVAILABLE", "REJECT")),
            }

            job.update(
                status="completed",
                progress=100,
                stage="completed",
                output_path=output_path,
                clips=clips,
                render_meta=render_meta,
                analysis_bundle=analysis_bundle,
                critique=critique_summary,
                revision=revision_summary,
                publish_plan=publish_plan,
                editorial_decision=editorial_decision,
            )
            job["_stages"] = stages
            job["_critiques"] = critiques
            job["_aspect_ratio"] = kwargs.get("aspect_ratio", "9:16")
            job["_publish_platforms"] = kwargs.get("publish_platforms", [])

            await ws.broadcast({
                "type": "job_completed",
                "job_id": job_id,
                "output_path": output_path,
                "clips": clips,
            })

            # Webhook callback
            if kwargs.get("webhook_url"):
                await _send_webhook(kwargs["webhook_url"], job)

        else:
            job["status"] = "failed"
            job["error"] = result.get("error", "Unknown error")
            await ws.broadcast({
                "type": "job_failed",
                "job_id": job_id,
                "error": result.get("error"),
            })

    except asyncio.CancelledError:
        job["status"] = "cancelled"
        job["error"] = "Cancelled by user"
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        log.error(f"[Job {job_id}] Failed: {e}", exc_info=True)
        await ws.broadcast({
            "type": "job_failed",
            "job_id": job_id,
            "error": str(e),
        })
    finally:
        active_count = max(0, active_count - 1)

async def _send_webhook(url: str, job: dict):
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={
                k: v for k, v in job.items() if not k.startswith("_")
            })
    except Exception as e:
        log.warning(f"Webhook failed: {e}")

# ── Entry ──

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
        reload=False,
        log_level="info",
    )
