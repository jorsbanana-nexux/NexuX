"""
NexuX V8.0 — Self-Healing Engine
===================================
Auto-detects and fixes errors in the pipeline without user intervention.

When something fails, the healer:
1. Diagnoses the root cause
2. Applies a fix from the remediation playbook
3. Retries with adjusted parameters
4. Logs the issue for future prevention
5. Falls back gracefully if all retries fail

This is what makes NexuX reliable — it doesn't just crash, it heals.
"""
import subprocess
import json
import time
import os
import shutil
from pathlib import Path
from typing import Dict, Optional, Callable, List, Tuple, Any
from logging import getLogger

from .constants import OUTPUT_DIR

log = getLogger("nexus.healer")


# ── Remediation Playbook ──

PLAYBOOK = {
    "yt_dlp_download_failed": {
        "fixes": [
            {"action": "retry_with_lower_quality", "max_height": 720},
            {"action": "retry_with_different_format", "format": "best[height<=480]"},
            {"action": "retry_with_cookies", "cookies_arg": "--cookies-from-browser"},
            {"action": "retry_with_proxy", "proxy": None},
        ],
    },
    "ffmpeg_render_failed": {
        "fixes": [
            {"action": "simplify_filters", "remove": ["zoompan", "color_grade"]},
            {"action": "reduce_resolution", "scale": 0.75},
            {"action": "change_codec", "codec": "libx264", "preset": "ultrafast"},
            {"action": "bare_render", "filters": []},
        ],
    },
    "whisper_model_load_failed": {
        "fixes": [
            {"action": "smaller_model", "model_size": "medium"},
            {"action": "smaller_model", "model_size": "small"},
            {"action": "smaller_model", "model_size": "base"},
            {"action": "use_cpu", "device": "cpu"},
        ],
    },
    "subtitle_render_failed": {
        "fixes": [
            {"action": "simplify_subtitle", "style": "simple"},
            {"action": "disable_animation", "animation": "none"},
            {"action": "burn_subtitles_basic", "font": "Arial", "size": 24},
        ],
    },
    "no_audio_track": {
        "fixes": [
            {"action": "add_silent_audio"},
            {"action": "extract_audio_separately"},
        ],
    },
    "corrupt_video": {
        "fixes": [
            {"action": "reencode_video"},
            {"action": "use_different_downloader"},
        ],
    },
    "timeout": {
        "fixes": [
            {"action": "increase_timeout", "multiplier": 2},
            {"action": "reduce_quality", "max_height": 720},
            {"action": "split_into_chunks"},
        ],
    },
    "out_of_memory": {
        "fixes": [
            {"action": "reduce_resolution", "scale": 0.5},
            {"action": "disable_vision", "skip": ["face", "scene", "screen"]},
            {"action": "process_one_at_a_time"},
        ],
    },
}


# ── Error Log (persistent) ──

ERROR_LOG = OUTPUT_DIR / "healer_log.json"


def _load_error_log() -> List[Dict]:
    try:
        if ERROR_LOG.exists():
            with open(ERROR_LOG, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []


def _save_error_log(logs: List[Dict]):
    try:
        if len(logs) > 100:
            logs = logs[-100:]
        with open(ERROR_LOG, "w") as f:
            json.dump(logs, f, indent=2)
    except Exception:
        pass


def _log_error(
    error_type: str,
    error_msg: str,
    fix_applied: Optional[str] = None,
    success: bool = False,
):
    """Log an error and its fix for future reference."""
    logs = _load_error_log()
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "type": error_type,
        "error": error_msg[:500],
        "fix": fix_applied,
        "success": success,
    }
    logs.append(entry)
    _save_error_log(logs)


def diagnose_error(error: Exception, context: str = "") -> str:
    """Diagnose the root cause of an error and return an error type key."""
    msg = str(error).lower()
    
    if "yt-dlp" in msg or "download" in context.lower() and "failed" in msg:
        return "yt_dlp_download_failed"
    if "ffmpeg" in msg or "render" in context.lower():
        if "timeout" in msg:
            return "timeout"
        if "memory" in msg or "oom" in msg:
            return "out_of_memory"
        if "subtitle" in msg or "ass" in msg:
            return "subtitle_render_failed"
        return "ffmpeg_render_failed"
    if "whisper" in msg or "model" in msg and "load" in msg:
        return "whisper_model_load_failed"
    if "no audio" in msg or "audio" in msg and "not found" in msg:
        return "no_audio_track"
    if "corrupt" in msg or "invalid" in msg and "data" in msg:
        return "corrupt_video"
    if "timeout" in msg or "timed out" in msg:
        return "timeout"
    
    return "unknown"


