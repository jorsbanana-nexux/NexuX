"""
NexuX V9.5 — Smart Pipeline Orchestrator
==========================================
Revolutionary two-phase architecture:
1. Fast metadata + auto-caption fetch (NO video download)
2. AI moment selection from transcript
3. Download ONLY selected sections (partial download!)
4. Parallel rendering with professional effects
5. Quality gate + assembly

V8.0 key improvements over V7.0:
- Auto-captions from YouTube (skips whisper entirely — saves 30-60s)
- Partial download (only download the 60s we need, not 2 hours)
- Parallel section downloads (asyncio.gather)
- Parallel rendering (asyncio.gather)
- Audio-only fallback for whisper (10x faster than full video)
- Real-time progress with ETA estimation
"""
import asyncio
import time
from typing import Dict, Optional, Callable, List
from pathlib import Path
import logging

from .constants import OUTPUT_DIR, MAX_RETRIES
from .utils import retry, get_file_size_mb
from .download import (
    get_video_info, fetch_auto_captions,
    download_clip_section, download_audio_only,
)
from .transcribe import transcribe
from .analyze import analyze_content
from .render_pro import render_clip_pro, concatenate_clips_pro
from .critic import evaluate_clip, apply_revision_directives
from .subtitle_quality import process_subtitle_quality
from .audio_enhancer import enhance_audio
from .creative_brain import choose_creative_palette, record_outcome
from .self_healer import heal, diagnose_error, check_system_health, auto_cleanup_old_jobs

log = logging.getLogger("nexus.pipeline")


async def _run_sync(func, *args, **kwargs):
    """Run a synchronous function in a thread to avoid blocking the event loop."""
    return await asyncio.to_thread(func, *args, **kwargs)


def _generate_hook_text(clip: Dict, transcript: Dict, clip_idx: int) -> Optional[str]:
    """Generate a hook text overlay from the first segment of the clip."""
    cs = clip.get("start", 0)
    ce = clip.get("end", cs + 60)
    
    segments = transcript.get("segments", [])
    clip_segs = [s for s in segments if s.get("end", 0) > cs and s.get("start", 0) < ce]
    
    if not clip_segs:
        return None
    
    # Use the first segment's text as hook (first 60 chars)
    first_text = clip_segs[0].get("text", "").strip()
    if len(first_text) > 60:
        # Try to cut at a word boundary
        cut = first_text[:60].rfind(" ")
        if cut > 20:
            first_text = first_text[:cut] + "..."
        else:
            first_text = first_text[:57] + "..."
    
    # Only show hook for first 2 clips
    if clip_idx >= 2:
        return None
    
    if not first_text:
        return None
    
    return first_text.upper()


