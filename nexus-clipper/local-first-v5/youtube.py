from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}


def validate_youtube_url(url: str) -> str:
    url = (url or "").strip()
    if len(url) > 2000 or not re.match(r"^https?://", url, re.I):
        raise ValueError("URL YouTube tidak valid")
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.hostname not in YOUTUBE_HOSTS:
        raise ValueError("Hanya URL YouTube yang didukung")
    if parsed.hostname in {"youtu.be", "www.youtu.be"} and not parsed.path.strip("/"):
        raise ValueError("YouTube video ID kosong")
    if parsed.hostname not in {"youtu.be", "www.youtu.be"} and parsed.path not in {"/watch", "/shorts", "/live", "/embed"} and not parsed.path.startswith(("/watch", "/shorts/", "/live/", "/embed/")):
        raise ValueError("URL YouTube bukan URL video yang dikenali")
    return url


def probe_youtube(url: str) -> dict[str, Any]:
    url = validate_youtube_url(url)
    cmd = ["yt-dlp", "--dump-single-json", "--no-playlist", "--no-warnings", url]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1500:] or "yt-dlp metadata gagal")
    info = json.loads(result.stdout)
    if info.get("is_live"):
        raise ValueError("Live stream belum didukung pada Local-First V5")
    return {
        "id": info.get("id"),
        "title": info.get("title", ""),
        "duration": info.get("duration", 0),
        "uploader": info.get("uploader", ""),
        "thumbnail": info.get("thumbnail", ""),
        "webpage_url": info.get("webpage_url", url),
    }


def download_youtube(url: str, job_dir: Path, max_height: int = 1080) -> tuple[Path, dict[str, Any]]:
    url = validate_youtube_url(url)
    job_dir.mkdir(parents=True, exist_ok=True)
    meta = probe_youtube(url)
    max_duration = int(os.getenv("MAX_VIDEO_DURATION_SECONDS", "21600"))
    if meta.get("duration") and int(meta["duration"]) > max_duration:
        raise ValueError(f"Video terlalu panjang. Batas lokal: {max_duration} detik")

    output = job_dir / "source.%(ext)s"
    fmt = (
        f"bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]/"
        f"best[height<={max_height}][ext=mp4]/best[height<={max_height}]/best"
    )
    cmd = [
        "yt-dlp", "--no-playlist", "--no-warnings", "--no-part",
        "--retries", "5", "--fragment-retries", "5",
        "-f", fmt, "-o", str(output), url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=int(os.getenv("DOWNLOAD_TIMEOUT_SECONDS", "3600")))
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:] or "Download YouTube gagal")

    candidates = [p for p in job_dir.glob("source.*") if p.suffix.lower() in {".mp4", ".mkv", ".webm", ".mov"}]
    if not candidates:
        raise FileNotFoundError("yt-dlp selesai tetapi file video lokal tidak ditemukan")
    return max(candidates, key=lambda p: p.stat().st_size), meta
