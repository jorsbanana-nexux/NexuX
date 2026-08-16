from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from process_supervisor import run as supervised_run


@dataclass(frozen=True)
class RetrievalRange:
    start: float
    end: float

    def padded(self, before: float = 6.0, after: float = 8.0) -> "RetrievalRange":
        return RetrievalRange(max(0.0, self.start - before), self.end + after)


def _vtt_timestamp(value: str) -> float:
    value = value.strip().replace(",", ".")
    parts = value.split(":")
    if len(parts) == 2:
        minutes, seconds = parts
        return float(minutes) * 60.0 + float(seconds)
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return float(hours) * 3600.0 + float(minutes) * 60.0 + float(seconds)
    raise ValueError(f"Invalid VTT timestamp: {value}")


def parse_vtt(text: str) -> dict[str, Any]:
    """Parse WebVTT captions into the transcript shape consumed by NexuX."""
    segments: list[dict[str, Any]] = []
    pattern = re.compile(
        r"(?m)^\s*(\d{1,2}:\d{2}(?::\d{2})?[.,]\d{3})\s+-->\s+(\d{1,2}:\d{2}(?::\d{2})?[.,]\d{3}).*?\n(.*?)(?=\n\s*\n|\Z)",
        re.S,
    )
    for index, match in enumerate(pattern.finditer(text)):
        start = _vtt_timestamp(match.group(1))
        end = _vtt_timestamp(match.group(2))
        raw = re.sub(r"<[^>]+>", "", match.group(3))
        raw = re.sub(r"\{[^}]+\}", "", raw)
        raw = re.sub(r"\s+", " ", raw).strip()
        if not raw or end <= start:
            continue
        segments.append({
            "id": index,
            "start": start,
            "end": end,
            "text": raw,
            "words": [],
        })
    duration = max((float(s["end"]) for s in segments), default=0.0)
    return {"language": None, "segments": segments, "duration": duration, "source": "youtube_vtt"}


def fetch_youtube_captions(url: str, job_dir: Path) -> dict[str, Any] | None:
    """Fetch creator/auto captions without downloading the video itself."""
    caption_dir = job_dir / "recon" / "captions"
    caption_dir.mkdir(parents=True, exist_ok=True)
    output = caption_dir / "%(id)s.%(ext)s"
    cmd = [
        "yt-dlp", "--skip-download", "--no-playlist", "--no-warnings",
        "--write-subs", "--write-auto-subs",
        "--sub-langs", os.getenv("NEXUX_RECON_SUB_LANGS", "id,id-ID,en,en-US"),
        "--sub-format", "vtt", "-o", str(output), url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        return None
    files = sorted(caption_dir.glob("*.vtt"))
    if not files:
        return None
    # Prefer the largest caption file; duplicate language tracks are common.
    source = max(files, key=lambda p: p.stat().st_size)
    transcript = parse_vtt(source.read_text(encoding="utf-8", errors="replace"))
    transcript["caption_file"] = str(source)
    return transcript if transcript.get("segments") else None


def fetch_recon_audio(url: str, job_dir: Path, job_id: str) -> Path:
    """Fallback reconnaissance: audio only, never a full-resolution video download."""
    recon_dir = job_dir / "recon"
    recon_dir.mkdir(parents=True, exist_ok=True)
    output = recon_dir / "audio.%(ext)s"
    cmd = [
        "yt-dlp", "--no-playlist", "--no-warnings", "--retries", "5",
        "--fragment-retries", "5", "-f", "bestaudio[ext=m4a]/bestaudio/best",
        "-o", str(output), url,
    ]
    result = supervised_run(
        cmd,
        key=f"recon-audio:{job_id}",
        timeout=int(os.getenv("RECON_AUDIO_TIMEOUT_SECONDS", "3600")),
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:] or "YouTube reconnaissance audio gagal")
    files = [p for p in recon_dir.glob("audio.*") if p.is_file() and p.suffix.lower() not in {".part", ".ytdl"}]
    if not files:
        raise FileNotFoundError("Reconnaissance audio tidak ditemukan")
    return max(files, key=lambda p: p.stat().st_size)


def download_segment(
    url: str,
    job_dir: Path,
    candidate_id: str,
    start: float,
    end: float,
    before: float = 6.0,
    after: float = 8.0,
    max_height: int = 1080,
) -> tuple[Path, dict[str, float]]:
    """Retrieve only the media interval needed for a selected candidate."""
    if end <= start:
        raise ValueError("Invalid retrieval interval")
    padded = RetrievalRange(start, end).padded(before, after)
    segment_dir = job_dir / "segments"
    segment_dir.mkdir(parents=True, exist_ok=True)
    output = segment_dir / f"{candidate_id}.%(ext)s"
    fmt = f"bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={max_height}][ext=mp4]/best[height<={max_height}]/best"
    section = f"*{padded.start:.3f}-{padded.end:.3f}"
    cmd = [
        "yt-dlp", "--no-playlist", "--no-warnings", "--retries", "8",
        "--fragment-retries", "8", "--download-sections", section,
        "--force-keyframes-at-cuts", "-f", fmt, "-o", str(output), url,
    ]
    result = supervised_run(
        cmd,
        key=f"segment:{candidate_id}",
        timeout=int(os.getenv("SEGMENT_DOWNLOAD_TIMEOUT_SECONDS", "1800")),
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:] or "Targeted segment download gagal")
    files = [p for p in segment_dir.glob(f"{candidate_id}.*") if p.is_file() and p.suffix.lower() not in {".part", ".ytdl"}]
    if not files:
        raise FileNotFoundError("Targeted segment selesai tetapi media tidak ditemukan")
    path = max(files, key=lambda p: p.stat().st_size)
    return path, {"requested_start": start, "requested_end": end, "retrieved_start": padded.start, "retrieved_end": padded.end}


def retrieval_summary(job: dict[str, Any]) -> dict[str, Any]:
    source = job.get("source", {})
    return {
        "strategy": job.get("retrieval", {}).get("strategy", "unknown"),
        "full_video_downloaded": bool(job.get("video_path")),
        "recon_audio": bool(job.get("recon_audio_path")),
        "caption_first": bool(job.get("transcript", {}).get("source") == "youtube_vtt"),
        "segments_cached": len(list((Path(job["job_dir"]) / "segments").glob("*"))) if job.get("job_dir") else 0,
        "source_url": source.get("url"),
    }
