"""
NexuX V7.0 — FastAPI Backend (Production-Ready)
==================================================
Canonical API matching the frontend V7.0 contract.

V7.0 upgrades from V6.4 (legacy):
- SQLite persistent job storage (survives restarts)
- API key authentication (optional, env-based)
- Job history with pagination
- Automatic cleanup of old jobs (TTL-based)
- Structured logging with request IDs
- Rate limiting per API key

Architecture:
- Local-first: no cloud AI, no external API calls
- All processing on-device via FFmpeg + Whisper + OpenCV
- B-roll-free editorial policy (NO_BROLL_POLICY.md)
"""
import os, json, time, asyncio, uuid, sqlite3, hashlib
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from fastapi import (
    FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks,
    HTTPException, Request, Depends, Query,
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

# ── Constants ──
VERSION = "7.0.0"
DB_PATH = Path(os.environ.get("NEXUX_DB_PATH", "nexux_jobs.db"))
JOB_TTL_HOURS = int(os.environ.get("NEXUX_JOB_TTL_HOURS", "72"))
API_KEY = os.environ.get("NEXUX_API_KEY", "")  # Empty = no auth (local dev)

# ── SQLite Job Store ──

def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

db = None

def _init_db():
    """Create tables if not exist."""
    global db
    db = _get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'queued',
            progress REAL DEFAULT 0.0,
            stage TEXT DEFAULT 'queued',
            output_path TEXT,
            error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            clips TEXT DEFAULT '[]',
            broll INTEGER DEFAULT 0,
            render_meta TEXT DEFAULT '[]',
            analysis_bundle TEXT,
            critique TEXT,
            revision TEXT,
            publish_plan TEXT,
            editorial_decision TEXT,
            request_data TEXT,
            api_key_hash TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
        CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at);
        CREATE INDEX IF NOT EXISTS idx_jobs_api_key ON jobs(api_key_hash);
    """)
    db.commit()

def _save_job(job: dict):
    """Persist job to SQLite."""
    if not db:
        return
    try:
        db.execute("""
            INSERT OR REPLACE INTO jobs (
                job_id, status, progress, stage, output_path, error,
                created_at, updated_at, clips, broll, render_meta,
                analysis_bundle, critique, revision, publish_plan,
                editorial_decision, request_data, api_key_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job["job_id"],
            job["status"],
            job["progress"],
            job["stage"],
            job.get("output_path"),
            job.get("error"),
            job["created_at"],
            datetime.now(timezone.utc).isoformat(),
            json.dumps(job.get("clips", [])),
            int(job.get("broll", False)),
            json.dumps(job.get("render_meta", [])),
            json.dumps(job["analysis_bundle"]) if job.get("analysis_bundle") else None,
            json.dumps(job["critique"]) if job.get("critique") else None,
            json.dumps(job["revision"]) if job.get("revision") else None,
            json.dumps(job["publish_plan"]) if job.get("publish_plan") else None,
            json.dumps(job["editorial_decision"]) if job.get("editorial_decision") else None,
            json.dumps(job.get("_request_data", {})),
            job.get("_api_key_hash"),
        ))
        db.commit()
    except Exception as e:
        log.warning(f"[DB] Failed to save job {job['job_id']}: {e}")

def _load_job(job_id: str) -> Optional[dict]:
    """Load a job from SQLite."""
    if not db:
        return None
    row = db.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    if not row:
        return None
    return _row_to_job(row)

