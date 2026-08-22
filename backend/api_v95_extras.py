"""
NexuX V9.5 — Extras API (Analysis, Platforms, Repair, Legacy Re-render)
========================================================================
Restores the V8.5/V9.0 endpoint surface as a proper FastAPI router
(replaces the removed `_integrate_api.py` exec-loader):

GET  /api/virality/{job_id}                  → 8-dimension virality scores per clip
GET  /api/hooks/{job_id}                     → hook detection per clip
GET  /api/caption-quality/{job_id}           → caption quality report per clip
GET  /api/reframe/{job_id}                   → auto-reframe data per clip
GET  /api/clips/{job_id}/{idx}/retention     → per-second retention heatmap (V9.6)
GET  /api/clips/{job_id}/{idx}/hook-lab      → hook variants + title CTR (V9.6)
POST /api/title-ctr                          → transparent CTR prediction for any title (V9.6)
GET  /api/platforms                          → supported publish platforms
GET  /api/repair/diagnose                    → self-healing diagnostics
POST /api/repair/fix-all                     → auto-fix all detected issues
POST /api/preview-render/{job_id}/{idx}      → real-time FFmpeg preview (legacy shape)
POST /api/rerender/{job_id}/{idx}            → re-render with personalization (legacy shape)
POST /api/rerender/{job_id}/{idx}/overlays   → re-render with overlay burn-in
"""
import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

log = logging.getLogger("nexus.api.extras")

router = APIRouter(prefix="/api", tags=["extras"])


# ── Shared job lookup (same storage contract as main.py / api_v95_editor.py) ──

def _load_job(job_id: str) -> Dict[str, Any]:
    db_path = Path(os.environ.get("NEXUX_DB_PATH", "nexux_jobs.db"))
    if not db_path.exists():
        raise HTTPException(404, "Job database not found")

    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(404, "Job not found")

    return {
        "job_id": row["job_id"],
        "status": row["status"],
        "clips": json.loads(row["clips"] or "[]"),
        "render_meta": json.loads(row["render_meta"] or "[]"),
        "analysis_bundle": json.loads(row["analysis_bundle"]) if row["analysis_bundle"] else None,
        "output_path": row["output_path"] if "output_path" in row.keys() else None,
    }


def _clip_windows(job: Dict[str, Any]) -> List[Dict[str, float]]:
    """Best-effort clip start/end windows from analysis_bundle."""
    bundle = job.get("analysis_bundle") or {}
    candidates = bundle.get("clip_candidates") or []
    windows = []
    for c in candidates:
        try:
            windows.append({"start": float(c["start"]), "end": float(c["end"])})
        except (KeyError, TypeError, ValueError):
            continue
    return windows


def _resolve_clip_path(job: Dict[str, Any], clip_idx: int) -> Path:
    """Resolve the rendered clip file for preview/re-render."""
    clips = job.get("clips") or []
    candidates: List[Path] = []
    if clip_idx < len(clips):
        candidates.append(Path(clips[clip_idx]))
    out_dir = Path(os.environ.get("NEXUX_OUTPUT_DIR", "output"))
    candidates += [
        out_dir / job["job_id"] / f"clip_{clip_idx:02d}.mp4",
        out_dir / job["job_id"] / f"clip_{clip_idx}.mp4",
        out_dir / f"{job['job_id']}_clip_{clip_idx}.mp4",
    ]
    if job.get("output_path"):
        candidates.append(Path(job["output_path"]))

    for path in candidates:
        p = path if path.is_absolute() else Path.cwd() / path
        if p.exists():
            return p
    raise HTTPException(404, f"Clip file for index {clip_idx} not found on disk")


# ── Analysis endpoints ──

@router.get("/virality/{job_id}")
async def get_virality(job_id: str):
    """8-dimension virality scores for every clip in the job."""
    from engine.virality_score import score_batch, score_to_api_dict

    job = _load_job(job_id)
    bundle = job.get("analysis_bundle") or {}
    segments = bundle.get("transcript_segments") or []
    clips = _clip_windows(job)

    if not segments or not clips:
        raise HTTPException(409, "Job has no transcript/clip analysis data yet")

    full_duration = max((s.get("end", 0) for s in segments), default=0)
    transcript = {"segments": segments}
    ranked = score_batch(clips, transcript, full_duration)

    return {
        "job_id": job_id,
        "clips": [
            {
                "clip_index": i,
                "start": round(clip["start"], 2),
                "end": round(clip["end"], 2),
                **score_to_api_dict(score),
            }
            for i, (clip, score) in enumerate(ranked)
        ],
        "count": len(ranked),
    }