def heal(
    error: Exception,
    context: str,
    retry_fn: Callable,
    current_params: Dict,
) -> Tuple[Optional[any], Dict]:
    """Try to heal an error by applying fixes from the playbook.
    
    Args:
        error: The exception that occurred
        context: Context string (e.g., "download", "render", "transcribe")
        retry_fn: Function to retry after applying fix
        current_params: Current parameters being used
    
    Returns:
        (result, updated_params) if healed, (None, current_params) if not
    """
    error_type = diagnose_error(error, context)
    playbook = PLAYBOOK.get(error_type, {})
    fixes = playbook.get("fixes", [])
    
    log.warning(f"[Healer] Error type: {error_type} | Context: {context} | Fixes: {len(fixes)}")
    
    for i, fix in enumerate(fixs := fixes):
        fix_name = fix.get("action", "unknown")
        log.info(f"[Healer] Attempting fix {i+1}/{len(fixes)}: {fix_name}")
        
        # Apply fix to parameters
        updated_params = current_params.copy()
        updated_params.update(fix)
        updated_params["_healer_attempt"] = i + 1
        
        try:
            result = retry_fn(**updated_params)
            _log_error(error_type, str(error), fix_name, success=True)
            log.info(f"[Healer] Fix '{fix_name}' SUCCEEDED ✅")
            return result, updated_params
        except Exception as e:
            log.warning(f"[Healer] Fix '{fix_name}' failed: {e}")
            _log_error(error_type, str(e), fix_name, success=False)
            continue
    
    # All fixes failed — try ultimate fallback
    log.error(f"[Healer] All {len(fixes)} fixes failed for {error_type}")
    _log_error(error_type, str(error), "all_fixes_failed", success=False)
    return None, current_params


def check_system_health() -> Dict:
    """Check system health: ffmpeg, yt-dlp, disk space, etc."""
    health = {"healthy": True, "issues": []}
    
    # Check ffmpeg
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            health["healthy"] = False
            health["issues"].append("ffmpeg not working")
    except FileNotFoundError:
        health["healthy"] = False
        health["issues"].append("ffmpeg not found")
    except Exception:
        health["healthy"] = False
        health["issues"].append("ffmpeg check failed")
    
    # Check yt-dlp
    try:
        r = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            health["healthy"] = False
            health["issues"].append("yt-dlp not working")
    except FileNotFoundError:
        health["healthy"] = False
        health["issues"].append("yt-dlp not found")
    except Exception:
        health["healthy"] = False
        health["issues"].append("yt-dlp check failed")
    
    # Check disk space (need at least 1GB free)
    try:
        stat = os.statvfs(str(OUTPUT_DIR))
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        if free_gb < 1.0:
            health["healthy"] = False
            health["issues"].append(f"Low disk space: {free_gb:.1f} GB free")
        health["disk_free_gb"] = round(free_gb, 1)
    except Exception:
        pass
    
    # Check Python packages
    try:
        import fastapi
        import pydantic
    except ImportError as e:
        health["healthy"] = False
        health["issues"].append(f"Missing Python package: {e}")
    
    return health


def auto_cleanup_old_jobs(max_age_hours: int = 24):
    """Automatically clean up old job directories to free disk space."""
    now = time.time()
    max_age_seconds = max_age_hours * 3600
    
    cleaned = 0
    try:
        for job_dir in OUTPUT_DIR.iterdir():
            if not job_dir.is_dir():
                continue
            # Skip non-job directories
            if job_dir.name in ["creative_memory.json", "healer_log.json"]:
                continue
            
            mtime = job_dir.stat().st_mtime
            if now - mtime > max_age_seconds:
                shutil.rmtree(job_dir, ignore_errors=True)
                cleaned += 1
                log.info(f"[Healer] Cleaned up old job: {job_dir.name}")
    except Exception as e:
        log.warning(f"[Healer] Cleanup failed: {e}")
    
    if cleaned:
        log.info(f"[Healer] Auto-cleanup: removed {cleaned} old job(s)")
    return cleaned


