"""
Nexus-Clipper V6.4 — Pipeline Orchestrator
============================================
End-to-end pipeline with editorial consciousness:
1. Download → 2. Vision Analysis → 3. Transcription → 
4. Editorial Analysis → 5. Render → 6. Critic Revision → 7. Final Assembly

The critic revision loop (step 6) is what makes NexuX a conscious editor:
each clip is evaluated, and weak clips are automatically revised.
"""
import time, json
from pathlib import Path
from typing import Dict, Optional, Callable, List
import logging

from .constants import OUTPUT_DIR, MAX_RETRIES
from .utils import retry, get_file_size_mb
from .download import download_youtube, get_video_info
from .transcribe import transcribe
from .vision import analyze_faces, detect_scene_changes, detect_screen_share
from .analyze import analyze_content, batch_analyze_with_ai
from .render import render_clip, concatenate_clips
from .editorial import batch_editorial_analysis
from .critic import evaluate_clip, apply_revision_directives, revision_loop

log = logging.getLogger("nexus.pipeline")


async def run_pipeline(
    url: str,
    job_id: str,
    progress_callback: Optional[Callable] = None,
    **kwargs,
) -> Dict:
    """Run the complete Nexus-Clipper V6.4 pipeline.
    
    Stages:
    1. Download (0-15%)
    2. Face/Scene/Screen Analysis (15-25%)
    3. Transcription (25-55%)
    4. Editorial Analysis (55-70%) — V6.4: now includes editorial consciousness
    5. Rendering (70-85%) — V6.4: smart zoom based on face data
    6. Critic Revision (85-95%) — V6.4: NEW — quality gate with revision loop
    7. Final Assembly (95-100%)
    
    Args:
        url: YouTube video URL
        job_id: Unique job identifier
        progress_callback: Async callback(stage, progress_pct, **data)
        **kwargs: Override pipeline parameters
    
    Returns:
        Dict with job results: status, output_path, clips, stages, critiques
    """
    result = {
        "job_id": job_id,
        "status": "processing",
        "input_url": url,
        "stages": {},
        "clips": [],
        "output_path": None,
        "error": None,
        "critiques": [],  # V6.4: critic evaluations
    }

    async def _progress(stage: str, pct: float, **data):
        if progress_callback:
            await progress_callback(stage, pct, **data)

    try:
        # ── 1. Download ──
        await _progress("downloading", 0)
        video_path = retry(download_youtube, url, job_id, max_retries=MAX_RETRIES)
        video_size = get_file_size_mb(video_path)
        result["stages"]["download"] = {
            "status": "ok", "path": str(video_path),
            "size_mb": round(video_size, 1),
        }
        await _progress("downloading", 15, video_size_mb=round(video_size, 1))

        # ── 2. Vision Analysis ──
        await _progress("vision", 15)
        face_data = []
        scene_data = []
        screen_data = []
        if kwargs.get("face_tracking", True):
            try:
                face_data = retry(analyze_faces, video_path, job_id, max_retries=2)
            except Exception as e:
                log.warning(f"[Pipeline] Face tracking failed: {e}")
        if kwargs.get("scene_detection", True):
            try:
                scene_data = detect_scene_changes(video_path, job_id)
            except Exception as e:
                log.warning(f"[Pipeline] Scene detection failed: {e}")
        if kwargs.get("screen_detection", False):
            try:
                screen_data = detect_screen_share(video_path, job_id)
            except Exception as e:
                log.warning(f"[Pipeline] Screen detection failed: {e}")
        result["stages"]["vision"] = {
            "status": "ok",
            "face_samples": len(face_data),
            "scene_changes": len(scene_data),
            "screen_shares": len(screen_data),
        }
        await _progress("vision", 25)

        # ── 3. Transcription ──
        await _progress("transcribing", 25)
        transcript = retry(
            transcribe, video_path, job_id,
            kwargs.get("language"),
            kwargs.get("diarization", True),
            max_retries=2,
        )
        seg_count = len(transcript.get("segments", []))
        speakers = set(
            s.get("speaker", "SPEAKER_00")
            for s in transcript.get("segments", [])
            if s.get("speaker"))
        result["stages"]["transcribe"] = {
            "status": "ok", "segments": seg_count,
            "speakers": len(speakers),
            "language": transcript.get("language", "?"),
        }
        await _progress("transcribing", 55, segments=seg_count, speakers=len(speakers))

        # ── 4. Editorial Analysis (V6.4) ──
        await _progress("analyzing", 55)
        clips = analyze_content(
            transcript,
            target_duration=kwargs.get("target_duration", 60),
            face_data=face_data if face_data else None,
            scene_data=scene_data if scene_data else None,
            screen_data=screen_data if screen_data else None,
            max_clips=kwargs.get("clip_count", 10),
            use_ai_scoring=kwargs.get("ai_scoring", False),
            editorial_enrichment=True,  # V6.4: Always on
        )
        if not clips:
            raise RuntimeError(
                "No clips found. Try a shorter target_duration "
                "or use a longer video."
            )
        clips = clips[:kwargs.get("clip_count", 3)]
        result["stages"]["analyze"] = {
            "status": "ok", "clips_found": len(clips),
            "top_score": round(clips[0]["score"], 3) if clips else 0,
            "top_editorial": clips[0].get("editorial", {}).get("verdict", "unknown") if clips else "none",
        }
        await _progress("analyzing", 70, clips_found=len(clips))

        # ── 5. Rendering (V6.4: Smart Zoom) ──
        await _progress("rendering", 70, clips_to_render=len(clips))
        rendered = []
        for i, clip in enumerate(clips):
            cp = retry(
                render_clip, video_path, job_id, clip, transcript,
                kwargs, i, face_data if face_data else None,
                kwargs.get("color_grade", "none"),
                kwargs.get("auto_zoom", True),
                kwargs.get("video_codec", "h264"),
                kwargs.get("audio_codec", "aac"),
                max_retries=2,
            )
            rendered.append(cp)
            pct = 70 + int((i + 1) / max(len(clips), 1) * 15)
            await _progress("rendering", pct, clips_done=i+1, clips_total=len(clips))
        if not rendered:
            raise RuntimeError("All render attempts failed.")

        # ── 6. Critic Revision Loop (V6.4: NEW) ──
        await _progress("critique", 85, clips_to_critique=len(rendered))
        
        full_segments = transcript.get("segments", [])
        total_duration = float(full_segments[-1].get("end", 0)) if full_segments else 0
        
        final_clips = []
        critiques = []
        
        for i, (clip, out_path) in enumerate(zip(clips, rendered)):
            critique = evaluate_clip(
                clip, i, full_segments, total_duration, full_segments,
                out_path, revision_count=0
            )
            
            if critique.verdict in ("GOLD", "ACCEPTABLE"):
                final_clips.append(out_path)
                critiques.append({
                    "clip_index": i,
                    "verdict": critique.verdict,
                    "score": round(critique.score, 3),
                    "dimensions": {k: round(v, 3) for k, v in critique.dimensions.items()},
                    "issues": critique.issues,
                })
                log.info(f"[Pipeline] Clip {i}: {critique.verdict} ✅")
            elif critique.verdict == "NEEDS_REVISION" and critique.should_retry:
                # Try to revise
                log.info(f"[Pipeline] Clip {i}: Revising...")
                revised_clip = apply_revision_directives(
                    clip, critique.revision_directives,
                    clips, full_segments, total_duration
                )
                if revised_clip:
                    try:
                        revised_render = retry(
                            render_clip, video_path, job_id, revised_clip, transcript,
                            kwargs, i, face_data if face_data else None,
                            kwargs.get("color_grade", "none"),
                            kwargs.get("auto_zoom", True),
                            kwargs.get("video_codec", "h264"),
                            kwargs.get("audio_codec", "aac"),
                            max_retries=2,
                        )
                        # Re-evaluate the revised clip
                        revised_critique = evaluate_clip(
                            revised_clip, i, full_segments, total_duration, full_segments,
                            revised_render, revision_count=1
                        )
                        if revised_critique.verdict in ("GOLD", "ACCEPTABLE", "NEEDS_REVISION"):
                            final_clips.append(revised_render)
                            critiques.append({
                                "clip_index": i,
                                "verdict": revised_critique.verdict,
                                "score": round(revised_critique.score, 3),
                                "dimensions": {k: round(v, 3) for k, v in revised_critique.dimensions.items()},
                                "issues": revised_critique.issues,
                                "revised": True,
                                "original_score": round(critique.score, 3),
                            })
                            log.info(f"[Pipeline] Clip {i}: Revised to {revised_critique.verdict} ✅")
                        else:
                            # Even revised version is weak — use original
                            final_clips.append(out_path)
                            critiques.append({
                                "clip_index": i,
                                "verdict": "ACCEPTABLE_AFTER_REVISION",
                                "score": round(revised_critique.score, 3),
                                "issues": revised_critique.issues,
                                "revised": True,
                            })
                    except Exception as e:
                        log.warning(f"[Pipeline] Re-render failed: {e}")
                        final_clips.append(out_path)
                        critiques.append({
                            "clip_index": i,
                            "verdict": critique.verdict,
                            "score": round(critique.score, 3),
                            "issues": critique.issues,
                        })
                else:
                    # Can't improve — use original
                    final_clips.append(out_path)
                    critiques.append({
                        "clip_index": i,
                        "verdict": "WEAK_BEST_AVAILABLE",
                        "score": round(critique.score, 3),
                        "issues": critique.issues,
                    })
            else:
                # REJECT but we still need clips — use the best we have
                final_clips.append(out_path)
                critiques.append({
                    "clip_index": i,
                    "verdict": critique.verdict,
                    "score": round(critique.score, 3),
                    "issues": critique.issues,
                })
                log.warning(f"[Pipeline] Clip {i}: {critique.verdict} — using anyway (best available)")
            
            pct = 85 + int((i + 1) / max(len(clips), 1) * 10)
            await _progress("critique", pct, clips_critiqued=i+1, clips_total=len(clips))
        
        result["stages"]["critique"] = {
            "status": "ok",
            "gold": sum(1 for c in critiques if c.get("verdict") == "GOLD"),
            "acceptable": sum(1 for c in critiques if c.get("verdict") == "ACCEPTABLE"),
            "revised": sum(1 for c in critiques if c.get("revised")),
            "weak": sum(1 for c in critiques if c.get("verdict") in ("WEAK_BEST_AVAILABLE", "REJECT")),
        }
        result["critiques"] = critiques

        # ── 7. Final Assembly ──
        await _progress("finalizing", 95)
        final = final_clips[0]
        if len(final_clips) > 1:
            final = concatenate_clips(job_id, final_clips)
        if kwargs.get("normalize_audio", True):
            try:
                from .render import normalize_audio
                norm_path = OUTPUT_DIR / job_id / f"{job_id}_normalized.mp4"
                final = normalize_audio(final, norm_path)
            except Exception as e:
                log.warning(f"[Pipeline] Audio normalization failed: {e}")

        final_str = str(final)
        result["status"] = "completed"
        result["output_path"] = final_str
        result["clips"] = [str(r) for r in final_clips]
        result["stages"]["render"] = {
            "status": "ok", "clips_rendered": len(final_clips),
            "final_path": final_str,
            "final_size_mb": round(get_file_size_mb(final), 1),
        }
        await _progress("completed", 100, output_path=final_str, clips=result["clips"])
        log.info(f"[Pipeline] COMPLETE: {final_str}")
        log.info(f"[Pipeline] Critique summary: "
                 f"{result['stages']['critique']['gold']} GOLD, "
                 f"{result['stages']['critique']['acceptable']} ACCEPTABLE, "
                 f"{result['stages']['critique']['revised']} REVISED, "
                 f"{result['stages']['critique']['weak']} WEAK")
        return result
    except Exception as e:
        err_msg = str(e)
        result["status"] = "failed"
        result["error"] = err_msg
        log.error(f"[Pipeline] FAILED: {err_msg}")
        await _progress("failed", 0, error=err_msg)
        return result
