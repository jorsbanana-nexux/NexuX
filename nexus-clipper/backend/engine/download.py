"""
Nexus-Clipper Premium v4.0 — Download Engine
=============================================
YouTube video download via yt-dlp with:
- Best quality auto-selection
- Progress tracking
- Format filtering
- Retry with exponential backoff
"""
import json, subprocess, time
from pathlib import Path
from typing import Dict, Optional
import logging

from .constants import OUTPUT_DIR, DOWNLOAD_TIMEOUT
from .utils import retry

log = logging.getLogger("nexus.download")


def download_youtube(url: str, job_id: str, max_height: int = 1080) -> Path:
    """Download YouTube video in best quality.
    
    Args:
        url: YouTube video URL
        job_id: Unique job identifier for output directory
        max_height: Maximum video height (default 1080p)
    
    Returns:
        Path to downloaded video file
    
    Raises:
        RuntimeError: If download fails after all retries
        FileNotFoundError: If no video file found after download
    """
    work_dir = OUTPUT_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)
    
    # Output template
    tmpl = str(work_dir / "%(title).100s.%(ext)s")
    
    # Format selection: prefer mp4, fall back to best available
    fmt = (
        f"bestvideo[ext=mp4][height<={max_height}]+bestaudio[ext=m4a]/"
        f"best[ext=mp4][height<={max_height}]/"
        f"bestvideo[height<={max_height}]+bestaudio/"
        f"best[height<={max_height}]/"
        f"best"
    )
    
    cmd = [
        "yt-dlp",
        "-f", fmt,
        "-o", tmpl,
        "--no-playlist",
        "--no-warnings",
        "--no-check-certificates",
        "--socket-timeout", "30",
        "--retries", "10",
        "--fragment-retries", "10",
        "--no-part",           # Don't use .part files
        "--no-mtime",          # Don't set file modification time
        url,
    ]
    
    def _download():
        log.info(f"[Download] Starting: {url[:80]}...")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=DOWNLOAD_TIMEOUT)
        
        if r.returncode != 0:
            err = r.stderr[-500:] if len(r.stderr) > 500 else r.stderr
            raise RuntimeError(f"yt-dlp download failed: {err}")
        
        # Find downloaded file (largest video file)
        video_extensions = [".mp4", ".mkv", ".webm", ".mov", ".avi"]
        candidates = []
        for ext in video_extensions:
            candidates.extend(work_dir.glob(f"*{ext}"))
        
        if not candidates:
            # List all files for debugging
            all_files = list(work_dir.iterdir())
            log.error(f"[Download] No video found. Files in dir: {[f.name for f in all_files]}")
            raise FileNotFoundError(f"No video file found in {work_dir}")
        
        # Pick largest file
        candidates.sort(key=lambda p: p.stat().st_size, reverse=True)
        video_path = candidates[0]
        
        size_mb = video_path.stat().st_size / (1024 * 1024)
        log.info(f"[Download] Complete: {video_path.name} ({size_mb:.1f} MB)")
        return video_path
    
    return retry(_download, max_retries=3)


def get_video_info(url: str) -> Dict:
    """Get YouTube video metadata without downloading.
    
    Args:
        url: YouTube video URL
    
    Returns:
        Dict with title, duration, uploader, view count, formats, etc.
    """
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-playlist",
        "--no-warnings",
        url,
    ]
    
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp info failed: {r.stderr[-300:]}")
    
    info = json.loads(r.stdout)
    
    return {
        "title": info.get("title", ""),
        "duration": info.get("duration", 0),
        "duration_str": info.get("duration_string", "0:00"),
        "uploader": info.get("uploader", ""),
        "uploader_url": info.get("uploader_url", ""),
        "view_count": info.get("view_count", 0),
        "like_count": info.get("like_count", 0),
        "comment_count": info.get("comment_count", 0),
        "thumbnail": info.get("thumbnail", ""),
        "description": (info.get("description", "") or "")[:500],
        "tags": info.get("tags", [])[:30] if info.get("tags") else [],
        "categories": info.get("categories", []),
        "resolution": f"{info.get('width', 0)}x{info.get('height', 0)}",
        "fps": info.get("fps", 30),
        "filesize_approx_mb": round((info.get("filesize_approx") or 0) / (1024**2), 1),
        "age_limit": info.get("age_limit", 0),
        "is_live": info.get("is_live", False),
    }


def search_youtube(query: str, max_results: int = 10) -> list:
    """Search YouTube for videos matching query.
    
    Args:
        query: Search query
        max_results: Maximum results to return
    
    Returns:
        List of video info dicts
    """
    cmd = [
        "yt-dlp",
        f"ytsearch{max_results}:{query}",
        "--dump-json",
        "--no-playlist",
        "--no-warnings",
    ]
    
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp search failed: {r.stderr[-300:]}")
    
    results = []
    for line in r.stdout.strip().split("\n"):
        if line.strip():
            info = json.loads(line)
            results.append({
                "id": info.get("id", ""),
                "title": info.get("title", ""),
                "url": info.get("webpage_url", ""),
                "duration": info.get("duration", 0),
                "view_count": info.get("view_count", 0),
                "uploader": info.get("uploader", ""),
                "thumbnail": info.get("thumbnail", ""),
            })
    
    return results
