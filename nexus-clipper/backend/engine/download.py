"""
NexuX V8.0 — Smart Download Engine
====================================
Revolutionary two-phase download:
1. Fast metadata + auto-caption fetch (no video download!)
2. Partial download — ONLY the selected moment time ranges

Key innovation: yt-dlp --download-sections downloads only the
seconds we need, not the entire video. A 2-hour video → 60-second
download instead of 30-minute download.
"""
import json, subprocess, os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

from .constants import OUTPUT_DIR, DOWNLOAD_TIMEOUT
from .utils import retry

log = logging.getLogger("nexus.download")


def get_video_info(url: str) -> Dict:
    """Get YouTube video metadata WITHOUT downloading — instant."""
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
        "has_auto_captions": bool(
            any(
                sub.get("ext") == "vtt" or sub.get("ext") == "json3"
                for sub in (info.get("automatic_captions") or {}).get("en", [])
            )
        ),
        "available_subs": list((info.get("subtitles") or {}).keys()),
        "available_auto_subs": list((info.get("automatic_captions") or {}).keys()),
    }


def fetch_auto_captions(
    url: str,
    job_id: str,
    language: Optional[str] = None,
) -> Optional[Dict]:
    """Fetch YouTube auto-generated captions WITHOUT downloading video.
    
    This is the FAST PATH — if YouTube has auto-captions, we skip
    the entire whisper transcription step (saves 30-60 seconds).
    
    Returns transcript dict in same format as transcribe(), or None.
    """
    work_dir = OUTPUT_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)

    # Determine language to fetch
    lang = language or "en"

    # First, check what auto-captions are available
    cmd_info = [
        "yt-dlp",
        "--dump-json",
        "--no-playlist",
        "--no-warnings",
        url,
    ]
    r = subprocess.run(cmd_info, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        log.warning(f"[Download] Cannot fetch video info for captions: {r.stderr[-200:]}")
        return None

    info = json.loads(r.stdout)
    auto_caps = info.get("automatic_captions") or {}

    # Try requested language, then English, then first available
    caption_lang = None
    for try_lang in [lang, "en", "en-US", "en-GB"]:
        if try_lang in auto_caps and auto_caps[try_lang]:
            caption_lang = try_lang
            break
    if not caption_lang and auto_caps:
        caption_lang = next(iter(auto_caps))

    if not caption_lang:
        log.info("[Download] No auto-captions available — will use whisper")
        return None

    # Download the auto-caption as JSON3 (has word timing)
    sub_formats = auto_caps[caption_lang]
    # Prefer json3 (has word-level timing), then vtt, then srv1
    best_format = None
    for fmt in sub_formats:
        if fmt.get("ext") == "json3":
            best_format = fmt
            break
    if not best_format:
        for fmt in sub_formats:
            if fmt.get("ext") == "vtt":
                best_format = fmt
                break
    if not best_format and sub_formats:
        best_format = sub_formats[0]

    if not best_format:
        return None

    sub_url = best_format.get("url")
    if not sub_url:
        return None

    log.info(f"[Download] Fetching auto-captions ({caption_lang}, {best_format.get('ext')})...")

    # Download the subtitle file
    sub_file = work_dir / f"auto_caption.{best_format.get('ext', 'vtt')}"
    cmd_sub = [
        "yt-dlp",
        "--no-playlist",
        "--no-warnings",
        "--write-auto-sub",
        "--sub-lang", caption_lang,
        "--sub-format", best_format.get("ext", "vtt"),
        "--skip-download",
        "-o", str(work_dir / "auto_caption"),
        url,
    ]
    r = subprocess.run(cmd_sub, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        log.warning(f"[Download] Auto-caption download failed: {r.stderr[-200:]}")
        return None

    # Find the downloaded subtitle file
    sub_files = list(work_dir.glob("auto_caption.*"))
    # Filter out video files
    sub_files = [f for f in sub_files if f.suffix in (".vtt", ".json3", ".srv1", ".srv2", ".srv3", ".ass", ".srt")]
    if not sub_files:
        log.warning("[Download] No subtitle file found after download")
        return None

    sub_file = sub_files[0]
    log.info(f"[Download] Auto-caption file: {sub_file.name}")

    # Parse the subtitle file into transcript format
    if sub_file.suffix == ".json3":
        transcript = _parse_json3(sub_file)
    elif sub_file.suffix == ".vtt":
        transcript = _parse_vtt(sub_file)
    else:
        # For other formats, try yt-dlp's --write-auto-sub with json3
        log.warning(f"[Download] Unsupported subtitle format: {sub_file.suffix}")
        return None

    if not transcript or not transcript.get("segments"):
        log.warning("[Download] Auto-caption parsing yielded no segments")
        return None

    log.info(f"[Download] Auto-captions parsed: {len(transcript['segments'])} segments ✅")
    return transcript


def _parse_json3(filepath: Path) -> Optional[Dict]:
    """Parse YouTube JSON3 subtitle format into transcript dict."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        segments = []
        for event in data.get("events", []):
            if not event.get("segs"):
                continue

            text = "".join(seg.get("utf8", "") for seg in event["segs"]).strip()
            if not text:
                continue

            start = event.get("tStartMs", 0) / 1000.0
            duration = event.get("dDurationMs", 0) / 1000.0
            end = start + duration if duration > 0 else start + 2.0

            # Word-level timing if available
            words = []
            for seg in event.get("segs", []):
                word_text = seg.get("utf8", "").strip()
                if word_text:
                    word_start = start + (seg.get("tOffsetMs", 0) / 1000.0)
                    words.append({
                        "text": word_text,
                        "start": round(word_start, 3),
                        "end": round(word_start + 0.3, 3),
                    })

            segments.append({
                "start": round(start, 3),
                "end": round(end, 3),
                "text": text,
                "words": words if words else [{"text": text, "start": start, "end": end}],
            })

        return {
            "text": " ".join(s["text"] for s in segments),
            "segments": segments,
            "language": data.get("language", "en"),
            "source": "youtube_auto",
        }
    except Exception as e:
        log.warning(f"[Download] JSON3 parse failed: {e}")
        return None


def _parse_vtt(filepath: Path) -> Optional[Dict]:
    """Parse VTT subtitle format into transcript dict."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        segments = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip header and blank lines
            if not line or line.startswith("WEBVTT") or line.startswith("NOTE"):
                i += 1
                continue

            # Try to parse timestamp line (00:00:01.000 --> 00:00:03.000)
            if "-->" in line:
                times = line.split("-->")
                start_str = times[0].strip()
                end_str = times[1].strip().split(" ")[0]  # Remove position info

                start = _parse_timestamp(start_str)
                end = _parse_timestamp(end_str)

                # Collect text lines until blank or next timestamp
                text_lines = []
                i += 1
                while i < len(lines):
                    text_line = lines[i].strip()
                    if not text_line or "-->" in text_line:
                        break
                    # Remove VTT tags like <c.colorname>
                    import re
                    clean = re.sub(r'<[^>]+>', '', text_line)
                    if clean:
                        text_lines.append(clean)
                    i += 1

                text = " ".join(text_lines).strip()
                if text:
                    words = [{"text": w, "start": start, "end": end} for w in text.split()]
                    segments.append({
                        "start": round(start, 3),
                        "end": round(end, 3),
                        "text": text,
                        "words": words,
                    })
            else:
                i += 1

        return {
            "text": " ".join(s["text"] for s in segments),
            "segments": segments,
            "language": "en",
            "source": "youtube_auto",
        }
    except Exception as e:
        log.warning(f"[Download] VTT parse failed: {e}")
        return None


def _parse_timestamp(ts: str) -> float:
    """Parse timestamp string (HH:MM:SS.mmm or MM:SS.mmm) to seconds."""
    ts = ts.strip()
    parts = ts.split(":")
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    return float(parts[0])


def download_clip_section(
    url: str,
    job_id: str,
    start: float,
    end: float,
    clip_index: int = 0,
    max_height: int = 1080,
) -> Path:
    """Download ONLY a specific time range of a YouTube video.
    
    Uses yt-dlp --download-sections to fetch only the seconds we need.
    For a 60-second clip from a 2-hour video, this downloads ~60 seconds
    of content instead of the entire 2 hours.
    
    Args:
        url: YouTube video URL
        job_id: Job identifier
        start: Start time in seconds
        end: End time in seconds
        clip_index: Clip index for filename
        max_height: Max video height
    
    Returns:
        Path to downloaded clip section
    """
    work_dir = OUTPUT_DIR / job_id / "sections"
    work_dir.mkdir(parents=True, exist_ok=True)

    # Format timestamps for yt-dlp: "*start-end"
    section = f"*{start}-{end}"
    tmpl = str(work_dir / f"clip_{clip_index:02d}.%(ext)s")

    # Format selection
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
        "--download-sections", section,
        "--no-playlist",
        "--no-warnings",
        "--socket-timeout", "30",
        "--retries", "5",
        "--fragment-retries", "5",
        "--no-part",
        "--no-mtime",
        "--force-keyframes-at-cuts",  # More accurate cuts
        url,
    ]

    def _download():
        duration = end - start
        log.info(f"[Download] Section {clip_index}: {start:.1f}s-{end:.1f}s ({duration:.0f}s)")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=DOWNLOAD_TIMEOUT)

        if r.returncode != 0:
            err = r.stderr[-500:] if len(r.stderr) > 500 else r.stderr
            raise RuntimeError(f"yt-dlp section download failed: {err}")

        # Find the downloaded file
        video_extensions = [".mp4", ".mkv", ".webm", ".mov", ".avi"]
        candidates = []
        for ext in video_extensions:
            candidates.extend(work_dir.glob(f"clip_{clip_index:02d}{ext}"))

        if not candidates:
            # Try any video file in the directory
            for ext in video_extensions:
                candidates.extend(work_dir.glob(f"*{ext}"))

        if not candidates:
            all_files = list(work_dir.iterdir())
            log.error(f"[Download] No video found. Files: {[f.name for f in all_files]}")
            raise FileNotFoundError(f"No video file found in {work_dir}")

        candidates.sort(key=lambda p: p.stat().st_size, reverse=True)
        video_path = candidates[0]

        size_mb = video_path.stat().st_size / (1024 * 1024)
        log.info(f"[Download] Section {clip_index} complete: {video_path.name} ({size_mb:.1f} MB)")
        return video_path

    return retry(_download, max_retries=3)


