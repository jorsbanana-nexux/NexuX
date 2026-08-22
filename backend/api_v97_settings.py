"""
NexuX V9.7 — Settings API
=============================
Backend for the Settings page (top-right of the new UI).
- GET    /api/settings           → read current persistent settings
- PATCH  /api/settings           → update (persisted to JSON store)
- GET    /api/settings/models    → list the 3 curated WhisperX variants
                                   with download state (model cache)
- POST   /api/settings/models/preload → download a WhisperX model ahead of time
- DELETE /api/settings/reset     → restore defaults

Design rules:
- Model preload runs in a BackgroundTask so the UI shows progress.
- All writes are validated against settings_store defaults (unknown keys → 400).
- WhisperX is imported lazily inside the background task (never here).
"""
import os
import sys
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from utils import settings_store

router = APIRouter(prefix="/api/settings", tags=["settings"])
log = logging.getLogger("nexus.settings")

# Loading-id → {status, message} for preload progress polling.
_preload_jobs: Dict[str, Dict[str, Any]] = {}


class SettingsPatch(BaseModel):
    transcription_model: Optional[str] = None
    language: Optional[str] = None
    diarization: Optional[bool] = None
    batch_size: Optional[int] = None
    word_timestamps: Optional[bool] = None
    proxy_url: Optional[str] = None
    player_clients: Optional[str] = None
    auto_update_ytdlp: Optional[bool] = None


@router.get("")
def get_settings() -> Dict[str, Any]:
    return {
        "settings": settings_store.all_settings(),
        "variants": settings_store.MODEL_VARIANTS,
        "env": {
            "HF_TOKEN_set": bool(os.environ.get("HF_TOKEN")),
            "has_gpu": shutil.which("nvidia-smi") is not None,
        },
    }


@router.patch("")
def update_settings(patch: SettingsPatch) -> Dict[str, Any]:
    updates = {k: v for k, v in patch.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No settings provided")
    try:
        merged = settings_store.set_settings(updates)
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))
    except IOError as e:
        raise HTTPException(500, str(e))
    return {"ok": True, "settings": merged}


def _whisperx_installed() -> bool:
    try:
        __import__("whisperx")
        return True
    except ImportError:
        return False


def _model_cached(variant: str) -> bool:
    """Check the faster-whisper/WhisperX cache for the model weights."""
    cache = Path(os.environ.get("HF_HOME", str(Path.home() / ".cache" / "huggingface")))
    hub = cache / "hub"
    if not hub.exists():
        return False
    needle = variant.lower().replace("-", "")
    for repo in hub.iterdir():
        name = repo.name.lower().replace("-", "")
        if needle in name and ("whisper" in name or "fasterwhisper" in name):
            return True
    return False


@router.get("/models")
def list_models() -> Dict[str, Any]:
    installed = _whisperx_installed()
    models = []
    for key, meta in settings_store.MODEL_VARIANTS.items():
        models.append({
            "id": key,
            **meta,
            "downloaded": _model_cached(key) if installed else False,
            "active": settings_store.get("transcription_model") == key,
        })
    return {
        "whisperx_installed": installed,
        "models": models,
        "preload": _preload_jobs,
    }


def _preload_worker(variant: str, job_id: str) -> None:
    _preload_jobs[job_id] = {"status": "downloading", "variant": variant, "message": "Starting..."}
    try:
        import whisperx  # lazy — only inside worker
        from engine.utils import get_device

        device = "cpu"  # Preload safely on CPU even on GPU machines
        compute = "int8"
        _preload_jobs[job_id]["message"] = f"Downloading {variant}..."
        log.info(f"[Settings] Preloading WhisperX {variant}...")
        whisperx.load_model(variant, device=device, compute_type=compute)
        _preload_jobs[job_id] = {
            "status": "done", "variant": variant,
            "message": f"{variant} ready",
        }
        log.info(f"[Settings] WhisperX {variant} preloaded ✅")
    except Exception as e:
        _preload_jobs[job_id] = {
            "status": "error", "variant": variant,
            "message": str(e)[:300],
        }
        log.warning(f"[Settings] Preload failed for {variant}: {e}")


class PreloadRequest(BaseModel):
    variant: str
    install_whisperx: bool = False


@router.post("/models/preload")
def preload_model(req: PreloadRequest, background: BackgroundTasks) -> Dict[str, Any]:
    if req.variant not in settings_store.MODEL_VARIANTS:
        raise HTTPException(400, f"Unknown variant: {req.variant}")

    if not _whisperx_installed():
        if not req.install_whisperx:
            raise HTTPException(
                409,
                "WhisperX is not installed. Re-request with install_whisperx=true "
                "to install it first (this can take a few minutes).",
            )
        log.info("[Settings] Installing whisperx package...")
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "whisperx>=3.1"],
            capture_output=True, text=True, timeout=900,
        )
        if r.returncode != 0:
            raise HTTPException(500, f"whisperx install failed: {r.stderr[-300:]}")
        log.info("[Settings] whisperx installed ✅")

    job_id = f"preload_{req.variant}"
    background.add_task(_preload_worker, req.variant, job_id)
    return {"ok": True, "job": job_id, "variant": req.variant}


@router.get("/models/preload/{job_id}")
def preload_status(job_id: str) -> Dict[str, Any]:
    job = _preload_jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Unknown preload job")
    return job


@router.delete("/reset")
def reset_settings() -> Dict[str, Any]:
    merged = settings_store.set_settings(dict(settings_store.DEFAULT_SETTINGS))
    return {"ok": True, "settings": merged}
