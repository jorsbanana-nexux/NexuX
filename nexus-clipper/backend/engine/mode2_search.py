"""
NexuX V8.0 — Mode 2: Multi-Source Search & Download
=====================================================
Search YouTube for 10 related videos based on a keyword.
Download only relevant MOMENTS (partial download) from each.
Keeps PC lightweight — no full 10-video downloads.
"""
import subprocess
import json
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from logging import getLogger
import hashlib

from .constants import OUTPUT_DIR

log = getLogger("nexus.mode2.search")


def search_youtube(keyword: str, max_results: int = 10) -> List[Dict]:
    """Search YouTube for videos related to the keyword.
    
    Uses yt-dlp's ytsearch feature — no API key needed.
    Returns metadata for each video: title, url, duration, description, channel.
    """
    log.info(f"[Mode2] Searching YouTube for: '{keyword}' (max {max_results})")
    
    cmd = [
        "yt-dlp",
        f"ytsearch{max_results}:{keyword}",
        "--dump-json",
        "--no-warnings",
        "--skip-download",
        "--flat-playlist",  # Fast — just metadata, no video info
    ]
    
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    if r.returncode != 0:
        log.error(f"[Mode2] Search failed: {r.stderr[-300:]}")
        # Fallback: try without flat-playlist for more details
        cmd2 = [
            "yt-dlp",
            f"ytsearch{max_results}:{keyword}",
            "--dump-json",
            "--no-warnings",
            "--skip-download",
        ]
        r = subprocess.run(cmd2, capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            log.error(f"[Mode2] Search fallback also failed: {r.stderr[-300:]}")
            return []
        results_raw = r.stdout.strip().split("\n")
    else:
        results_raw = r.stdout.strip().split("\n")
    
    videos = []
    for line in results_raw:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            video = {
                "id": data.get("id", ""),
                "url": data.get("url", data.get("webpage_url", "")),
                "title": data.get("title", ""),
                "duration": data.get("duration", 0),
                "channel": data.get("channel", data.get("uploader", "")),
                "description": (data.get("description", "") or "")[:500],
                "view_count": data.get("view_count", 0),
                "upload_date": data.get("upload_date", ""),
            }
            if video["url"] and video["title"]:
                videos.append(video)
        except json.JSONDecodeError:
            continue
    
    log.info(f"[Mode2] Found {len(videos)} videos for '{keyword}'")
    for i, v in enumerate(videos):
        log.info(f"  [{i+1}] {v['title'][:60]} ({v['duration']}s) — {v['channel']}")
    
    return videos


def get_auto_captions(url: str, lang: str = "en") -> Optional[Dict]:
    """Fetch auto-captions for a YouTube video (fast path — no Whisper needed)."""
    log.info(f"[Mode2] Fetching auto-captions for {url}")
    
    cmd = [
        "yt-dlp",
        "--write-auto-subs",
        "--sub-lang", lang,
        "--skip-download",
        "--sub-format", "json3",
        "-o", "%(id)s",
        "--print", "%(id)s",
        url,
    ]
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            "yt-dlp",
            "--write-auto-subs",
            "--sub-lang", f"{lang},id",
            "--skip-download",
            "--sub-format", "json3",
            "-o", os.path.join(tmpdir, "%(id)s"),
            url,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if r.returncode != 0:
            log.warning(f"[Mode2] Auto-captions failed: {r.stderr[-200:]}")
            return None
        
        # Find the json3 subtitle file
        for f in os.listdir(tmpdir):
            if f.endswith(".json3"):
                fpath = os.path.join(tmpdir, f)
                try:
                    with open(fpath, "r", encoding="utf-8") as f2:
                        data = json.load(f2)
                    
                    segments = []
                    for event in data.get("events", []):
                        segs = event.get("segs", [])
                        text = "".join(s.get("utf8", "") for s in segs).strip()
                        if not text:
                            continue
                        start = event.get("tStartMs", 0) / 1000.0
                        dur = event.get("dDurationMs", 0) / 1000.0
                        segments.append({
                            "start": start,
                            "end": start + dur,
                            "text": text,
                            "words": [],  # Auto-caps usually don't have word-level
                        })
                    
                    if segments:
                        log.info(f"[Mode2] Auto-captions: {len(segments)} segments")
                        return {"segments": segments, "source": "auto_captions"}
                except Exception as e:
                    log.warning(f"[Mode2] Parse auto-captions failed: {e}")
    
    return None


def download_video_moments(
    url: str,
    moments: List[Dict],
    job_id: str,
    video_idx: int,
    output_dir: Path,
) -> List[Path]:
    """Download ONLY specific moments from a video (partial download).
    
    moments = [{"start": 120.5, "end": 135.2, "reason": "peter parker scene"}, ...]
    Uses yt-dlp --download-sections for efficient partial download.
    """
    downloaded = []
    
    for m_idx, moment in enumerate(moments):
        start = moment["start"]
        end = moment["end"]
        duration = end - start
        
        if duration < 2:
            continue
        if duration > 120:
            end = start + 120  # Cap at 2 minutes per moment
        
        out_path = output_dir / f"src_{video_idx:02d}_mom_{m_idx:02d}.mp4"
        
        # yt-dlp --download-sections format: "*start-end"
        sections = f"*{start}-{end}"
        
        cmd = [
            "yt-dlp", "-y",
            "--download-sections", sections,
            "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "--merge-output-format", "mp4",
            "-o", str(out_path),
            url,
        ]
        
        log.info(f"[Mode2] Downloading video {video_idx} moment {m_idx}: {start:.1f}s-{end:.1f}s ({duration:.1f}s)")
        
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if r.returncode != 0:
            log.warning(f"[Mode2] Download failed for {url} [{start}-{end}]: {r.stderr[-200:]}")
            # Fallback: simpler format
            cmd2 = [
                "yt-dlp", "-y",
                "--download-sections", sections,
                "-f", "best[ext=mp4]",
                "-o", str(out_path),
                url,
            ]
            r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=120)
            if r2.returncode != 0:
                continue
        
        if out_path.exists() and out_path.stat().st_size > 1000:
            downloaded.append(out_path)
            log.info(f"[Mode2] ✅ Downloaded {out_path.name} ({out_path.stat().st_size // 1024}KB)")
        else:
            # Check for .webm or other extensions
            for ext in [".webm", ".mkv", ".mp4"]:
                alt = out_path.with_suffix(ext)
                if alt.exists() and alt.stat().st_size > 1000:
                    downloaded.append(alt)
                    break
    
    return downloaded


