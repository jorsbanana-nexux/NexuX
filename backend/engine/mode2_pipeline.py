"""
NexuX V9.5 — Mode 2: Complete Pipeline
=======================================
The full Mode 2 flow:
1. User types keyword (no URL)
2. AI searches YouTube for 10 related videos
3. AI fetches auto-captions, finds relevant moments
4. AI downloads only relevant moments (partial download)
5. AI generates narrative script (LLM)
6. AI compiles moments + narration + SFX + text → one video
7. AI generates thumbnail
8. Output: video + thumbnail + title + hashtags + description

This is NOT a clipper — it's a creative compilation engine.
"""
import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from logging import getLogger

from .mode2_search import search_youtube, analyze_videos_for_keyword, download_video_moments
from .mode2_narrator import generate_narrative
from .mode2_compiler import compile_video
from .constants import OUTPUT_DIR

log = getLogger("nexus.mode2.pipeline")


async def run_mode2_pipeline(
    keyword: str,
    style_config: Optional[Dict] = None,
    voice_enabled: bool = True,
    voice_name: str = "id-ID-ArdiNeural",
    sfx_enabled: bool = True,
    bgm_enabled: bool = True,
    target_duration: int = 60,
    max_sources: int = 10,
    max_moments_per_video: int = 3,
    job_id: Optional[str] = None,
    progress_callback: Optional[callable] = None,
    storyboard: Optional[List[Dict]] = None,
) -> Dict:
    """Run the complete Mode 2 pipeline.
    
    Returns:
        {
            "job_id": str,
            "output_path": Path,
            "thumbnail_path": Path,
            "metadata": {
                "title": str,
                "hashtags": list,
                "description": str,
                "sources_used": int,
                "total_duration": float,
                "keyword": str,
            }
        }
    """
    start_time = time.time()
    
    if not job_id:
        job_id = f"mode2_{int(time.time())}_{keyword.replace(' ', '_')[:20]}"
    
    if progress_callback:
        progress_callback(5, "Searching YouTube for related videos...")
    
    # ── Step 1: Get videos (storyboard override OR search YouTube) ──
    if storyboard:
        log.info(f"[Mode2] Step 1: Using provided storyboard ({len(storyboard)} clips)")
        videos = [
            {
                "url": c.get("video_url", ""),
                "title": c.get("video_title", "")[:120],
                "duration": c.get("duration", 0),
                "view_count": c.get("view_count", 0),
                "channel": c.get("channel", ""),
            }
            for c in storyboard if c.get("video_url")
        ]
    else:
        log.info(f"[Mode2] Step 1: Searching YouTube for '{keyword}'")
        videos = await _run_async(search_youtube, keyword, max_sources)
    
    if not videos:
        log.error("[Mode2] No videos found!")
        return {"job_id": job_id, "error": "No videos found for keyword"}
    
    if progress_callback:
        progress_callback(15, f"Found {len(videos)} videos. Analyzing transcripts...")
    
    # ── Step 2: Analyze transcripts for relevant moments ──
    log.info(f"[Mode2] Step 2: Analyzing {len(videos)} videos for relevant moments")
    moments = await _run_async(analyze_videos_for_keyword, keyword, videos, max_moments_per_video)
    
    if not moments:
        log.error("[Mode2] No relevant moments found in transcripts")
        return {"job_id": job_id, "error": "No relevant moments found"}
    
    if progress_callback:
        progress_callback(30, f"Found {len(moments)} moments. Generating narrative...")
    
    # ── Step 3: Generate narrative (LLM) ──
    log.info(f"[Mode2] Step 3: Generating narrative with LLM")
    production_plan = await _run_async(generate_narrative, keyword, moments, target_duration)
    
    if progress_callback:
        progress_callback(45, f"Narrative ready. Downloading moments from {len(moments)} videos...")
    
    # ── Step 4: Download only relevant moments (partial download) ──
    log.info(f"[Mode2] Step 4: Downloading moments (partial download)")
    out_dir = OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Group moments by video index
    moments_by_video = {}
    for m in moments:
        vidx = m.get("video_idx", 0)
        if vidx not in moments_by_video:
            moments_by_video[vidx] = {"url": m["video_url"], "moments": []}
        moments_by_video[vidx]["moments"].append(m)
    
    # Download in parallel
    downloaded_files = {}
    download_tasks = []
    
    for vidx, vdata in moments_by_video.items():
        download_tasks.append(
            _run_async(download_video_moments, vdata["url"], vdata["moments"], job_id, vidx, out_dir)
        )
    
    results = await asyncio.gather(*download_tasks, return_exceptions=True)
    
    for vidx, result in zip(moments_by_video.keys(), results):
        if isinstance(result, list):
            downloaded_files[vidx] = result
        elif isinstance(result, Exception):
            log.error(f"[Mode2] Download error for video {vidx}: {result}")
    
    total_downloaded = sum(len(v) for v in downloaded_files.values())
    log.info(f"[Mode2] Downloaded {total_downloaded} moment clips from {len(downloaded_files)} videos")
    
    if total_downloaded == 0:
        log.error("[Mode2] No moments downloaded")
        return {"job_id": job_id, "error": "Failed to download any moments"}
    
    if progress_callback:
        progress_callback(65, f"Downloaded {total_downloaded} clips. Compiling video...")
    
    # ── Step 5: Compile video ──
    log.info(f"[Mode2] Step 5: Compiling video")
    
    default_style = {
        "preset": "hormozi",
        "font_size": 52,
        "primary": "#FFFFFF",
        "highlight": "#FFD700",
        "stroke": "#000000",
        "stroke_width": 4,
        "bold": True,
        "position": "bottom",
    }
    style = style_config or default_style
    
    result = await _run_async(
        compile_video,
        job_id, keyword, moments, downloaded_files, production_plan, style,
        voice_enabled, voice_name, sfx_enabled, bgm_enabled,
    )
    
    if not result.get("output_path"):
        log.error("[Mode2] Compilation failed")
        return {"job_id": job_id, "error": "Compilation failed"}
    
    if progress_callback:
        progress_callback(90, "Video compiled. Finalizing...")
    
    # ── Step 6: Final output ──
    elapsed = time.time() - start_time
    metadata = result.get("metadata", {})
    metadata["processing_time"] = round(elapsed, 1)
    metadata["mode"] = "mode2"
    metadata["sources_found"] = len(videos)
    metadata["moments_found"] = len(moments)
    metadata["clips_downloaded"] = total_downloaded
    # Traceability: persist the exact storyboard that produced this compilation
    metadata["storyboard"] = storyboard or [
        {
            "clip_idx": i + 1,
            "role": "hook" if i == 0 else ("payoff" if i == len(videos) - 1 else "beat"),
            "video_url": v.get("url", ""),
            "video_title": v.get("title", "")[:120],
            "duration": v.get("duration", 0),
            "channel": v.get("channel", ""),
        }
        for i, v in enumerate(videos)
    ]
    
    log.info(f"[Mode2] ✅ Complete in {elapsed:.1f}s")

    # Persist metadata for traceability (/api/mode2/jobs reads this)
    try:
        job_dir = OUTPUT_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2)
        )
    except Exception as e:
        log.warning(f"[Mode2] Failed to persist metadata.json: {e}")

    if progress_callback:
        progress_callback(100, "Done!")

    return {
        "job_id": job_id,
        "output_path": str(result["output_path"]),
        "thumbnail_path": str(result["thumbnail_path"]) if result.get("thumbnail_path") else None,
        "metadata": metadata,
    }


async def _run_async(func, *args, **kwargs):
    """Run a sync function in a thread."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
