"""
Nexus-Clipper Premium v4.0 — Pipeline Orchestrator
====================================================
End-to-end pipeline: Download → Analyze → Render
With stage tracking, error recovery, and progress reporting.
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

log = logging.getLogger("nexus.pipeline")


async def run_pipeline(
    url: str,
    job_id: str,
    progress_callback: Optional[Callable] = None,
    **kwargs,
) -> Dict:
    """Run the complete Nexus-Clipper pipeline.
    
    Stages:
    1. Download (0-15%)
    2. Face/Scene/Screen Analysis (15-25%)
    3. Transcription (25-55%)
    4. Content Analysis (55-65%)
    5. Rendering (65-95%)
    6. Final Assembly (95-100%)
    
    Args:
        url: YouTube video URL
        job_id: Unique job identifier
        progress_callback: Async callback(stage, progress_pct, **data)
        **kwargs: Override pipeline parameters
    
    Returns:
        Dict with job results: status, output_path, clips, stages
    """
    result = {
        "job_id": job_id,
        "status": "processing",
        "input_url": url,
        "stages": {},
        "clips": [],
        "output_path": None,
        "error": None,
    }

    async def _progress(stage: str, pct: float, **data):
        if progress_callback:
            await progress_callback(stage, pct, **data)

    try:
        await _progress("downloading", 0)
        video_path = retry(download_youtube, url, job_id, max_retries=MAX_RETRIES)
        video_size = get_file_size_mb(video_path)
        result["stages"]["download"] = {
            "status": "ok", "path": str(video_path),
            "size_mb": round(video_size, 1),
        }
        await _progress("downloading", 15, video_size_mb=round(video_size, 1))

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

        await _progress("analyzing", 55)
        clips = analyze_content(
            transcript,
            target_duration=kwargs.get("target_duration", 60),
            face_data=face_data if face_data else None,
            scene_data=scene_data if scene_data else None,
            screen_data=screen_data if screen_data else None,
            max_clips=kwargs.get("clip_count", 10),
            use_ai_scoring=kwargs.get("ai_scoring", False),
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
        }
        await _progress("analyzing", 65, clips_found=len(clips))

        await _progress("rendering", 65, clips_to_render=len(clips))
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
            pct = 65 + int((i + 1) / max(len(clips), 1) * 25)
            await _progress("rendering", pct, clips_done=i+1, clips_total=len(clips))
        if not rendered:
            raise RuntimeError("All render attempts failed.")

        await _progress("finalizing", 90)
        final = rendered[0]
        if len(rendered) > 1:
            final = concatenate_clips(job_id, rendered)
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
        result["clips"] = [str(r) for r in rendered]
        result["stages"]["render"] = {
            "status": "ok", "clips_rendered": len(rendered),
            "final_path": final_str,
            "final_size_mb": round(get_file_size_mb(final), 1),
        }
        await _progress("completed", 100, output_path=final_str, clips=result["clips"])
        log.info(f"[Pipeline] COMPLETE: {final_str}")
        return result
    except Exception as e:
        err_msg = str(e)
        result["status"] = "failed"
        result["error"] = err_msg
        log.error(f"[Pipeline] FAILED: {err_msg}")
        await _progress("failed", 0, error=err_msg)
        return result
