"""
NexuX V9.5 — Post-Render Editor API
=====================================
Backend endpoints that power the post-render personalization editor.

Endpoints:
GET  /api/editor/templates          → List all creator template presets
GET  /api/editor/styles             → List all subtitle style presets
GET  /api/editor/effects            → List available effects (zoom, color grade, speed ramp)
POST /api/editor/preview/{job_id}/{clip_idx} → Real-time preview render
POST /api/editor/rerender/{job_id}/{clip_idx} → Full re-render with personalization
POST /api/editor/rerender/{job_id}/all        → Batch re-render all clips
GET  /api/editor/clip/{job_id}/{clip_idx}      → Get clip details (transcript, segments, metadata)
"""
import os
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from .engine.styles import STYLE_PRESETS, resolve_style
from .engine.constants import OUTPUT_DIR, ASPECT_RATIOS, COLOR_GRADES

log = logging.getLogger("nexus.api.editor")

router = APIRouter(prefix="/api/editor", tags=["editor"])


# ── Pydantic Models ──

class PersonalizationRequest(BaseModel):
    """Full personalization settings for re-rendering a clip."""
    # Subtitle/Caption settings
    subtitle_style: str = Field("hormozi")
    font: str = Field("Arial")
    font_size: int = Field(52, ge=20, le=100)
    primary_color: str = Field("#FFFFFF")
    highlight_color: str = Field("#FFD700")
    stroke_color: str = Field("#000000")
    stroke_width: int = Field(3, ge=1, le=10)
    position: str = Field("center")
    animation: str = Field("pop")
    highlight_words: bool = True
    show_emojis: bool = True
    bg_bar: bool = True
    bg_opacity: float = Field(0.35, ge=0, le=1)

    # Visual effects
    zoom_style: str = Field("subtle")  # subtle, dramatic, punch, breathing, none
    zoom_level: float = Field(1.0, ge=1.0, le=3.0)
    color_grade: str = Field("none")  # none, warm, cool, vibrant, cinematic, vintage
    speed_ramp: bool = False
    speed_ramp_type: str = Field("none")  # slowmo, speedup, punch, none

    # Layout
    aspect_ratio: str = Field("9:16")
    auto_reframe: bool = True
    face_tracking: bool = True

    # Audio
    bgm_volume: int = Field(50, ge=0, le=100)
    voice_volume: int = Field(100, ge=0, le=100)
    normalize_audio: bool = True
    bass_boost: bool = False
    sfx_enabled: bool = True

    # Branding
    watermark_text: str = ""
    watermark_position: str = "bottom-right"
    show_watermark: bool = False

    # Trim
    trim_start: float = 0.0
    trim_end: float = 0.0  # 0 = use original end

    # Template (if using a creator template)
    template_id: Optional[str] = None

    # Overlays (V9.0 timeline editor)
    overlays: Optional[List[Dict[str, Any]]] = None


class PreviewRequest(BaseModel):
    """Lightweight preview render request."""
    subtitle_style: str = "hormozi"
    zoom_style: str = "subtle"
    color_grade: str = "none"
    aspect_ratio: str = "9:16"
    # Only render first 5 seconds for preview
    preview_duration: float = Field(5.0, ge=1, le=15)


# ── Creator Templates (matches frontend) ──

