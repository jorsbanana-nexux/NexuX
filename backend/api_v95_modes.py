"""
NexuX V9.5 — Unified Mode API Endpoints
==========================================
New API endpoints for the dual-mode system.

POST /api/v2/generate     → Start generation (auto-detects mode from input)
GET  /api/v2/modes        → List available modes
POST /api/v2/mode2/generate → Mode 2 specific generation (keyword-based)

These endpoints supplement the existing V8.0 endpoints in main.py.
Import and include this router in main.py.
"""
import asyncio
import uuid
from typing import Optional, List
from datetime import datetime, timezone
from logging import getLogger

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field

from engine.mode_router import get_mode_config, get_all_modes, validate_mode_input
from engine.opus_killer import score_with_opus_killer
from engine.podcast_analyzer import analyze_podcast
from engine.clip_titler import generate_clip_titles, generate_hashtags, generate_description
from engine.keyword_expander import expand_keyword, get_search_strategy

log = getLogger("nexus.api_v2")

router = APIRouter(prefix="/api/v2", tags=["v2"])


# ── Pydantic Models ──

class GenerateV2Request(BaseModel):
    """Unified generation request that supports both modes."""
    mode: str = Field("podcast", pattern="^(podcast|creative|mode1|mode2|1|2)$")
    
    # Mode 1 (Podcast)
    youtube_url: Optional[str] = None
    target_duration: int = Field(45, ge=20, le=90)
    clip_count: int = Field(5, ge=1, le=10)
    aspect_ratio: str = Field("9:16")
    subtitle_style: str = Field("hormozi")
    auto_zoom: bool = True
    face_tracking: bool = True
    language: Optional[str] = None
    remove_fillers: bool = True
    
    # Mode 2 (Creative)
    keyword: Optional[str] = None
    voice_enabled: bool = True
    voice_name: str = Field("id-ID-ArdiNeural")
    sfx_enabled: bool = True
    bgm_enabled: bool = True
    max_sources: int = Field(10, ge=3, le=20)
    
    # Shared
    color_grade: str = Field("none")


class ModeResponse(BaseModel):
    mode: str
    name: str
    description: str
    icon: str
    color: str
    requires_url: bool
    requires_keyword: bool
    features: List[str]


class GenerateV2Response(BaseModel):
    job_id: str
    mode: str
    status: str
    message: str


# ── Endpoints ──

@router.get("/modes", response_model=List[ModeResponse])
async def list_modes():
    """List all available modes with their features."""
    modes = get_all_modes()
    return [
        ModeResponse(
            mode=m.mode, name=m.name, description=m.description,
            icon=m.icon, color=m.color,
            requires_url=m.requires_url, requires_keyword=m.requires_keyword,
            features=m.features,
        )
        for m in modes
    ]


@router.post("/generate", response_model=GenerateV2Response)
async def generate_v2(
    req: GenerateV2Request,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Unified generation endpoint.
    
    Auto-detects mode from input:
    - If youtube_url provided → Mode 1 (Podcast)
    - If keyword provided → Mode 2 (Creative)
    - If mode explicitly set, validates the required input
    """
    # Normalize mode
    mode = req.mode
    if mode in ("mode1", "1"):
        mode = "podcast"
    elif mode in ("mode2", "2"):
        mode = "creative"
    
    # Auto-detect mode if not explicit
    if not req.youtube_url and not req.keyword:
        raise HTTPException(400, "Either youtube_url (Mode 1) or keyword (Mode 2) is required")
    
    if req.youtube_url and not req.keyword:
        mode = "podcast"
    elif req.keyword and not req.youtube_url:
        mode = "creative"
    
    # Validate
    is_valid, error = validate_mode_input(mode, req.youtube_url, req.keyword)
    if not is_valid:
        raise HTTPException(400, error)
    
    config = get_mode_config(mode)
    job_id = f"{mode}_{uuid.uuid4().hex[:12]}"
    
    log.info(f"[API V2] Generate request: mode={mode}, job_id={job_id}")
    
    # Deferred import: api_v95_modes is imported by main at startup,
    # so main's helpers can only be imported at request time.
    from main import start_pipeline_job, start_mode2_job

    if mode == "podcast":
        # Register a REAL job in the store → progress, WebSocket updates,
        # cancellation, and SQLite persistence all work exactly like /api/generate.
        start_pipeline_job(
            background_tasks,
            req.youtube_url,
            {
                "target_duration": req.target_duration,
                "clip_count": req.clip_count,
                "aspect_ratio": req.aspect_ratio,
                "subtitle_style": req.subtitle_style,
                "auto_zoom": req.auto_zoom,
                "face_tracking": req.face_tracking,
                "language": req.language,
                "remove_fillers_pauses": req.remove_fillers,
                "color_grade": req.color_grade,
            },
            job_id=job_id,
        )

        return GenerateV2Response(
            job_id=job_id, mode=mode, status="queued",
            message=f"🎙️ {config.name} started! Poll /api/job/{job_id} for progress."
        )

    else:
        # Register a REAL Mode 2 job → pollable via /api/job/{job_id} like Mode 1.
        start_mode2_job(
            background_tasks,
            {
                "keyword": req.keyword,
                "voice_enabled": req.voice_enabled,
                "voice_name": req.voice_name,
                "sfx_enabled": req.sfx_enabled,
                "bgm_enabled": req.bgm_enabled,
                "target_duration": req.target_duration,
                "max_sources": req.max_sources,
            },
            job_id=job_id,
        )

        return GenerateV2Response(
            job_id=job_id, mode=mode, status="queued",
            message=f"✨ {config.name} started! Poll /api/job/{job_id} for progress."
        )


@router.get("/keyword/expand")
async def expand_keyword_endpoint(keyword: str, max_terms: int = 15):
    """
    Expand a keyword into related search terms.
    Useful for previewing what Mode 2 will search for.
    """
    terms = expand_keyword(keyword, max_terms=max_terms)
    strategy = get_search_strategy(keyword)
    return {
        "original": keyword,
        "expanded": terms,
        "niche": strategy.get("niche"),
        "primary_terms": strategy["primary_terms"],
        "secondary_terms": strategy["secondary_terms"],
    }


@router.get("/modes/{mode}/features")
async def get_mode_features(mode: str):
    """Get detailed features for a specific mode."""
    try:
        config = get_mode_config(mode)
        return {
            "mode": config.mode,
            "name": config.name,
            "description": config.description,
            "icon": config.icon,
            "features": config.features,
            "requires_url": config.requires_url,
            "requires_keyword": config.requires_keyword,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