@router.get("/hooks/{job_id}")
async def get_hooks(job_id: str):
    """Hook detection results for every clip in the job."""
    from engine.hook_detection import detect_best_hook, hook_to_api_dict

    job = _load_job(job_id)
    bundle = job.get("analysis_bundle") or {}
    segments = bundle.get("transcript_segments") or []
    clips = _clip_windows(job)

    if not segments or not clips:
        raise HTTPException(409, "Job has no transcript/clip analysis data yet")

    results = []
    for i, clip in enumerate(clips):
        hook = detect_best_hook(segments, clip["start"], clip["end"])
        results.append({"clip_index": i, **hook_to_api_dict(hook)})

    return {"job_id": job_id, "hooks": results, "count": len(results)}


@router.get("/clips/{job_id}/{clip_idx}/retention")
async def get_retention_heatmap(job_id: str, clip_idx: int):
    r"""Per-second retention heatmap for one clip (V9.6 — Beyond Opus)."""
    from engine.retention_heatmap import predict_retention_curve
    from engine.hook_detection import detect_best_hook

    job = _load_job(job_id)
    bundle = job.get("analysis_bundle") or {}
    segments = bundle.get("transcript_segments") or []
    clips = _clip_windows(job)

    if not segments or not clips:
        raise HTTPException(409, "Job has no transcript/clip analysis data yet")
    if clip_idx < 0 or clip_idx >= len(clips):
        raise HTTPException(404, f"Clip index {clip_idx} out of range")

    clip = clips[clip_idx]
    transcript = {"segments": segments}
    hook = detect_best_hook(segments, clip["start"], clip["end"])
    raw = getattr(hook, "hook_score", 0) if hook else 0
    hook_strength = (raw / 100.0) if raw else 0.5

    heatmap = predict_retention_curve(
        clip, transcript, hook_strength=hook_strength)
    return {"job_id": job_id, "clip_index": clip_idx, **heatmap}


@router.get("/clips/{job_id}/{clip_idx}/hook-lab")
async def get_hook_lab(job_id: str, clip_idx: int, n: int = 5):
    r"""Hook variants with scores/archetypes + CTR prediction lab (V9.6)."""
    from engine.hook_lab import generate_hook_variants

    job = _load_job(job_id)
    bundle = job.get("analysis_bundle") or {}
    segments = bundle.get("transcript_segments") or []
    clips = _clip_windows(job)

    if not segments or not clips:
        raise HTTPException(409, "Job has no transcript/clip analysis data yet")
    if clip_idx < 0 or clip_idx >= len(clips):
        raise HTTPException(404, f"Clip index {clip_idx} out of range")

    clip = clips[clip_idx]
    transcript = {"segments": segments}
    variants = generate_hook_variants(
        clip, transcript, n=max(1, min(n, 10)))

    return {
        "job_id": job_id,
        "clip_index": clip_idx,
        "variants": variants,
        "count": len(variants),
    }


class TitleCtrRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    clip_text: str = Field("", max_length=5000)


@router.post("/title-ctr")
async def post_title_ctr(req: TitleCtrRequest):
    r"""Predict relative CTR for any title string (V9.6).

    Job-agnostic: works before/without a job so the editor can score
    candidate titles live while typing.
    """
    from engine.hook_lab import predict_title_ctr

    return predict_title_ctr(req.title, clip_text=req.clip_text)


@router.get("/caption-quality/{job_id}")
async def get_caption_quality(job_id: str):
    """Caption quality report for each clip's transcript segment groups."""
    from engine.caption_engine_v2 import score_caption_quality

    job = _load_job(job_id)
    bundle = job.get("analysis_bundle") or {}
    segments = bundle.get("transcript_segments") or []
    clips = _clip_windows(job)

    if not segments or not clips:
        raise HTTPException(409, "Job has no transcript/clip analysis data yet")

    reports = []
    for i, clip in enumerate(clips):
        groups = [
            s for s in segments
            if s.get("start", 0) < clip["end"] and s.get("end", 0) > clip["start"]
        ]
        report = score_caption_quality(groups, {}, style_name=None)
        reports.append({"clip_index": i, **report})

    return {"job_id": job_id, "reports": reports, "count": len(reports)}