CREATOR_TEMPLATES = [
    {"id": "hormozi", "name": "Hormozi Style", "creator": "Alex Hormozi",
     "description": "Bold yellow text, word-by-word pop, punchy zoom",
     "badge": "🔥 HOT", "badge_color": "text-orange-400",
     "style_id": "hormozi", "animation": "pop", "zoom_style": "punch",
     "color_grade": "vibrant", "speed_ramp": True, "speed_ramp_type": "punch"},
    {"id": "mrbeast", "name": "MrBeast Style", "creator": "Jimmy Donaldson",
     "description": "Huge text, explosive animations, extreme energy",
     "badge": "💥 EXPLOSIVE", "badge_color": "text-red-400",
     "style_id": "mrbeast", "animation": "bounce", "zoom_style": "dramatic",
     "color_grade": "vibrant", "speed_ramp": True, "speed_ramp_type": "punch"},
    {"id": "ali-abdaal", "name": "Ali Abdaal", "creator": "Ali Abdaal",
     "description": "Clean, minimal, professional — calm productivity",
     "badge": "📚 CLEAN", "badge_color": "text-blue-400",
     "style_id": "minimalist", "animation": "fade", "zoom_style": "subtle",
     "color_grade": "cool", "speed_ramp": False, "speed_ramp_type": "none"},
    {"id": "iman-gadzhi", "name": "Iman Gadzhi", "creator": "Iman Gadzhi",
     "description": "Dark aesthetic, gold accents, luxury feel",
     "badge": "👑 LUXURY", "badge_color": "text-amber-400",
     "style_id": "cinematic_gold", "animation": "fade_slow", "zoom_style": "breathing",
     "color_grade": "cinematic", "speed_ramp": False, "speed_ramp_type": "none"},
    {"id": "gamer-comic", "name": "Gamer Comic", "creator": "Gaming Community",
     "description": "Comic book style, glitch effects, high energy",
     "badge": "🎮 GAMER", "badge_color": "text-cyan-400",
     "style_id": "gaming", "animation": "bounce", "zoom_style": "dramatic",
     "color_grade": "vibrant", "speed_ramp": True, "speed_ramp_type": "speedup"},
    {"id": "neon-cyberpunk", "name": "Neon Cyberpunk", "creator": "Cyberpunk Aesthetic",
     "description": "Futuristic neon, glitch transitions, dark mode",
     "badge": "🌃 NEON", "badge_color": "text-fuchsia-400",
     "style_id": "neon", "animation": "flicker", "zoom_style": "breathing",
     "color_grade": "cool", "speed_ramp": False, "speed_ramp_type": "none"},
    {"id": "anime-impact", "name": "Anime Impact", "creator": "Anime Community",
     "description": "Explosive text, impact frames, dramatic pauses",
     "badge": "⚔️ ANIME", "badge_color": "text-red-400",
     "style_id": "gaming", "animation": "bounce", "zoom_style": "punch",
     "color_grade": "vibrant", "speed_ramp": True, "speed_ramp_type": "slowmo"},
    {"id": "minimal-aesthetic", "name": "Minimal Aesthetic", "creator": "Clean Design",
     "description": "Minimal text, subtle animations, elegant spacing",
     "badge": "✨ MINIMAL", "badge_color": "text-stone-300",
     "style_id": "minimalist", "animation": "fade_slow", "zoom_style": "none",
     "color_grade": "none", "speed_ramp": False, "speed_ramp_type": "none"},
    {"id": "podcast-pro", "name": "Podcast Pro", "creator": "Podcast Clips",
     "description": "Speaker labels, clean captions, professional cut",
     "badge": "🎙️ PODCAST", "badge_color": "text-cyan-400",
     "style_id": "podcast", "animation": "fade", "zoom_style": "subtle",
     "color_grade": "warm", "speed_ramp": False, "speed_ramp_type": "none"},
    {"id": "viral-tiktok", "name": "Viral TikTok", "creator": "TikTok Trends",
     "description": "Fast cuts, trending style, emoji-heavy captions",
     "badge": "📱 VIRAL", "badge_color": "text-pink-400",
     "style_id": "tiktok_viral", "animation": "pop", "zoom_style": "punch",
     "color_grade": "vibrant", "speed_ramp": True, "speed_ramp_type": "speedup"},
    {"id": "cinematic-story", "name": "Cinematic Story", "creator": "Filmmaker Style",
     "description": "Cinematic bars, slow zoom, serif font, dramatic",
     "badge": "🎬 CINEMA", "badge_color": "text-amber-300",
     "style_id": "cinematic", "animation": "fade_slow", "zoom_style": "breathing",
     "color_grade": "cinematic", "speed_ramp": False, "speed_ramp_type": "none"},
    {"id": "news-viral", "name": "News Viral", "creator": "News Clip Style",
     "description": "Breaking news style, bold headlines, urgent energy",
     "badge": "📢 NEWS", "badge_color": "text-red-400",
     "style_id": "news-pro", "animation": "pop", "zoom_style": "subtle",
     "color_grade": "none", "speed_ramp": False, "speed_ramp_type": "none"},
]