def analyze_videos_for_keyword(
    keyword: str,
    videos: List[Dict],
    max_moments_per_video: int = 3,
) -> List[Dict]:
    """Analyze video transcripts to find moments relevant to the keyword.
    
    For each video:
    1. Fetch auto-captions
    2. Find segments that mention the keyword or related terms
    3. Extract timestamp ranges
    
    Returns moments per video with metadata.
    """
    log.info(f"[Mode2] Analyzing {len(videos)} videos for keyword: '{keyword}'")
    
    keyword_lower = keyword.lower()
    keyword_words = keyword_lower.split()
    
    all_moments = []
    
    for v_idx, video in enumerate(videos):
        url = video["url"]
        title = video["title"]
        
        # Fetch auto-captions
        caps = get_auto_captions(url, lang="en")
        if not caps:
            # Try Indonesian
            caps = get_auto_captions(url, lang="id")
        
        if not caps:
            log.warning(f"[Mode2] No captions for video {v_idx}: {title[:40]}")
            continue
        
        segments = caps.get("segments", [])
        video_moments = []
        
        # Find segments mentioning keyword
        for seg in segments:
            text = seg.get("text", "").lower()
            
            # Check if any keyword word appears in the segment
            if any(kw in text for kw in keyword_words):
                start = seg["start"]
                end = seg["end"]
                
                # Expand the moment a bit for context (2s before, 2s after)
                start = max(0, start - 2)
                end = end + 2
                
                # Don't exceed video duration
                if video["duration"] > 0:
                    end = min(end, video["duration"])
                
                video_moments.append({
                    "start": start,
                    "end": end,
                    "text": seg.get("text", ""),
                    "reason": f"Keyword '{keyword}' found in transcript",
                    "video_idx": v_idx,
                    "video_url": url,
                    "video_title": title,
                })
        
        # Limit moments per video
        video_moments = video_moments[:max_moments_per_video]
        
        # Merge overlapping moments
        video_moments = _merge_overlapping(video_moments)
        
        if video_moments:
            all_moments.extend(video_moments)
            log.info(f"[Mode2] Video {v_idx}: {len(video_moments)} relevant moments")
    
    log.info(f"[Mode2] Total moments across all videos: {len(all_moments)}")
    return all_moments


def _merge_overlapping(moments: List[Dict]) -> List[Dict]:
    """Merge overlapping time ranges."""
    if not moments:
        return []
    
    sorted_m = sorted(moments, key=lambda m: m["start"])
    merged = [sorted_m[0]]
    
    for m in sorted_m[1:]:
        last = merged[-1]
        if m["start"] <= last["end"]:
            # Overlap — extend
            last["end"] = max(last["end"], m["end"])
            last["text"] = last.get("text", "") + " " + m.get("text", "")
        else:
            merged.append(m)
    
    return merged
