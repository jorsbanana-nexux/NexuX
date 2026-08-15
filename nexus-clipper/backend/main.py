"""
Nexus-Clipper Premium v4.0 — FastAPI Backend
==============================================
Enterprise API with:
- Job queue with concurrency control
- WebSocket real-time progress
- Job cancellation
- Rate limiting
- Structured error responses
- Health monitoring
"""
import os, json, time, asyncio, signal, uuid
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

from engine import (
    run_pipeline, get_video_info, search_youtube,
    STYLE_PRESETS, ASPECT_RATIOS, COLOR_GRADES,
    OUTPUT_DIR,
)
from engine.constants import MAX_CONCURRENT_JOBS

# ── Logger Setup ──
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
log = logging.getLogger("nexus.api")

# ── Models ──

class GenerateRequest(BaseModel):
    youtube_url: str = Field(..., min_length=10, max_length=500)
    target_duration: int = Field(60, ge=15, le=300)
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
    # Local-first: cloud AI scoring is opt-in only.
    ai_scoring: bool = Field(False)
    normalize_audio: bool = Field(True)
    webhook_url: Optional[str] = None

class JobResponse(BaseModel):
    job_id: str
    status: str
    progress: float = 0.0
    stage: str = "queued"
    output_path: Optional[str] = None
    error: Optional[str] = None
    created_at: str = ""
    clips: List[str] = []

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

jobs: Dict[str, dict] = {}
job_locks: Dict[str, asyncio.Lock] = {}
cancel_flags: Dict[str, bool] = {}
active_count = 0

# ── App ──

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Nexus-Clipper Premium v4.0 starting...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    yield
    log.info("Shutting down...")

app = FastAPI(
    title="Nexus-Clipper Premium",
    version="4.0.0",
    description="Autonomous AI Video Generation Platform — Enterprise Edition",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for output
odir = Path("output")
odir.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(odir.absolute())), name="output")

# ── Routes ──

@app.get("/")
async def root():
    return {
        "name": "Nexus-Clipper Premium",
        "version": "4.0.0",
        "status": "operational",
        "active_jobs": active_count,
        "total_jobs": len(jobs),
        "ws_clients": ws.count,
    }

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
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
        "color_grades": list(COLOR_GRADES.keys()),
        "video_codecs": ["h264", "h265"],
        "audio_codecs": ["aac", "mp3"],
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
    
    # UUID prevents collisions when multiple requests arrive in the same second.
    jid = f"nx-{uuid.uuid4().hex}"
    job = {
        "job_id": jid,
        "status": "queued",
        "progress": 0.0,
        "stage": "queued",
        "output_path": None,
        "error": None,
        "clips": [],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
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
    }
    
    # Keep webhook delivery outside pipeline kwargs so the engine signature
    # remains focused on rendering/transformation options.
    bg.add_task(_process_job, jid, req.youtube_url, style_kwargs, req.webhook_url)
    log.info(f"Job {jid} queued: {req.youtube_url[:80]}")
    
    return JobResponse(**job)

@app.get("/api/job/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    j = jobs.get(job_id)
    if not j:
        raise HTTPException(404, f"Job {job_id} not found")
    return JobResponse(**j)

@app.get("/api/jobs")
async def list_jobs(status: Optional[str] = None):
    filtered = jobs
    if status:
        filtered = {k: v for k, v in jobs.items() if v["status"] == status}
    return {
        "total": len(filtered),
        "jobs": [JobResponse(**v) for v in filtered.values()],
    }

@app.delete("/api/job/{job_id}")
async def cancel_job(job_id: str):
    j = jobs.get(job_id)
    if not j:
        raise HTTPException(404, f"Job {job_id} not found")
    if j["status"] in ("completed", "failed", "cancelled"):
        raise HTTPException(400, f"Job already {j['status']}")
    cancel_flags[job_id] = True
    j["status"] = "cancelled"
    # _process_job owns active_count decrement so queued and running
    # cancellation paths cannot decrement the counter twice.
    await ws.broadcast({"type": "job_cancelled", "job_id": job_id})
    return {"job_id": job_id, "status": "cancelled"}

@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await ws.connect(websocket)
    try:
        await websocket.send_json({
            "type": "connected",
            "version": "4.0.0",
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
                        "type": "job_status", **jobs[msg["job_id"]]})
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

async def _process_job(
    job_id: str,
    url: str,
    kwargs: dict,
    webhook_url: Optional[str] = None,
):
    global active_count
    job = jobs[job_id]

    async def _progress(stage: str, pct: float, **data):
        if cancel_flags.get(job_id):
            raise asyncio.CancelledError()
        job.update(stage=stage, progress=pct)
        await ws.broadcast({
            "type": "job_progress",
            "job_id": job_id,
            "stage": stage,
            "progress": pct,
            **data,
        })

    try:
        # A queued job may be cancelled before BackgroundTasks gets to run it.
        if cancel_flags.get(job_id) or job["status"] == "cancelled":
            raise asyncio.CancelledError()

        job["status"] = "processing"
        result = await run_pipeline(url, job_id, _progress, **kwargs)
        
        if result["status"] == "completed":
            job.update(
                status="completed", progress=100, stage="completed",
                output_path=result.get("output_path"),
                clips=result.get("clips", []),
            )
            await ws.broadcast({
                "type": "job_completed",
                "job_id": job_id,
                "output_path": result.get("output_path"),
            })
            # Webhook callback is deliberately outside the engine kwargs.
            if webhook_url:
                await _send_webhook(webhook_url, job)
        else:
            job.update(status="failed", error=result.get("error", "Unknown error"))
            await ws.broadcast({
                "type": "job_failed", "job_id": job_id,
                "error": result.get("error"),
            })

    except asyncio.CancelledError:
        job.update(status="cancelled", error="Cancelled by user")
    except Exception as e:
        job.update(status="failed", error=str(e))
        await ws.broadcast({
            "type": "job_failed", "job_id": job_id,
            "error": str(e),
        })
    finally:
        # This is the single ownership point for releasing the concurrency slot.
        active_count = max(0, active_count - 1)

async def _send_webhook(url: str, job: dict):
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json=job)
    except Exception as e:
        log.warning(f"Webhook failed: {e}")

# ── Entry ──

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, log_level="info")