def download_youtube(url: str, job_id: str, max_height: int = 1080) -> Path:
    """Download full YouTube video (fallback when partial download isn't possible)."""
    work_dir = OUTPUT_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)

    tmpl = str(work_dir / "source.%(ext)s")
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
        "--socket-timeout", "30",
        "--retries", "10",
        "--fragment-retries", "10",
        "--no-part",
        "--no-mtime",
        url,
    ]

    def _download():
        log.info(f"[Download] Full video: {url[:80]}...")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=DOWNLOAD_TIMEOUT)

        if r.returncode != 0:
            err = r.stderr[-500:] if len(r.stderr) > 500 else r.stderr
            raise RuntimeError(f"yt-dlp download failed: {err}")

        video_extensions = [".mp4", ".mkv", ".webm", ".mov", ".avi"]
        candidates = []
        for ext in video_extensions:
            candidates.extend(work_dir.glob(f"source{ext}"))

        if not candidates:
            all_files = list(work_dir.iterdir())
            log.error(f"[Download] No video found. Files: {[f.name for f in all_files]}")
            raise FileNotFoundError(f"No video file found in {work_dir}")

        candidates.sort(key=lambda p: p.stat().st_size, reverse=True)
        video_path = candidates[0]

        size_mb = video_path.stat().st_size / (1024 * 1024)
        log.info(f"[Download] Complete: {video_path.name} ({size_mb:.1f} MB)")
        return video_path

    return retry(_download, max_retries=3)


