from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from analysis_bundle import build_analysis_bundle
from app import (
    app, DATA, JOBS, OUTPUTS, build_candidates, ffprobe, editorial_metadata,
    to_dict, sample_faces, SubjectObservation, build_camera_path, path_to_dict,
    download_youtube, rerank_candidates, transcribe_local,
)
from caption_runtime import render_ass_safe
from captions import PRESETS
from compositor import build_final_filter, run_ffmpeg, spec_for_aspect_ratio
from contracts import CompatJob, GenerateRequest
from job_store import read as atomic_read, recover_interrupted, update as atomic_update
from process_supervisor import terminate as terminate_process
from timeline import build_timeline, ffmpeg_filter_for_timeline
from vision_quality import inspect_render, detect_scene_changes, detect_face_subjects, visual_quality

router = APIRouter(prefix="/api")


def _job_path(job_id: str) -> Path:
    if not job_id or not all(c in "0123456789abcdef" for c in job_id) or len(job_id) != 32:
        raise HTTPException(422, "Invalid job_id")
    return JOBS / f"{job_id}.json"


def _read(job_id: str) -> dict[str, Any]:
    path = _job_path(job_id)
    if not path.exists():
        raise HTTPException(404, "Job not found")
    return atomic_read(JOBS, job_id)


def _write(job: dict[str, Any]) -> dict[str, Any]:
    return atomic_update(JOBS, job)


def _set(job: dict[str, Any], **updates: Any) -> dict[str, Any]:
    current = atomic_update(JOBS, job, **updates)
    job.clear()
    job.update(current)
    return job


def _relative_output(path: Path) -> str:
    return f"/output/{path.name}"


def _hex_to_ass(value: str, fallback: str) -> str:
    candidate = value.strip() if isinstance(value, str) else ""
    if len(candidate) != 7 or not candidate.startswith("#"):
        candidate = fallback
    rgb = candidate[1:]
    r, g, b = rgb[0:2], rgb[2:4], rgb[4:6]
    return f"&H00{b}{g}{r}".upper()


def _style_overrides(req: GenerateRequest) -> dict[str, Any]:
    return {"font":req.font,"size":req.font_size,"primary":_hex_to_ass(req.primary_color,"#FFFFFF"),"highlight":_hex_to_ass(req.highlight_color,"#FFD700"),"outline":_hex_to_ass(req.stroke_color,"#000000"),"outline_width":req.stroke_width,"position":req.position,"animation":req.animation}


def _camera_path_for_request(video: Path, clip: dict[str, Any], timeline: Any, req: GenerateRequest) -> list[Any]:
    if not req.face_tracking:
        return []
    observations = sample_faces(video, float(clip["start"]), float(clip["end"]), sample_fps=3.0)
    mapped: list[SubjectObservation] = []
    for obs in observations:
        output_time = timeline.source_to_output(obs.time)
        if output_time is not None:
            mapped.append(SubjectObservation(output_time, obs.x, obs.y, obs.w, obs.h, obs.confidence, obs.kind))
    points = build_camera_path(mapped)
    if req.auto_zoom or not points:
        return points
    return [replace(point, crop_w=0.92) for point in points]