# ── Effects catalog ──

ZOOM_STYLES = [
    {"id": "none", "name": "No Zoom", "description": "Static frame, no movement"},
    {"id": "subtle", "name": "Subtle Zoom", "description": "Slow, barely noticeable zoom-in"},
    {"id": "dramatic", "name": "Dramatic Zoom", "description": "Fast zoom for impact moments"},
    {"id": "punch", "name": "Punch Zoom", "description": "Quick zoom punch on key words"},
    {"id": "breathing", "name": "Breathing Zoom", "description": "Gentle in-and-out zoom loop"},
]

COLOR_GRADES_LIST = [
    {"id": "none", "name": "None", "description": "Original colors"},
    {"id": "warm", "name": "Warm", "description": "Orange/amber tones, cozy feel"},
    {"id": "cool", "name": "Cool", "description": "Blue/cyan tones, tech feel"},
    {"id": "vibrant", "name": "Vibrant", "description": "Punchy, saturated colors"},
    {"id": "cinematic", "name": "Cinematic", "description": "Film-like teal & orange"},
    {"id": "vintage", "name": "Vintage", "description": "Faded retro look"},
]

SPEED_RAMP_TYPES = [
    {"id": "none", "name": "None", "description": "Constant speed"},
    {"id": "slowmo", "name": "Slow Motion", "description": "Slow down key moments"},
    {"id": "speedup", "name": "Speed Up", "description": "Accelerate through filler"},
    {"id": "punch", "name": "Punch Effect", "description": "Quick slow → fast for impact"},
]

ANIMATIONS = [
    {"id": "pop", "name": "Pop", "description": "Words pop in one by one"},
    {"id": "bounce", "name": "Bounce", "description": "Words bounce in with spring"},
    {"id": "fade", "name": "Fade", "description": "Gentle fade in"},
    {"id": "fade_slow", "name": "Fade Slow", "description": "Slow cinematic fade"},
    {"id": "typewriter", "name": "Typewriter", "description": "Character-by-character"},
    {"id": "flicker", "name": "Flicker", "description": "Glitchy flicker effect"},
    {"id": "slow_reveal", "name": "Slow Reveal", "description": "Slow mask reveal"},
]

POSITIONS = [
    {"id": "top", "name": "Top", "description": "Top of screen"},
    {"id": "center", "name": "Center", "description": "Middle of screen"},
    {"id": "bottom", "name": "Bottom", "description": "Bottom of screen"},
    {"id": "random", "name": "Random", "description": "Varying positions"},
]


# ── Endpoints ──

@router.get("/templates")
async def list_templates():
    """List all creator template presets available in the editor."""
    return {"templates": CREATOR_TEMPLATES, "count": len(CREATOR_TEMPLATES)}


@router.get("/styles")
async def list_styles():
    """List all subtitle style presets (30+ styles)."""
    styles = []
    for key, preset in STYLE_PRESETS.items():
        styles.append({
            "id": key,
            "name": key.replace("_", " ").title(),
            "font": preset.get("font", "Arial"),
            "font_size": preset.get("font_size", 48),
            "primary": preset.get("primary", "#FFFFFF"),
            "highlight": preset.get("highlight", "#FFD700"),
            "position": preset.get("position", "center"),
            "animation": preset.get("animation", "pop"),
        })
    return {"styles": styles, "count": len(styles)}


@router.get("/effects")
async def list_effects():
    """List all available visual effects for personalization."""
    return {
        "zoom_styles": ZOOM_STYLES,
        "color_grades": COLOR_GRADES_LIST,
        "speed_ramp_types": SPEED_RAMP_TYPES,
        "animations": ANIMATIONS,
        "positions": POSITIONS,
        "aspect_ratios": [{"id": k, "name": k, "w": v[0], "h": v[1]} for k, v in ASPECT_RATIOS.items()],
    }