@router.get("/reframe/{job_id}")
async def get_reframe(job_id: str):
    """Auto-reframe crop instructions per clip (from stored render metadata)."""
    job = _load_job(job_id)
    render_meta = job.get("render_meta") or []

    frames = []
    for i, meta in enumerate(render_meta):
        reframe = meta.get("reframe") or (meta.get("render") or {}).get("reframe")
        if reframe:
            frames.append({"clip_index": i, "reframe": reframe})

    if not frames:
        raise HTTPException(409, "No reframe data stored for this job")

    return {"job_id": job_id, "clips": frames, "count": len(frames)}


# ── Platforms ──

@router.get("/platforms")
async def get_platforms():
    """List all supported publish platforms with their specs."""
    from engine.autopost_engine import list_platforms

    return {"platforms": list_platforms()}


# ── Repair / self-healing ──

@router.get("/repair/diagnose")
async def repair_diagnose():
    """Run the full self-healing diagnostic suite."""
    from engine.repair_system import run_full_diagnosis

    results = run_full_diagnosis()
    issues = [
        {
            "id": r.id,
            "label": r.label,
            "status": r.status,
            "detail": r.detail,
        }
        for r in results
    ]
    return {"issues": issues, "count": len(issues)}


@router.post("/repair/fix-all")
async def repair_fix_all():
    """Attempt to auto-fix every detected issue."""
    from engine.repair_system import fix_all

    results = fix_all()
    fixed = [r for r in results if r.status == "fixed"]
    return {
        "fixed": len(fixed),
        "results": [
            {
                "id": r.id,
                "label": r.label,
                "status": r.status,
                "detail": r.detail,
            }
            for r in results
        ],
    }


# ── Legacy preview / re-render surface (kept for existing frontend clients) ──

class PreviewRenderRequest(BaseModel):
    editor_state: Dict[str, Any] = Field(default_factory=dict)
    current_time: float = 0.0


class RerenderRequest(BaseModel):
    settings: Dict[str, Any] = Field(default_factory=dict)


class OverlayRerenderRequest(BaseModel):
    settings: Dict[str, Any] = Field(default_factory=dict)
    overlays: List[Dict[str, Any]] = Field(default_factory=list)


@router.post("/preview-render/{job_id}/{clip_idx}")
async def preview_render_legacy(job_id: str, clip_idx: int, req: PreviewRenderRequest):
    """Real-time FFmpeg preview (480p, 5s) — legacy response shape."""
    import asyncio
    from engine.preview_renderer import generate_preview

    job = _load_job(job_id)
    source = _resolve_clip_path(job, clip_idx)

    result = await asyncio.to_thread(
        generate_preview, job_id, clip_idx, req.editor_state, source, req.current_time,
    )
    if not result.success:
        raise HTTPException(500, result.error or "Preview render failed")

    return {
        "preview_url": result.preview_url,
        "render_time": round(result.render_time, 2),
    }


@router.post("/rerender/{job_id}/{clip_idx}")
async def rerender_clip_legacy(job_id: str, clip_idx: int, req: RerenderRequest):
    """Re-render a clip with personalization settings — legacy response shape."""
    import asyncio
    from engine.rerender_pipeline import rerender_clip_with_personalization

    job = _load_job(job_id)
    source = _resolve_clip_path(job, clip_idx)

    result = await asyncio.to_thread(
        rerender_clip_with_personalization,
        job, clip_idx, req.settings, source,
    )
    if result.get("status") != "success":
        raise HTTPException(500, result.get("error") or "Re-render failed")

    return {
        "status": "success",
        "output_url": result.get("output_url") or result.get("output_path"),
        "changes_applied": result.get("changes_applied", []),
    }


@router.post("/rerender/{job_id}/{clip_idx}/overlays")
async def rerender_with_overlays(job_id: str, clip_idx: int, req: OverlayRerenderRequest):
    """Re-render a clip with draggable overlay elements burned in."""
    import asyncio
    from engine.rerender_pipeline import rerender_clip_with_personalization

    job = _load_job(job_id)
    source = _resolve_clip_path(job, clip_idx)

    result = await asyncio.to_thread(
        rerender_clip_with_personalization,
        job, clip_idx, req.settings, source,
        None, None, req.overlays,
    )
    if result.get("status") != "success":
        raise HTTPException(500, result.get("error") or "Overlay re-render failed")

    return {
        "status": "success",
        "output_url": result.get("output_url") or result.get("output_path"),
        "changes_applied": result.get("changes_applied", []) + ["overlays_burned_in"],
    }