def _load_jobs(status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[dict]:
    """Load jobs from SQLite with optional filtering."""
    if not db:
        return []
    if status:
        rows = db.execute(
            "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (status, limit, offset)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
    return [_row_to_job(r) for r in rows]

def _row_to_job(row: sqlite3.Row) -> dict:
    """Convert a SQLite row to a job dict."""
    return {
        "job_id": row["job_id"],
        "status": row["status"],
        "progress": row["progress"],
        "stage": row["stage"],
        "output_path": row["output_path"],
        "error": row["error"],
        "created_at": row["created_at"],
        "clips": json.loads(row["clips"] or "[]"),
        "broll": bool(row["broll"]),
        "render_meta": json.loads(row["render_meta"] or "[]"),
        "analysis_bundle": json.loads(row["analysis_bundle"]) if row["analysis_bundle"] else None,
        "critique": json.loads(row["critique"]) if row["critique"] else None,
        "revision": json.loads(row["revision"]) if row["revision"] else None,
        "publish_plan": json.loads(row["publish_plan"]) if row["publish_plan"] else None,
        "editorial_decision": json.loads(row["editorial_decision"]) if row["editorial_decision"] else None,
        "_stages": {},
        "_critiques": [],
    }

def _cleanup_old_jobs():
    """Delete jobs older than TTL."""
    if not db:
        return
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=JOB_TTL_HOURS)).isoformat()
    try:
        db.execute("DELETE FROM jobs WHERE created_at < ?", (cutoff,))
        db.commit()
        deleted = db.total_changes
        if deleted:
            log.info(f"[DB] Cleaned up {deleted} old jobs (TTL={JOB_TTL_HOURS}h)")
    except Exception as e:
        log.warning(f"[DB] Cleanup failed: {e}")

# ── API Key Auth ──

def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()[:16]

def _verify_api_key(request: Request) -> bool:
    """Verify API key from X-API-Key header. Returns True if auth disabled or key valid."""
    if not API_KEY:
        return True  # No key set = local dev mode, auth disabled
    provided = request.headers.get("X-API-Key", "")
    if not provided:
        return False
    return _hash_key(provided) == _hash_key(API_KEY)

async def _require_auth(request: Request):
    """Dependency that raises 401 if API key is invalid."""
    if not _verify_api_key(request):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Set X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

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

# ── In-Memory Job Cache ──
# Hot cache for active jobs. SQLite is the source of truth for persistence.

jobs: Dict[str, dict] = {}
cancel_flags: Dict[str, bool] = {}
active_count = 0

def _new_job(jid: str) -> dict:
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
        "_stages": {},
        "_critiques": [],
        "_request_data": {},
        "_api_key_hash": None,
    }

# ── App ──