@router.get("/clip/{job_id}/{clip_idx}")
async def get_clip_details(job_id: str, clip_idx: int):
    """Get detailed information about a specific clip for the editor."""
    import sqlite3
    DB_PATH = Path(os.environ.get("NEXUX_DB_PATH", "nexux_jobs.db"))
    
    if not DB_PATH.exists():
        raise HTTPException(404, "Database not found")
    
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(404, "Job not found")
    
    clips = json.loads(row["clips"] or "[]")
    if clip_idx >= len(clips):
        raise HTTPException(404, f"Clip {clip_idx} not found (only {len(clips)} clips)")
    
    clip_url = clips[clip_idx]
    render_meta = json.loads(row["render_meta"] or "[]")
    analysis_bundle = json.loads(row["analysis_bundle"]) if row["analysis_bundle"] else None
    
    clip_meta = render_meta[clip_idx] if clip_idx < len(render_meta) else {}
    
    return {
        "job_id": job_id,
        "clip_index": clip_idx,
        "clip_url": clip_url,
        "render_meta": clip_meta,
        "analysis": analysis_bundle,
        "duration": clip_meta.get("duration", 45),
        "transcript": clip_meta.get("transcript", []),
    }


@router.post("/preview/{job_id}/{clip_idx}")
async def preview_render(
    job_id: str,
    clip_idx: int,
    req: PreviewRequest,
):
    """
    Quick preview render (first 5 seconds only).
    Returns a preview URL that can be displayed in the editor.
    """
    from .engine.preview_renderer import generate_preview
    
    try:
        result = await asyncio.to_thread(
            generate_preview,
            job_id, clip_idx,
            style_name=req.subtitle_style,
            zoom_style=req.zoom_style,
            color_grade=req.color_grade,
            aspect_ratio=req.aspect_ratio,
            preview_duration=req.preview_duration,
        )
        return {
            "preview_url": result.preview_url if hasattr(result, 'preview_url') else str(result),
            "render_time": result.render_time if hasattr(result, 'render_time') else 0,
        }
    except Exception as e:
        log.error(f"[Editor] Preview render failed: {e}")
        raise HTTPException(500, f"Preview render failed: {str(e)}")


@router.post("/rerender/{job_id}/{clip_idx}")
async def rerender_clip(
    job_id: str,
    clip_idx: int,
    req: PersonalizationRequest,
):
    """
    Full re-render of a single clip with personalized settings.
    
    This is the main endpoint that powers the post-render editor.
    Takes all personalization settings and produces a new rendered clip.
    """
    from .engine.rerender_pipeline import rerender_clip_with_personalization
    
    # If template_id is set, apply template settings
    if req.template_id:
        template = next((t for t in CREATOR_TEMPLATES if t["id"] == req.template_id), None)
        if template:
            req.subtitle_style = template.get("style_id", req.subtitle_style)
            req.zoom_style = template.get("zoom_style", req.zoom_style)
            req.color_grade = template.get("color_grade", req.color_grade)
            req.speed_ramp = template.get("speed_ramp", req.speed_ramp)
            req.speed_ramp_type = template.get("speed_ramp_type", req.speed_ramp_type)
            log.info(f"[Editor] Applied template '{req.template_id}' for clip {clip_idx}")
    
    try:
        result = await asyncio.to_thread(
            rerender_clip_with_personalization,
            job_id, clip_idx,
            subtitle_style=req.subtitle_style,
            font=req.font,
            font_size=req.font_size,
            primary_color=req.primary_color,
            highlight_color=req.highlight_color,
            stroke_color=req.stroke_color,
            stroke_width=req.stroke_width,
            position=req.position,
            animation=req.animation,
            highlight_words=req.highlight_words,
            zoom_style=req.zoom_style,
            zoom_level=req.zoom_level,
            color_grade=req.color_grade,
            speed_ramp=req.speed_ramp,
            speed_ramp_type=req.speed_ramp_type,
            aspect_ratio=req.aspect_ratio,
            auto_reframe=req.auto_reframe,
            face_tracking=req.face_tracking,
            bgm_volume=req.bgm_volume,
            voice_volume=req.voice_volume,
            normalize_audio=req.normalize_audio,
            bass_boost=req.bass_boost,
            sfx_enabled=req.sfx_enabled,
            watermark_text=req.watermark_text,
            watermark_position=req.watermark_position,
            show_watermark=req.show_watermark,
            trim_start=req.trim_start,
            trim_end=req.trim_end if req.trim_end > 0 else None,
            overlays=req.overlays,
        )
        
        return {
            "status": "completed",
            "clip_index": clip_idx,
            "output_url": result.get("output_url", ""),
            "changes_applied": _summarize_changes(req),
        }
    except Exception as e:
        log.error(f"[Editor] Re-render failed: {e}")
        raise HTTPException(500, f"Re-render failed: {str(e)}")