def _render_with_spec(video: Path, job: dict[str, Any], clip: dict[str, Any], output: Path, timeline: Any, req: GenerateRequest) -> dict[str, Any]:
    spec = spec_for_aspect_ratio(req.aspect_ratio)
    ass = output.with_suffix(".ass")
    editorial = editorial_metadata(clip["text"], emoji_enabled=req.emoji_enabled)
    style = PRESETS.get(req.subtitle_style, PRESETS["hormozi"])
    selected_animation = req.animation or style.get("animation", "pop")
    render_ass_safe(job["transcript"],timeline,ass,preset=req.subtitle_style if req.subtitle_style in PRESETS else "hormozi",font=req.font,headline=editorial.headline,emoji=editorial.emoji,canvas_w=spec.width,canvas_h=spec.height,overrides={**_style_overrides(req),"animation":selected_animation})
    media = job.get("meta") or ffprobe(video)
    video_stream = next((s for s in media.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video_stream:
        raise RuntimeError("Video stream dimensions unavailable")
    source_w, source_h = int(video_stream["width"]), int(video_stream["height"])
    camera_points = _camera_path_for_request(video,clip,timeline,req)
    edl_graph = ffmpeg_filter_for_timeline(timeline)[0]
    filter_complex = build_final_filter(edl_graph,camera_points,ass,source_w,source_h,spec)
    run_ffmpeg(video,output,filter_complex,spec=spec,job_id=job.get("job_id"),normalize_audio=req.normalize_audio)
    quality = inspect_render(output,expected_width=spec.width,expected_height=spec.height,min_duration=max(0.1,timeline.duration_after*0.98),max_duration=timeline.duration_after+0.25)
    if quality["verdict"] != "APPROVED":
        raise RuntimeError(f"Render quality gate failed: {json.dumps(quality,ensure_ascii=False)}")
    return {"editorial":to_dict(editorial),"caption_preset":req.subtitle_style,"caption_animation":selected_animation,"camera":{"face_tracking":req.face_tracking,"auto_zoom":req.auto_zoom,"points":path_to_dict(camera_points),"point_count":len(camera_points)},"source_dimensions":{"width":source_w,"height":source_h},"output_dimensions":{"width":spec.width,"height":spec.height},"quality":quality,"broll":False,"audio_normalized":req.normalize_audio}


class CancellationRegistry(dict[str, bool]):
    def __setitem__(self,job_id:str,value:bool)->None:
        super().__setitem__(job_id,value)
        if value:
            terminate_process(f"download:{job_id}"); terminate_process(f"transcribe:{job_id}"); terminate_process(f"render:{job_id}")


CANCEL_FLAGS = CancellationRegistry()


async def _run_generation(job_id: str, req: GenerateRequest) -> None:
    job = _read(job_id)
    try:
        CANCEL_FLAGS.setdefault(job_id,False)
        if job.get("status")=="cancelled" or CANCEL_FLAGS.get(job_id): return
        _set(job,status="processing",stage="downloading",progress=5)
        job_dir=DATA/"uploads"/job_id
        video,meta=await asyncio.to_thread(download_youtube,req.youtube_url,job_dir,1080,job_id)
        media=ffprobe(video)
        _set(job,stage="transcribing",progress=25,video_path=str(video),meta=media)
        if CANCEL_FLAGS.get(job_id): _set(job,status="cancelled",stage="cancelled"); return
        transcript=await asyncio.to_thread(transcribe_local,video,req.language)
        _set(job,stage="analyzing",progress=45,transcript=transcript)
        if CANCEL_FLAGS.get(job_id): _set(job,status="cancelled",stage="cancelled"); return
        candidates=build_candidates(transcript["segments"])
        if not candidates: raise RuntimeError("No viable 20-60 second candidates found")
        duration=float(media.get("format",{}).get("duration") or 0.0)
        scenes=await asyncio.to_thread(detect_scene_changes,video,0.0,duration or None)
        candidates=rerank_candidates(candidates,scene_boundaries=scenes,target_duration=float(req.target_duration),limit=min(20,max(req.clip_count*4,10)),video=video,transcript=transcript)
        candidates.sort(key=lambda c:float(c.get("editorial_rank",0.0)),reverse=True)
        candidates=candidates[:req.clip_count]
        if not candidates: raise RuntimeError("Editorial ranking produced no candidates")
        subject_samples=[]
        for candidate in candidates:
            samples=await asyncio.to_thread(detect_face_subjects,video,float(candidate["start"]),float(candidate["end"]))
            subject_samples.append({"candidate_id":candidate["id"],"observations":samples})
        bundle=build_analysis_bundle(transcript,candidates,scenes,subject_samples)
        _set(job,stage="rendering",progress=65,candidates=candidates,selected_candidate_id=candidates[0]["id"],analysis_bundle=bundle.to_dict(),vision={"scene_count":len(scenes),"scenes":scenes,"subject_samples":subject_samples})
        rendered=[]; render_meta=[]
        for idx,candidate in enumerate(candidates):
            if CANCEL_FLAGS.get(job_id): _set(job,status="cancelled",stage="cancelled"); return
            timeline=await asyncio.to_thread(build_timeline,video,transcript,candidate)
            output=OUTPUTS/f"{job_id}_clip_{idx+1:02d}.mp4"
            info=await asyncio.to_thread(_render_with_spec,video,{**job,"transcript":transcript,"meta":media},candidate,output,timeline,req)
            rendered.append(_relative_output(output)); render_meta.append({"clip_id":candidate["id"],"output":_relative_output(output),**info})
            _set(job,progress=65+((idx+1)/max(1,len(candidates)))*30,clips=rendered,render_meta=render_meta)
        _set(job,status="completed",stage="complete",progress=100,output_path=rendered[0] if rendered else None,clips=rendered,render_meta=render_meta)
    except Exception as exc:
        _set(job,status="failed",stage="failed",error=str(exc))
    finally:
        CANCEL_FLAGS.pop(job_id,None)


recover_interrupted(JOBS)
app.include_router(router)