def download_audio_only(url: str, job_id: str) -> Path:
    """Download audio-only for fast transcription fallback.
    
    Much faster than downloading full video — only audio track.
    Used when YouTube auto-captions are not available.
    """
    work_dir = OUTPUT_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)

    tmpl = str(work_dir / "audio.%(ext)s")
    cmd = [
        "yt-dlp",
        "-f", "bestaudio[ext=m4a]/bestaudio",
        "-o", tmpl,
        "--no-playlist",
        "--no-warnings",
        "--socket-timeout", "30",
        "--retries", "5",
        "--no-part",
        "--no-mtime",
        url,
    ]

    def _download():
        log.info(f"[Download] Audio-only for transcription...")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if r.returncode != 0:
            err = r.stderr[-500:] if len(r.stderr) > 500 else r.stderr
            raise RuntimeError(f"yt-dlp audio download failed: {err}")

        audio_files = list(work_dir.glob("audio.*"))
        if not audio_files:
            raise FileNotFoundError(f"No audio file found in {work_dir}")

        audio_path = audio_files[0]
        size_mb = audio_path.stat().st_size / (1024 * 1024)
        log.info(f"[Download] Audio complete: {audio_path.name} ({size_mb:.1f} MB)")
        return audio_path

    return retry(_download, max_retries=3)


def search_youtube(query: str, max_results: int = 10) -> list:
    """Search YouTube for videos matching query."""
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