@router.post("/rerender/{job_id}/all")
async def rerender_all_clips(
    job_id: str,
    req: PersonalizationRequest,
):
    """Batch re-render all clips in a job with the same personalization settings."""
    from .engine.rerender_pipeline import rerender_all_clips
    
    # Apply template if set
    if req.template_id:
        template = next((t for t in CREATOR_TEMPLATES if t["id"] == req.template_id), None)
        if template:
            req.subtitle_style = template.get("style_id", req.subtitle_style)
            req.zoom_style = template.get("zoom_style", req.zoom_style)
            req.color_grade = template.get("color_grade", req.color_grade)
            req.speed_ramp = template.get("speed_ramp", req.speed_ramp)
            req.speed_ramp_type = template.get("speed_ramp_type", req.speed_ramp_type)
    
    try:
        result = await asyncio.to_thread(
            rerender_all_clips,
            job_id,
            subtitle_style=req.subtitle_style,
            zoom_style=req.zoom_style,
            color_grade=req.color_grade,
            aspect_ratio=req.aspect_ratio,
            auto_reframe=req.auto_reframe,
        )
        
        return {
            "status": "completed",
            "clips_rendered": result.get("count", 0),
            "output_urls": result.get("urls", []),
            "changes_applied": _summarize_changes(req),
        }
    except Exception as e:
        log.error(f"[Editor] Batch re-render failed: {e}")
        raise HTTPException(500, f"Batch re-render failed: {str(e)}")


@router.get("/clip/{job_id}/{clip_idx}/transcript")
async def get_clip_transcript(job_id: str, clip_idx: int):
    """Get the transcript for a specific clip (for the transcript panel in editor)."""
    import sqlite3
    DB_PATH = Path(os.environ.get("NEXUX_DB_PATH", "nexux_jobs.db"))
    
    if not DB_PATH.exists():
        raise HTTPException(404, "Database not found")
    
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(404, "Job not found")
    
    analysis_bundle = json.loads(row["analysis_bundle"]) if row["analysis_bundle"] else None
    render_meta = json.loads(row["render_meta"] or "[]")
    
    clip_meta = render_meta[clip_idx] if clip_idx < len(render_meta) else {}
    transcript = clip_meta.get("transcript", [])
    
    # Format transcript for the editor UI
    segments = []
    for seg in transcript:
        segments.append({
            "id": seg.get("id", f"seg-{len(segments)}"),
            "speaker": seg.get("speaker", "SPEAKER_00"),
            "start": seg.get("start", 0),
            "end": seg.get("end", 0),
            "text": seg.get("text", ""),
            "words": seg.get("words", []),
        })
    
    return {
        "job_id": job_id,
        "clip_index": clip_idx,
        "segments": segments,
        "total_segments": len(segments),
    }


# ── Helpers ──

def _summarize_changes(req: PersonalizationRequest) -> List[str]:
    """Generate a human-readable list of changes applied."""
    changes = []
    if req.template_id:
        changes.append(f"Template: {req.template_id}")
    changes.append(f"Subtitle: {req.subtitle_style}")
    if req.zoom_style != "subtle":
        changes.append(f"Zoom: {req.zoom_style}")
    if req.color_grade != "none":
        changes.append(f"Color: {req.color_grade}")
    if req.speed_ramp:
        changes.append(f"Speed ramp: {req.speed_ramp_type}")
    if req.aspect_ratio != "9:16":
        changes.append(f"Aspect: {req.aspect_ratio}")
    if req.show_watermark:
        changes.append(f"Watermark: {req.watermark_text}")
    if req.trim_start > 0 or req.trim_end > 0:
        changes.append(f"Trim: {req.trim_start}s - {req.trim_end}s")
    return changes
