"""
NexuX V9.5 — Enhanced Mode 2 Pipeline
=======================================
Upgraded Mode 2 with keyword expansion, better search, and auto-titling.

Improvements over V8.0 Mode 2:
1. Keyword expansion → searches 15+ terms instead of 1
2. Smarter search: deduplicate channels, prefer videos with captions
3. Auto-generate viral titles + hashtags + description per clip
4. Better narrative with Opus Killer scoring
5. Multi-language search (EN + ID)
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
from .keyword_expander import get_search_strategy, expand_keyword
from .clip_titler import generate_clip_titles, generate_hashtags, generate_description
from .opus_killer import score_with_opus_killer
from .constants import OUTPUT_DIR

log = getLogger("nexus.mode2.enhanced")


async def run_mode2_enhanced(
    keyword: str,
    style_config: Optional[Dict] = None,
    voice_enabled: bool = True,
    voice_name: str = "id-ID-ArdiNeural",
    sfx_enabled: bool = True,
    bgm_enabled: bool = True,
    target_duration: int = 60,
    max_sources: int = 10,
    max_moments_per_video: int = 3,
    language: str = "both",
    job_id: Optional[str] = None,
    progress_callback: Optional[callable] = None,
) -> Dict:
    """
    Enhanced Mode 2 pipeline with keyword expansion and auto-titling.
    
    Flow:
    1. Expand keyword → 15+ search terms
    2. Search YouTube using expanded terms (deduplicate channels)
    3. Analyze transcripts for relevant moments
    4. Generate narrative with LLM
    5. Download only relevant moments (partial)
    6. Compile video with TTS, SFX, transitions
    7. Auto-generate viral title, hashtags, description
    8. Score with Opus Killer
    """
    start_time = time.time()
    
    if not job_id:
        job_id = f"mode2_{int(time.time())}_{keyword.replace(' ', '_')[:20]}"
    
    # ── Step 1: Keyword Expansion ──
    if progress_callback:
        progress_callback(3, "Expanding keyword for better search...")
    
    log.info(f"[Mode2+] Step 1: Expanding keyword '{keyword}'")
    strategy = get_search_strategy(keyword, max_sources)
    
    log.info(f"[Mode2+] Expanded to {len(strategy['primary_terms'])} primary + {len(strategy['secondary_terms'])} secondary terms")
    log.info(f"[Mode2+] Detected niche: {strategy.get('niche', 'general')}")
    
    # ── Step 2: Multi-term YouTube Search ──
    if progress_callback:
        progress_callback(8, f"Searching YouTube ({len(strategy['primary_terms'])} terms)...")
    
    log.info(f"[Mode2+] Step 2: Searching YouTube with expanded terms")
    
    all_videos = []
    seen_urls = set()
    seen_channels = set()
    channel_count = {}
    
    for term in strategy["primary_terms"]:
        videos = await _run_async(search_youtube, term, max_sources // 2)
        for v in videos:
            if v["url"] not in seen_urls:
                # Deduplicate channels (max 2 per channel for diversity)
                ch = v.get("channel", "")
                if channel_count.get(ch, 0) < 2:
                    seen_urls.add(v["url"])
                    all_videos.append(v)
                    channel_count[ch] = channel_count.get(ch, 0) + 1
        
        if len(all_videos) >= max_sources:
            break
    
    # If not enough, use secondary terms
    if len(all_videos) < max_sources:
        for term in strategy["secondary_terms"]:
            videos = await _run_async(search_youtube, term, max_sources // 3)
            for v in videos:
                if v["url"] not in seen_urls:
                    ch = v.get("channel", "")
                    if channel_count.get(ch, 0) < 2:
                        seen_urls.add(v["url"])
                        all_videos.append(v)
                        channel_count[ch] = channel_count.get(ch, 0) + 1
            if len(all_videos) >= max_sources:
                break
    
    if not all_videos:
        log.error("[Mode2+] No videos found!")
        return {"job_id": job_id, "error": "No videos found for keyword"}
    
    log.info(f"[Mode2+] Found {len(all_videos)} unique videos from {len(channel_count)} channels")
    
    if progress_callback:
        progress_callback(18, f"Found {len(all_videos)} videos. Analyzing transcripts...")
    
    # ── Step 3: Analyze transcripts for relevant moments ──
    log.info(f"[Mode2+] Step 3: Analyzing {len(all_videos)} videos for relevant moments")
    moments = await _run_async(analyze_videos_for_keyword, keyword, all_videos, max_moments_per_video)
    
    if not moments:
        log.error("[Mode2+] No relevant moments found")
        return {"job_id": job_id, "error": "No relevant moments found"}
    
    if progress_callback:
        progress_callback(32, f"Found {len(moments)} moments. Generating narrative...")
    
    # ── Step 4: Generate narrative ──
    log.info(f"[Mode2+] Step 4: Generating narrative with LLM")
    production_plan = await _run_async(generate_narrative, keyword, moments, target_duration)
    
    if progress_callback:
        progress_callback(45, f"Narrative ready. Downloading moments...")
    
    # ── Step 5: Download only relevant moments ──
    log.info(f"[Mode2+] Step 5: Downloading moments (partial download)")
    out_dir = OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    
    moments_by_video = {}
    for m in moments:
        vidx = m.get("video_idx", 0)
        if vidx not in moments_by_video:
            moments_by_video[vidx] = {"url": m["video_url"], "moments": []}
        moments_by_video[vidx]["moments"].append(m)
    
    download_tasks = []
    for vidx, vdata in moments_by_video.items():
        download_tasks.append(
            _run_async(download_video_moments, vdata["url"], vdata["moments"], job_id, vidx, out_dir)
        )
    
    results = await asyncio.gather(*download_tasks, return_exceptions=True)
    
    downloaded_files = {}
    for vidx, result in zip(moments_by_video.keys(), results):
        if isinstance(result, list):
            downloaded_files[vidx] = result
        elif isinstance(result, Exception):
            log.error(f"[Mode2+] Download error for video {vidx}: {result}")
    
    total_downloaded = sum(len(v) for v in downloaded_files.values())
    
    if total_downloaded == 0:
        return {"job_id": job_id, "error": "Failed to download any moments"}
    
    if progress_callback:
        progress_callback(65, f"Downloaded {total_downloaded} clips. Compiling video...")
    
    # ── Step 6: Compile video ──
    log.info(f"[Mode2+] Step 6: Compiling video")
    
    default_style = {
        "preset": "hormozi", "font_size": 52,
        "primary": "#FFFFFF", "highlight": "#FFD700",
        "stroke": "#000000", "stroke_width": 4, "bold": True, "position": "bottom",
    }
    style = style_config or default_style
    
    result = await _run_async(
        compile_video, job_id, keyword, moments, downloaded_files, production_plan, style,
        voice_enabled, voice_name, sfx_enabled, bgm_enabled,
    )
    
    if not result.get("output_path"):
        return {"job_id": job_id, "error": "Compilation failed"}
    
    if progress_callback:
        progress_callback(85, "Video compiled. Generating titles & metadata...")
    
    # ── Step 7: Auto-generate viral titles + hashtags + description (NEW) ──
    log.info(f"[Mode2+] Step 7: Auto-generating titles and metadata")
    
    # Get clip text for title generation
    clip_text = " ".join(m.get("text", "") for m in moments[:5])
    
    titles = generate_clip_titles(
        clip={"start": 0, "end": target_duration, "text": clip_text[:300]},
        transcript_segments=[{"text": m.get("text", ""), "speaker": "narrator"} for m in moments[:5]],
        hook_text=production_plan.get("narration_script", "")[:200],
        mode="creative",
        count=5,
        language="id" if "id" in voice_name.lower() else "en",
    )
    
    hashtags = generate_hashtags(clip_text, mode="creative", language="id" if "id" in voice_name.lower() else "en")
    
    best_title = titles[0]["title"] if titles else f"{keyword} - Viral Compilation"
    description = generate_description(clip_text, best_title, mode="creative",
                                       language="id" if "id" in voice_name.lower() else "en",
                                       hashtags=hashtags)
    
    # ── Step 8: Score with Opus Killer ──
    log.info(f"[Mode2+] Step 8: Scoring with Opus Killer")
    
    opus_score = score_with_opus_killer(
        clip={"start": 0, "end": target_duration, "score": 0.5},
        transcript_segments=[{"text": m.get("text", ""), "speaker": "narrator"} for m in moments[:5]],
        full_segments=[{"text": m.get("text", ""), "start": m.get("start", 0), "end": m.get("end", 0)} for m in moments],
        total_duration=target_duration,
        mode="creative",
    )
    
    # ── Final output ──
    elapsed = time.time() - start_time
    metadata = result.get("metadata", {})
    metadata.update({
        "processing_time": round(elapsed, 1),
        "mode": "creative",
        "sources_found": len(all_videos),
        "moments_found": len(moments),
        "clips_downloaded": total_downloaded,
        "keyword": keyword,
        "expanded_terms": strategy["primary_terms"],
        "niche": strategy.get("niche"),
        "auto_titles": titles,
        "auto_hashtags": hashtags,
        "auto_description": description,
        "opus_killer_score": {
            "composite": round(opus_score.composite, 1),
            "grade": opus_score.grade,
            "verdict": opus_score.verdict,
            "beats_opus_by": round(opus_score.beats_opus_estimate, 1),
        },
    })
    
    log.info(f"[Mode2+] ✅ Complete in {elapsed:.1f}s | Score: {opus_score.composite:.1f}/100 ({opus_score.grade})")
    
    if progress_callback:
        progress_callback(100, "Done!")
    
    return {
        "job_id": job_id,
        "output_path": str(result["output_path"]),
        "thumbnail_path": str(result["thumbnail_path"]) if result.get("thumbnail_path") else None,
        "metadata": metadata,
        "titles": titles,
        "hashtags": hashtags,
        "description": description,
        "opus_killer_score": {
            "composite": round(opus_score.composite, 1),
            "grade": opus_score.grade,
            "verdict": opus_score.verdict,
            "breakdown": opus_score.breakdown,
            "reasoning": opus_score.reasoning,
        },
    }


async def _run_async(func, *args, **kwargs):
    """Run a sync function in a thread."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