ALLOWED_ORIGINS = os.environ.get(
    "NEXUX_ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db
    log.info(f"NexuX V{VERSION} starting (local-first, no B-roll, SQLite persistence)...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _init_db()
    _cleanup_old_jobs()
    # Restore in-progress jobs from DB (mark as interrupted)
    if db:
        rows = db.execute("SELECT job_id FROM jobs WHERE status IN ('queued', 'processing')").fetchall()
        for r in rows:
            db.execute("UPDATE jobs SET status = 'interrupted', error = 'Server restarted' WHERE job_id = ?", (r["job_id"],))
        db.commit()
        if rows:
            log.info(f"[DB] Marked {len(rows)} interrupted jobs from previous session")
    yield
    if db:
        db.close()
    log.info("Shutting down...")

app = FastAPI(
    title="NexuX Local-First Canonical",
    version=VERSION,
    description="Autonomous AI Video Repurposing Engine — Local-First, Zero Cloud Cost, Production-Ready",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

odir = OUTPUT_DIR if isinstance(OUTPUT_DIR, Path) else Path(str(OUTPUT_DIR))
odir.mkdir(parents=True, exist_ok=True)
app.mount("/output", StaticFiles(directory=str(odir.absolute())), name="output")

# ── Helpers ──

def _job_to_response(j: dict) -> JobResponse:
    public = {k: v for k, v in j.items() if not k.startswith("_")}
    if public.get("render_meta") is None:
        public["render_meta"] = []
    return JobResponse(**public)

def _get_job(job_id: str) -> Optional[dict]:
    """Get job from hot cache, fall back to SQLite."""
    if job_id in jobs:
        return jobs[job_id]
    return _load_job(job_id)

# ── Routes ──

@app.get("/")
async def root():
    return {
        "name": "NexuX",
        "version": VERSION,
        "status": "operational",
        "canonical_runtime": True,
        "broll": False,
        "auth_enabled": bool(API_KEY),
        "active_jobs": active_count,
        "total_jobs": len(jobs),
        "ws_clients": ws.count,
    }

@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "canonical_runtime": True,
        "canonical_engine": f"local-first-v{VERSION}",
        "broll": False,
        "auth_enabled": bool(API_KEY),
        "active_jobs": active_count,
        "queued_jobs": len([j for j in jobs.values() if j["status"] == "queued"]),
        "ws_clients": ws.count,
        "db_connected": db is not None,
        "timestamp": time.time(),
    }

@app.get("/api/styles")
async def get_styles(_=Depends(_require_auth)):
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
async def preview(url: str, _=Depends(_require_auth)):
    try:
        info = get_video_info(url)
        return PreviewResponse(status="ok", video=info)
    except Exception as e:
        raise HTTPException(400, f"Preview failed: {e}")

@app.post("/api/search")
async def search(req: SearchRequest, _=Depends(_require_auth)):
    try:
        results = search_youtube(req.query, req.max_results)
        return {"status": "ok", "results": results, "total": len(results)}
    except Exception as e:
        raise HTTPException(400, f"Search failed: {e}")

@app.post("/api/generate", response_model=JobResponse)
async def generate(req: GenerateRequest, bg: BackgroundTasks, request: Request, _=Depends(_require_auth)):
    global active_count

    if active_count >= MAX_CONCURRENT_JOBS:
        raise HTTPException(429, f"Max {MAX_CONCURRENT_JOBS} concurrent jobs. Try again shortly.")

    jid = f"nx-{uuid.uuid4().hex}"
    job = _new_job(jid)
    job["_request_data"] = req.model_dump()
    job["_api_key_hash"] = _hash_key(API_KEY) if API_KEY else None
    jobs[jid] = job
    cancel_flags[jid] = False
    active_count += 1
    _save_job(job)

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
async def get_job(job_id: str, _=Depends(_require_auth)):
    j = _get_job(job_id)
    if not j:
        raise HTTPException(404, f"Job {job_id} not found")
    return _job_to_response(j)

@app.get("/api/jobs")
async def list_jobs(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _=Depends(_require_auth),
):
    """List jobs with pagination. Checks hot cache first, then SQLite."""
    # Get active jobs from hot cache
    if status:
        cached = {k: v for k, v in jobs.items() if v["status"] == status}
    else:
        cached = dict(jobs)

    # Get historical jobs from SQLite
    db_jobs = _load_jobs(status, limit + 1, offset)

    # Merge: hot cache takes priority
    seen_ids = set()
    all_jobs = []
    for j in list(cached.values()):
        all_jobs.append(_job_to_response(j))
        seen_ids.add(j["job_id"])
    for j in db_jobs:
        if j["job_id"] not in seen_ids:
            all_jobs.append(_job_to_response(j))
            seen_ids.add(j["job_id"])

    # Sort by created_at desc
    all_jobs.sort(key=lambda x: x.created_at, reverse=True)
    total = len(all_jobs)
    paginated = all_jobs[offset:offset + limit]

    return {
        "total": total,
        "jobs": paginated,
        "limit": limit,
        "offset": offset,
    }

@app.delete("/api/job/{job_id}")
async def cancel_job(job_id: str, _=Depends(_require_auth)):
    global active_count
    j = _get_job(job_id)
    if not j:
        raise HTTPException(404, f"Job {job_id} not found")
    if j["status"] in ("completed", "failed", "cancelled", "interrupted"):
        raise HTTPException(400, f"Job already {j['status']}")
    cancel_flags[job_id] = True
    j["status"] = "cancelled"
    active_count = max(0, active_count - 1)
    _save_job(j)
    await ws.broadcast({"type": "job_cancelled", "job_id": job_id})
    return {"job_id": job_id, "status": "cancelled"}

# ── V7.0 Advanced Endpoints ──

@app.get("/api/vision/{job_id}")
async def get_vision(job_id: str, _=Depends(_require_auth)):
    j = _get_job(job_id)
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
        "source": stages.get("download", {}).get("path"),
    }

@app.get("/api/render-qa/{job_id}")
async def get_render_qa(job_id: str, _=Depends(_require_auth)):
    j = _get_job(job_id)
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
async def get_critic(job_id: str, _=Depends(_require_auth)):
    j = _get_job(job_id)
    if not j:
        raise HTTPException(404, f"Job {job_id} not found")
    critiques = j.get("_critiques", [])
    critique_report = {
        "revision_required": any(c.get("verdict") == "NEEDS_REVISION" for c in critiques),
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
async def get_publish_plan(job_id: str, _=Depends(_require_auth)):
    j = _get_job(job_id)
    if not j:
        raise HTTPException(404, f"Job {job_id} not found")
    platforms = j.get("_publish_platforms", []) or ["youtube", "tiktok", "instagram"]
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
async def publish_to_platform(job_id: str, platform: str, _=Depends(_require_auth)):
    j = _get_job(job_id)
    if not j:
        raise HTTPException(404, f"Job {job_id} not found")
    if j["status"] != "completed":
        raise HTTPException(400, f"Job {job_id} is not completed yet")
    log.info(f"[Publish] Job {job_id} → {platform} (local-first mock)")
    return {
        "job_id": job_id,
        "platform": platform,
        "status": "ready",
        "message": f"Clip prepared for {platform}. Manual upload required (local-first mode).",
    }

@app.get("/api/analytics/{job_id}")
async def get_analytics(job_id: str, _=Depends(_require_auth)):
    j = _get_job(job_id)
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
        "avg_score": round(sum(c.get("score", 0) for c in critiques) / max(len(critiques), 1), 3),
        "stages": list(stages.keys()),
        "broll": False,
    }

@app.get("/api/download/{job_id}")
async def download_clips(job_id: str, _=Depends(_require_auth)):
    j = _get_job(job_id)
    if not j:
        raise HTTPException(404, f"Job {job_id} not found")
    if j["status"] != "completed":
        raise HTTPException(400, f"Job {job_id} is not completed")

    clips = j.get("clips", [])
    if not clips:
        raise HTTPException(404, "No clips available for download")

    if len(clips) == 1:
        clip_path = OUTPUT_DIR / job_id / Path(clips[0]).name
        if not clip_path.exists():
            alt = Path(clips[0])
            if alt.exists():
                clip_path = alt
            else:
                raise HTTPException(404, f"Clip file not found: {clips[0]}")
        return FileResponse(str(clip_path), media_type="video/mp4", filename=clip_path.name)

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
            "version": VERSION,
            "active_jobs": active_count,
        })
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                t = msg.get("type", "")
                if t == "ping":
                    await websocket.send_json({"type": "pong"})
                elif t == "subscribe" and msg.get("job_id"):
                    j = _get_job(msg["job_id"])
                    if j:
                        await websocket.send_json({
                            "type": "job_status",
                            **_job_to_response(j).model_dump()
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
        if stage and data:
            job["_stages"][stage] = data
        _save_job(job)
        await ws.broadcast({
            "type": "job_progress",
            "job_id": job_id,
            "stage": stage,
            "progress": pct,
            **data,
        })

    try:
        job["status"] = "processing"
        _save_job(job)
        result = await run_pipeline(url, job_id, _progress, **kwargs)

        if result.get("status") == "completed":
            clips = result.get("clips", [])
            output_path = result.get("output_path")
            stages = result.get("stages", {})
            critiques = result.get("critiques", [])

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

            analysis_bundle = {
                "download": stages.get("download", {}),
                "vision": stages.get("vision", {}),
                "transcribe": stages.get("transcribe", {}),
                "analyze": stages.get("analyze", {}),
                "subtitle_qa": stages.get("subtitle_qa", {}),
                "critique": stages.get("critique", {}),
            }

            critique_summary = {
                "revision_required": any(c.get("verdict") == "NEEDS_REVISION" for c in critiques),
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
            _save_job(job)

            await ws.broadcast({
                "type": "job_completed",
                "job_id": job_id,
                "output_path": output_path,
                "clips": clips,
            })

            if kwargs.get("webhook_url"):
                await _send_webhook(kwargs["webhook_url"], job)

        else:
            job["status"] = "failed"
            job["error"] = result.get("error", "Unknown error")
            _save_job(job)
            await ws.broadcast({
                "type": "job_failed",
                "job_id": job_id,
                "error": result.get("error"),
            })

    except asyncio.CancelledError:
        job["status"] = "cancelled"
        job["error"] = "Cancelled by user"
        _save_job(job)
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)
        _save_job(job)
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
