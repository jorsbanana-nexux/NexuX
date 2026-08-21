"""
NexuX V9.5 — Core Utilities
============================================
Path normalization, FFmpeg helpers, retry logic, JSON cleaning.
"""
import os, math, time, shutil, subprocess
from pathlib import Path
from typing import Any
from functools import lru_cache
import logging

log = logging.getLogger("nexus.utils")

# ── Path Helpers ────────────────────────────────────
def to_unix(p) -> str:
    """Normalize any path to unix‑style string."""
    return str(p).replace("\\", "/")

def rel_path(p) -> str:
    """Get unix‑style relative path from cwd. Falls back to absolute."""
    p_str = to_unix(p)
    cwd_str = to_unix(Path.cwd())
    try:
        return str(Path(p_str).relative_to(Path(cwd_str))).replace("\\", "/")
    except ValueError:
        return p_str

# ── Time Formatting ─────────────────────────────────
def fmt_time(seconds: float) -> str:
    """Format seconds to HH:MM:SS.cs (ASS/FFmpeg format)."""
    s = max(0, seconds)
    h = int(s // 3600)
    m = int((s % 3600) // 60)
    sec = int(s % 60)
    cs = int((s % 1) * 100)
    return f"{h}:{m:02d}:{sec:02d}.{cs:02d}"

def fmt_duration(seconds: float) -> str:
    """Human-readable duration like '2m 35s'."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"

# ── Retry Logic ─────────────────────────────────────
def retry(func, *args, max_retries: int = 3, **kwargs):
    """Execute function with exponential backoff retry."""
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                wait = 2 ** attempt
                log.warning(f"Retry {attempt}/{max_retries}: {e}. Waiting {wait}s...")
                time.sleep(wait)
    raise RuntimeError(f"All {max_retries} retries failed. Last error: {last_err}")

# ── JSON Cleaning ───────────────────────────────────
def clean_for_json(obj: Any) -> Any:
    """Recursively replace NaN/Inf with 0.0 for JSON serialization."""
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return 0.0
    return obj

# ── FFmpeg Detection ────────────────────────────────
@lru_cache(maxsize=1)
def get_ffmpeg() -> str:
    """Find FFmpeg binary. Raises RuntimeError if not found."""
    path = shutil.which("ffmpeg")
    if not path:
        raise RuntimeError("FFmpeg not found! Install: apt install ffmpeg")
    return path

@lru_cache(maxsize=1)
def get_ffprobe() -> str:
    """Find FFprobe binary."""
    path = shutil.which("ffprobe")
    if not path:
        raise RuntimeError("FFprobe not found! Install: apt install ffmpeg")
    return path

def run_ffmpeg(cmd: list, timeout: int = 600, description: str = "") -> subprocess.CompletedProcess:
    """Run FFmpeg command with proper error handling."""
    get_ffmpeg()  # validate exists
    desc = description or " ".join(str(c) for c in cmd[:6])
    log.info(f"[FFmpeg] {desc}...")
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=to_unix(Path.cwd()),
        )
        if r.returncode != 0:
            err = r.stderr[-600:] if len(r.stderr) > 600 else r.stderr
            raise RuntimeError(f"FFmpeg failed (code {r.returncode}): {err}")
        return r
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"FFmpeg timed out after {timeout}s: {desc}")

# ── GPU Detection ───────────────────────────────────
@lru_cache(maxsize=1)
def has_gpu() -> bool:
    """Check if CUDA GPU is available."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False

def get_device() -> str:
    """Get compute device string."""
    return "cuda" if has_gpu() else "cpu"

# ── File Helpers ────────────────────────────────────
def safe_filename(name: str, max_len: int = 80) -> str:
    """Sanitize string for use as filename."""
    import re
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name[:max_len]

def get_file_size_mb(path: Path) -> float:
    """Get file size in megabytes."""
    return path.stat().st_size / (1024 * 1024) if path.exists() else 0.0