async def run_pipeline(
    url: str,
    job_id: str,
    progress_callback: Optional[Callable] = None,
    **kwargs,
) -> Dict:
    """Run the NexuX V8.0 smart pipeline.

    Stages:
    1. Smart Metadata (0-5%) — instant, no download
    2. Caption Fetch (5-10%) — YouTube auto-captions or audio-only whisper
    3. AI Moment Selection (10-20%) — find viral moments from transcript
    4. Smart Partial Download (20-40%) — download ONLY selected sections
    5. Parallel Rendering (40-85%) — all clips rendered simultaneously
    6. Quality Gate + Assembly (85-100%)

    All heavy sync operations dispatched to threads via asyncio.to_thread().
    """
    result = {
        "job_id": job_id,
        "status": "processing",
        "input_url": url,
        "stages": {},
        "clips": [],
        "output_path": None,
        "error": None,
        "critiques": [],
        "pipeline_version": "8.0",
    }

    pipeline_start = time.time()

    async def _progress(stage: str, pct: float, **data):
        elapsed = time.time() - pipeline_start
        if pct > 0:
            eta = elapsed / pct * (100 - pct)
            data["elapsed_seconds"] = round(elapsed, 1)
            data["eta_seconds"] = round(eta, 1)
        if progress_callback:
            await progress_callback(stage, pct, **data)

    # Auto-cleanup old jobs
    try:
        auto_cleanup_old_jobs(max_age_hours=24)
    except Exception:
        pass

    try:
        # ── 1. Smart Metadata ──
        await _progress("metadata", 0, message="Fetching video info...")
        video_info = await _run_sync(get_video_info, url)
        result["video_info"] = video_info
        total_duration = video_info.get("duration", 0)
        await _progress("metadata", 5, title=video_info.get("title", ""),
                         duration=total_duration,
                         message="Video info retrieved")

        # ── 2. Caption Fetch (FAST PATH) ──
        await _progress("transcribing", 5, message="Fetching captions...")

        language = kwargs.get("language")
        transcript = await _run_sync(fetch_auto_captions, url, job_id, language)

        if transcript:
            # FAST PATH: YouTube auto-captions available
            result["stages"]["transcribe"] = {
                "status": "ok",
                "source": "youtube_auto",
                "segments": len(transcript.get("segments", [])),
                "fast_path": True,
            }
            await _progress("transcribing", 10,
                           source="youtube_auto",
                           segments=len(transcript.get("segments", [])),
                           message="Auto-captions fetched (no whisper needed!)")
            log.info(f"[Pipeline] Auto-captions: {len(transcript['segments'])} segments — FAST PATH ✅")

        else:
            # FALLBACK: Download audio-only, then whisper transcribe
            await _progress("transcribing", 7, message="Downloading audio for transcription...")
            audio_path = await _run_sync(
                retry, download_audio_only, url, job_id, max_retries=MAX_RETRIES
            )

            await _progress("transcribing", 9, message="Transcribing with faster-whisper...")
            transcript = await _run_sync(
                retry, transcribe, audio_path, job_id,
                language=language,
                diarization=kwargs.get("diarization", True),
                max_retries=MAX_RETRIES
            )
            result["stages"]["transcribe"] = {
                "status": "ok",
                "source": "whisper",
                "segments": len(transcript.get("segments", [])),
                "fast_path": False,
            }
            await _progress("transcribing", 10,
                           source="whisper",
                           segments=len(transcript.get("segments", [])),
                           message="Transcription complete")

        segments = transcript.get("segments", [])
        if not segments:
            raise RuntimeError("No transcript segments — cannot analyze content")

        # ── 3. AI Moment Selection ──
        await _progress("analyzing", 10, message="AI selecting viral moments...")

        # Optional manual time range override
        manual_ranges = kwargs.get("manual_ranges")  # [{start, end}, ...]

        if manual_ranges:
            # User selected specific time ranges manually
            clips = []
            for i, r in enumerate(manual_ranges):
                clips.append({
                    "start": r["start"],
                    "end": r["end"],
                    "score": 100.0,  # User-selected = top priority
                    "reason": "Manual selection",
                    "rank": i + 1,
                })
            log.info(f"[Pipeline] Manual selection: {len(clips)} clips")
        else:
            # AI automatic selection
            clips = await _run_sync(
                analyze_content,
                transcript,
                target_duration=kwargs.get("target_duration", 60),
                max_clips=kwargs.get("clip_count", 5),
                use_ai_scoring=kwargs.get("ai_scoring", True),
                editorial_enrichment=True,
            )

        if not clips:
            raise RuntimeError("No clips found — analysis returned empty")

        result["stages"]["analyze"] = {
            "status": "ok",
            "clips_found": len(clips),
            "top_score": round(clips[0].get("score", 0), 2) if clips else 0,
        }
        await _progress("analyzing", 20,
                        clips_found=len(clips),
                        top_score=round(clips[0].get("score", 0), 2) if clips else 0,
                        message=f"Found {len(clips)} viral moments")

        # ── 3.5 Creative Brain — intelligent editing decisions ──
        creative_result = await _run_sync(
            choose_creative_palette, transcript, clips,
            {
                "color_grade": kwargs.get("color_grade"),
                "subtitle_style": kwargs.get("subtitle_style"),
            }
        )
        result["creative"] = {
            "palette": creative_result["palette"],
            "mood": creative_result["palette"].get("mood"),
            "run_count": creative_result.get("memory_run_count", 0),
        }
        log.info(f"[Pipeline] Creative Brain: mood={creative_result['palette'].get('mood')}")

        # ── 4. Smart Partial Download ──
        await _progress("downloading", 20,
                       message=f"Downloading {len(clips)} sections (partial)...")

        async def _download_one(clip_idx: int, clip: Dict) -> Optional[Path]:
            """Download a single clip section."""
            try:
                path = await _run_sync(
                    download_clip_section, url, job_id,
                    clip["start"], clip["end"], clip_idx,
                    2160 if kwargs.get("output_resolution") in ("uhd", "4k") else 1080,
                )
                return path
            except Exception as e:
                log.warning(f"[Pipeline] Section {clip_idx} download failed: {e}")
                return None

        # Download ALL sections in parallel
        download_tasks = [_download_one(i, c) for i, c in enumerate(clips)]
        section_paths = await asyncio.gather(*download_tasks)

        # Filter out failed downloads
        valid_clips = []
        valid_paths = []
        for i, (clip, path) in enumerate(zip(clips, section_paths)):
            if path:
                valid_clips.append((i, clip, path))
                valid_paths.append(path)

        if not valid_clips:
            raise RuntimeError("All section downloads failed")

        result["stages"]["download"] = {
            "status": "ok",
            "sections_downloaded": len(valid_clips),
            "sections_failed": len(clips) - len(valid_clips),
            "partial_download": True,
        }

        total_download_size = sum(get_file_size_mb(p) for _, _, p in valid_clips)
        await _progress("downloading", 40,
                       sections=len(valid_clips),
                       total_mb=round(total_download_size, 1),
                       message="All sections downloaded")

        # ── 5. Parallel Rendering ──
        await _progress("rendering", 40,
                       message=f"Rendering {len(valid_clips)} clips in parallel...")

        style_config = {
            "subtitle_style": kwargs.get("subtitle_style", "karaoke"),
            "font": kwargs.get("font", "Arial"),
            "font_size": kwargs.get("font_size", 16),
            "primary_color": kwargs.get("primary_color", "#ffffff"),
            "highlight_color": kwargs.get("highlight_color", "#ffeb3b"),
            "stroke_color": kwargs.get("stroke_color", "#000000"),
            "stroke_width": kwargs.get("stroke_width", 2),
            "position": kwargs.get("position", "bottom"),
            "animation": kwargs.get("animation", "pop"),
            "aspect_ratio": kwargs.get("aspect_ratio", "9:16"),
            "emoji_enabled": kwargs.get("emoji_enabled", True),
        }

        async def _render_one(clip_idx: int, clip: Dict, section_path: Path) -> Dict:
            """Render a single clip with PROFESSIONAL quality — 4-pass rendering."""
            try:
                # Get per-clip creative decisions
                clip_creative = creative_result["clip_decisions"][clip_idx] if clip_idx < len(creative_result["clip_decisions"]) else {}
                
                # Generate hook text from first segment of this clip
                hook_text = _generate_hook_text(clip, transcript, clip_idx)
                
                out_path = await _run_sync(
                    render_clip_pro, section_path, job_id, clip, transcript,
                    style_config, clip_idx,
                    None,  # face_data — not available for partial downloads
                    clip_creative.get("color_grade", kwargs.get("color_grade", "none")),
                    kwargs.get("auto_zoom", True),
                    kwargs.get("video_codec", "h264"),
                    kwargs.get("audio_codec", "aac"),
                    clip_creative,  # creative config per clip
                    hook_text,  # hook text overlay
                    True,  # SFX enabled
                    kwargs.get("output_resolution", "hd"),
                )
                return {
                    "clip_index": clip_idx,
                    "path": str(out_path),
                    "start": clip["start"],
                    "end": clip["end"],
                    "score": clip.get("score", 0),
                    "reason": clip.get("reason", ""),
                    "status": "ok",
                }
            except Exception as e:
                log.error(f"[Pipeline] Render {clip_idx} failed: {e}")
                return {
                    "clip_index": clip_idx,
                    "error": str(e),
                    "status": "failed",
                }

        # Render ALL clips in parallel
        render_tasks = [_render_one(i, c, p) for i, c, p in valid_clips]
        render_results = await asyncio.gather(*render_tasks)

        # Filter successful renders
        successful_clips = [r for r in render_results if r.get("status") == "ok"]
        result["stages"]["render"] = {
            "status": "ok",
            "clips_rendered": len(successful_clips),
            "clips_failed": len(render_results) - len(successful_clips),
            "parallel": True,
        }

        if not successful_clips:
            raise RuntimeError("All renders failed")

        # Update progress per clip rendered
        render_pct = 40 + int(len(successful_clips) / max(len(valid_clips), 1) * 40)
        await _progress("rendering", render_pct,
                        clips_rendered=len(successful_clips),
                        message=f"Rendered {len(successful_clips)}/{len(valid_clips)} clips")

        # ── 6. Quality Gate (Quick) ──
        await _progress("critique", 80, message="Quality check...")

        final_clips = []
        critiques = []

        for r in successful_clips:
            clip = next((c for i, c, p in valid_clips if i == r["clip_index"]), None)
            if clip:
                # Quick critic check
                critique = await _run_sync(
                    evaluate_clip, clip, r["clip_index"],
                    transcript.get("segments", []), total_duration,
                    transcript.get("segments", []), r["path"],
                    revision_count=0,
                )

                if critique.verdict in ("GOLD", "ACCEPTABLE"):
                    final_clips.append(r["path"])
                    critiques.append({
                        "clip_index": r["clip_index"],
                        "verdict": critique.verdict,
                        "score": round(critique.score, 3),
                        "dimensions": {k: round(v, 3) for k, v in critique.dimensions.items()},
                        "issues": critique.issues,
                    })
                    log.info(f"[Pipeline] Clip {r['clip_index']}: {critique.verdict} ✅")
                elif critique.verdict == "NEEDS_REVISION" and critique.should_retry:
                    # Try one revision
                    revised_clip = await _run_sync(
                        apply_revision_directives, clip,
                        critique.revision_directives,
                        clips, transcript.get("segments", []), total_duration
                    )
                    if revised_clip:
                        try:
                            # Re-download the revised section if time range changed
                            if revised_clip["start"] != clip["start"] or revised_clip["end"] != clip["end"]:
                                revised_path = await _run_sync(
                                    download_clip_section, url, job_id,
                                    revised_clip["start"], revised_clip["end"],
                                    r["clip_index"],
                                )
                                section_path = revised_path
                            else:
                                section_path = Path(r["path"])

                            revised_render = await _run_sync(
                                render_clip, section_path, job_id, revised_clip,
                                transcript, style_config, r["clip_index"],
                                None, kwargs.get("color_grade", "none"),
                                kwargs.get("auto_zoom", True),
                                kwargs.get("video_codec", "h264"),
                                kwargs.get("audio_codec", "aac"),
                            )
                            final_clips.append(str(revised_render))
                            critiques.append({
                                "clip_index": r["clip_index"],
                                "verdict": "REVISED",
                                "score": round(critique.score, 3),
                                "revised": True,
                                "issues": critique.issues,
                            })
                        except Exception as e:
                            log.warning(f"[Pipeline] Revision failed: {e}")
                            final_clips.append(r["path"])
                            critiques.append({
                                "clip_index": r["clip_index"],
                                "verdict": "WEAK_BEST_AVAILABLE",
                                "score": round(critique.score, 3),
                                "issues": critique.issues,
                            })
                else:
                    # REJECT — skip this clip
                    critiques.append({
                        "clip_index": r["clip_index"],
                        "verdict": critique.verdict,
                        "score": round(critique.score, 3),
                        "issues": critique.issues,
                        "skipped": True,
                    })
                    log.warning(f"[Pipeline] Clip {r['clip_index']}: {critique.verdict} — SKIPPED")
            else:
                final_clips.append(r["path"])

        result["stages"]["critique"] = {
            "status": "ok",
            "gold": sum(1 for c in critiques if c.get("verdict") == "GOLD"),
            "acceptable": sum(1 for c in critiques if c.get("verdict") == "ACCEPTABLE"),
            "revised": sum(1 for c in critiques if c.get("revised")),
            "weak": sum(1 for c in critiques if c.get("verdict") in ("WEAK_BEST_AVAILABLE", "REJECT")),
            "skipped": sum(1 for c in critiques if c.get("skipped")),
        }
        result["critiques"] = critiques
        result["clip_candidates"] = [
            {
                "path": r["path"],
                "start": r.get("start", 0),
                "end": r.get("end", 60),
                "score": r.get("score", 0),
                "reason": r.get("reason", ""),
            }
            for r in successful_clips if r.get("path")
        ]
        # Diarized transcript for speaker map / inline correction in editor
        result["transcript_segments"] = [
            {
                "start": s.get("start", 0),
                "end": s.get("end", 0),
                "text": s.get("text", ""),
                "speaker": s.get("speaker") or "SPEAKER_00",
            }
            for s in segments[:5000] if isinstance(s, dict)
        ]
        await _progress("critique", 85,
                        gold=result["stages"]["critique"]["gold"],
                        acceptable=result["stages"]["critique"]["acceptable"],
                        message="Quality check complete")

        # ── 7. Audio Enhancement (Optional) ──
        if kwargs.get("normalize_audio", False) and final_clips:
            await _progress("enhancing", 88, message="Enhancing audio...")
            try:
                enhanced_clips = []
                for clip_path in final_clips:
                    enhanced = await _run_sync(enhance_audio, Path(clip_path), job_id)
                    enhanced_clips.append(str(enhanced) if enhanced else clip_path)
                final_clips = enhanced_clips
                result["stages"]["audio_enhancement"] = {"status": "ok"}
            except Exception as e:
                log.warning(f"[Pipeline] Audio enhancement failed: {e}")
                result["stages"]["audio_enhancement"] = {"status": "skipped", "error": str(e)}

        # ── 8. Final Assembly ──
        await _progress("finalizing", 90, message="Assembling final output...")

        if len(final_clips) == 0:
            raise RuntimeError("No clips passed quality gate")

        if len(final_clips) == 1:
            # Single clip — just use it directly
            final_path = final_clips[0]
        else:
            # Multiple clips — concatenate
            final_path = await _run_sync(
                concatenate_clips, final_clips, job_id,
                kwargs.get("video_codec", "h264"),
                kwargs.get("audio_codec", "aac"),
            )

        result["output_path"] = final_path
        result["clips"] = final_clips
        result["stages"]["assembly"] = {"status": "ok"}
        result["status"] = "completed"

        elapsed = time.time() - pipeline_start
        result["total_time_seconds"] = round(elapsed, 1)

        await _progress("complete", 100,
                        output_path=final_path,
                        total_time=round(elapsed, 1),
                        clips_count=len(final_clips),
                        message="Complete!")

        log.info(f"[Pipeline] V8.0 complete in {elapsed:.1f}s — {len(final_clips)} clips")

        # Record creative outcome for learning
        avg_score = sum(c.get("score", 0) for c in critiques) / max(len(critiques), 1)
        palette_name = creative_result["palette"].get("mood", "unknown")
        try:
            record_outcome(palette_name, avg_score, success=True)
        except Exception:
            pass

    except Exception as e:
        log.exception(f"[Pipeline] FAILED: {e}")
        result["status"] = "failed"
        result["error"] = str(e)
        # Record failed creative outcome
        try:
            palette_name = creative_result["palette"].get("mood", "unknown") if creative_result else "unknown"
            record_outcome(palette_name, 0, success=False)
        except Exception:
            pass
        await _progress("error", 100, error=str(e), message="Pipeline failed")

    return result
