from __future__ import annotations

import copy
import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from analysis_bundle import build_analysis_bundle
from audio_intelligence import analyze_audio, audio_signals
from captions import render_ass
from compositor import CompositionSpec, build_final_filter, run_ffmpeg
from editorial import to_dict, editorial_metadata
from editorial_ranker import select_diverse
from face_sampling import sample_faces
from fonts import install_font, list_fonts
from scoring import rank_score, score_text
from targeted_retrieval import download_segment, fetch_recon_audio, fetch_youtube_captions, retrieval_summary
from timeline import build_timeline
from transcription import transcribe
from virtual_camera import SubjectObservation, build_camera_path, path_to_dict
from vision_quality import detect_scene_changes, detect_face_subjects, inspect_render, media_stream_summary, tool_state
from youtube import download_youtube, probe_youtube

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
UPLOADS = DATA / "uploads"
JOBS = DATA / "jobs"
OUTPUTS = ROOT / "outputs"
FONTS = ROOT / "assets" / "fonts"
for p in (UPLOADS, JOBS, OUTPUTS, FONTS):
    p.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD = int(os.getenv("MAX_UPLOAD_MB", "1024")) * 1024 * 1024
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

app = FastAPI(title="NexuX Local-First V6", version="6.0.0")


class YouTubeImport(BaseModel):
    url: str = Field(..., min_length=10, max_length=2000)
    max_height: int = Field(1080, ge=360, le=2160)


class RenderOptions(BaseModel):
    preset: str = Field("karaoke", pattern=r"^(karaoke|pop_line|deep_diver)$")
    font_name: str | None = Field(None, max_length=160)
    emoji_enabled: bool = False
    camera_enabled: bool = True


def ffprobe(path: Path) -> dict[str, Any]:
    cmd = ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-1200:] or "FFprobe failed")
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("FFprobe returned malformed JSON") from exc


def save_job(job_id: str, data: dict[str, Any]) -> None:
    (JOBS / f"{job_id}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_job(job_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{32}", job_id):
        raise HTTPException(422, "Invalid job_id")
    path = JOBS / f"{job_id}.json"
    if not path.exists():
        raise HTTPException(404, "Job not found")
    return json.loads(path.read_text(encoding="utf-8"))


def transcribe_local(video: Path, language: str | None = None) -> dict[str, Any]:
    return transcribe(video, language=language)


def _shift_transcript(transcript: dict[str, Any], offset: float) -> dict[str, Any]:
    result = copy.deepcopy(transcript)
    for segment in result.get("segments", []):
        segment["start"] = max(0.0, float(segment.get("start", 0.0)) - offset)
        segment["end"] = max(0.0, float(segment.get("end", 0.0)) - offset)
        for word in segment.get("words", []) or []:
            word["start"] = max(0.0, float(word.get("start", 0.0)) - offset)
            word["end"] = max(0.0, float(word.get("end", 0.0)) - offset)
    result["duration"] = max(0.0, float(result.get("duration", 0.0)) - offset)
    result["source"] = f"{result.get('source', 'unknown')}:shifted"
    return result


def _shift_candidate(candidate: dict[str, Any], offset: float) -> dict[str, Any]:
    result = dict(candidate)
    result["start"] = max(0.0, float(candidate["start"]) - offset)
    result["end"] = max(result["start"], float(candidate["end"]) - offset)
    result["duration"] = result["end"] - result["start"]
    return result


def _ensure_youtube_media(job: dict[str, Any], candidate: dict[str, Any]) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    """Fetch only the selected candidate plus safety handles when full video is absent."""
    existing = job.get("video_path")
    if existing and Path(existing).exists():
        return Path(existing), job, candidate
    source = job.get("source", {})
    url = source.get("url")
    if source.get("type") != "youtube" or not url:
        raise HTTPException(404, "Source media is unavailable")
    path, retrieval = download_segment(
        url,
        Path(job["job_dir"]),
        candidate["id"],
        float(candidate["start"]),
        float(candidate["end"]),
        max_height=int(source.get("max_height", 1080)),
    )
    local_job = copy.deepcopy(job)
    offset = float(retrieval["retrieved_start"])
    local_candidate = _shift_candidate(candidate, offset)
    local_job["video_path"] = str(path)
    local_job["transcript"] = _shift_transcript(job["transcript"], offset)
    local_job["meta"] = ffprobe(path)
    local_job["retrieval"] = {**job.get("retrieval", {}), "last_segment": retrieval}
    return path, local_job, local_candidate


def build_candidates(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for i, start_seg in enumerate(segments):
        text_parts: list[str] = []
        end = start_seg["end"]
        for j in range(i, min(len(segments), i + 18)):
            text_parts.append(segments[j]["text"])
            end = segments[j]["end"]
            duration = end - start_seg["start"]
            if duration > 60:
                break
            if 20 <= duration <= 60:
                text = " ".join(text_parts)
                opening = " ".join(s["text"] for s in segments[i:min(i + 3, j + 1)])
                score = rank_score(score_text(text, opening), duration)
                result.append({
                    "id": f"clip-{i:04d}-{j:04d}", "start": start_seg["start"], "end": end,
                    "duration": duration, "text": text, "viral_score": round(score.viral, 2),
                    "scores": score.__dict__, "segment_ids": list(range(i, j + 1)),
                    "editorial": to_dict(editorial_metadata(text, emoji_enabled=False)),
                })
    result.sort(key=lambda x: x["viral_score"], reverse=True)
    return result


def rerank_candidates(
    candidates: list[dict[str, Any]],
    scene_boundaries: list[dict[str, Any]] | None = None,
    target_duration: float = 45.0,
    limit: int = 10,
    video: Path | None = None,
    transcript: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    audio_profiles: dict[str, dict[str, float]] = {}
    if video is not None:
        segments = (transcript or {}).get("segments", [])
        for candidate in candidates:
            profile = analyze_audio(video, float(candidate["start"]), float(candidate["end"]), speech_segments=segments)
            audio_profiles[candidate["id"]] = audio_signals(profile)
            candidate["audio_profile"] = profile.to_dict()
    return select_diverse(candidates, limit=limit, target_duration=target_duration, scene_boundaries=scene_boundaries, audio_profiles=audio_profiles)


def resolve_candidate(job: dict[str, Any], candidate_id: str | None = None) -> dict[str, Any]:
    wanted = candidate_id or job.get("selected_candidate_id")
    candidate = next((x for x in job.get("candidates", []) if x.get("id") == wanted), None)
    if candidate is None:
        raise HTTPException(422, "Selected clip is invalid or missing")
    return candidate


def _stream_dimensions(media: dict[str, Any]) -> tuple[int, int]:
    for stream in media.get("streams", []):
        if stream.get("codec_type") == "video":
            try:
                return int(stream["width"]), int(stream["height"])
            except (KeyError, TypeError, ValueError):
                break
    raise RuntimeError("Video stream dimensions unavailable")


def _output_camera_points(video: Path, clip: dict[str, Any], timeline: Any, media: dict[str, Any]) -> tuple[list[Any], int, int]:
    width, height = _stream_dimensions(media)
    observations = sample_faces(video, float(clip["start"]), float(clip["end"]), sample_fps=3.0)
    mapped: list[SubjectObservation] = []
    for obs in observations:
        output_time = timeline.source_to_output(obs.time)
        if output_time is None:
            continue
        mapped.append(SubjectObservation(output_time, obs.x, obs.y, obs.w, obs.h, obs.confidence, obs.kind))
    path = build_camera_path(mapped)
    return path, width, height


def render(video: Path, job: dict[str, Any], clip: dict[str, Any], output: Path, timeline: Any, preset: str, font_name: str | None, emoji_enabled: bool, camera_enabled: bool) -> dict[str, Any]:
    ass = output.with_suffix(".ass")
    editorial = editorial_metadata(clip["text"], emoji_enabled=emoji_enabled)
    render_ass(job["transcript"], timeline, ass, preset=preset, font=font_name, headline=editorial.headline, emoji=editorial.emoji)
    media = job.get("meta") or ffprobe(video)
    source_w, source_h = _stream_dimensions(media)
    camera_path: list[Any] = []
    if camera_enabled:
        camera_path, source_w, source_h = _output_camera_points(video, clip, timeline, media)
    edl_graph = getattr(__import__("timeline"), "ffmpeg_filter_for_timeline")(timeline)[0]
    spec = CompositionSpec()
    filter_complex = build_final_filter(edl_graph, camera_path, ass, source_w, source_h, spec)
    run_ffmpeg(video, output, filter_complex, spec=spec)
    quality = inspect_render(output, expected_width=spec.width, expected_height=spec.height, min_duration=max(3.0, timeline.duration_after * 0.98), max_duration=timeline.duration_after + 0.25)
    if quality["verdict"] != "APPROVED":
        raise RuntimeError(f"Render quality gate failed: {json.dumps(quality, ensure_ascii=False)}")
    return {"editorial": to_dict(editorial), "camera": {"enabled": camera_enabled, "points": path_to_dict(camera_path), "point_count": len(camera_path)}, "source_dimensions": {"width": source_w, "height": source_h}, "quality": quality}


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", **tool_state(), "whisper_model": WHISPER_MODEL, "broll": False, "vision_quality": True, "editorial_ranker": True, "audio_intelligence": True, "targeted_retrieval": True, "version": "6.0.0"}


@app.post("/youtube/preview")
def youtube_preview(req: YouTubeImport):
    try:
        return {"status": "ok", "source": "youtube", "video": probe_youtube(req.url)}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(400, f"YouTube preview failed: {exc}") from exc


@app.post("/youtube/import")
def youtube_import(req: YouTubeImport):
    job_id = uuid.uuid4().hex
    job_dir = UPLOADS / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    try:
        meta = probe_youtube(req.url)
        captions = fetch_youtube_captions(req.url, job_dir)
        recon_audio = None
        if captions is None:
            recon_audio = fetch_recon_audio(req.url, job_dir, job_id)
    except ValueError as exc:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(400, f"YouTube reconnaissance failed: {exc}") from exc
    job = {
        "job_id": job_id,
        "job_dir": str(job_dir),
        "status": "reconnaissance_ready",
        "source": {"type": "youtube", "url": req.url, "metadata": meta, "max_height": req.max_height},
        "transcript": captions,
        "recon_audio_path": str(recon_audio) if recon_audio else None,
        "retrieval": {
            "strategy": "caption_first_targeted_media",
            "full_video_downloaded": False,
            "caption_first": captions is not None,
        },
    }
    save_job(job_id, job)
    return {**job, "retrieval": retrieval_summary(job)}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in {".mp4", ".mov", ".mkv", ".webm", ".avi"}:
        raise HTTPException(415, "Unsupported video extension")
    job_id = uuid.uuid4().hex
    target = UPLOADS / job_id / Path(file.filename or f"video{ext}").name
    target.parent.mkdir(parents=True, exist_ok=False)
    size = 0
    with target.open("wb") as handle:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD:
                handle.close(); target.unlink(missing_ok=True)
                raise HTTPException(413, "Upload exceeds MAX_UPLOAD_MB")
            handle.write(chunk)
    try:
        meta = ffprobe(target)
    except Exception as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(422, f"Malformed video: {exc}") from exc
    job = {"job_id": job_id, "status": "uploaded", "source": {"type": "file"}, "video_path": str(target), "meta": meta}
    save_job(job_id, job)
    return job


@app.post("/analyze/{job_id}")
def analyze(job_id: str):
    job = load_job(job_id)
    if job.get("transcript"):
        transcript = job["transcript"]
    elif job.get("recon_audio_path"):
        transcript = transcribe_local(Path(job["recon_audio_path"]))
        job["transcript"] = transcript
    elif job.get("video_path"):
        transcript = transcribe_local(Path(job["video_path"]))
    else:
        raise HTTPException(422, "No reconnaissance transcript or local media available")
    candidates = build_candidates(transcript["segments"])
    if not candidates:
        raise HTTPException(422, "No 20-60s standalone candidates found")
    source = Path(job["video_path"]) if job.get("video_path") else None
    scenes: list[dict[str, Any]] = []
    subjects: list[dict[str, Any]] = []
    if source and source.exists():
        duration = min(float(job.get("meta", {}).get("format", {}).get("duration") or 60.0), 600.0)
        scenes = detect_scene_changes(source, 0.0, duration)
        subjects = detect_face_subjects(source, 0.0, duration)
    ranked = rerank_candidates(candidates, scenes, target_duration=45.0, limit=10, video=source, transcript=transcript)
    bundle = build_analysis_bundle(transcript, ranked, scenes, subjects)
    job.update({
        "status": "analyzed",
        "transcript": transcript,
        "candidates": ranked,
        "selected_candidate_id": ranked[0]["id"],
        "analysis_bundle": bundle.to_dict(),
        "vision": {"scene_count": len(scenes), "scenes": scenes, "subject_samples": subjects},
        "retrieval": {**job.get("retrieval", {}), "candidate_count": len(candidates), "selected_count": len(ranked)},
    })
    save_job(job_id, job)
    return job


@app.get("/timeline/{job_id}/{candidate_id}")
def timeline_preview(job_id: str, candidate_id: str):
    job = load_job(job_id); candidate = resolve_candidate(job, candidate_id)
    try:
        source, local_job, local_candidate = _ensure_youtube_media(job, candidate)
        timeline = build_timeline(source, local_job["transcript"], local_candidate)
    except FileNotFoundError as exc:
        raise HTTPException(404, f"Video not found: {exc}") from exc
    except Exception as exc:
        raise HTTPException(500, f"Timeline analysis failed: {exc}") from exc
    return {"job_id": job_id, "candidate_id": candidate_id, "timeline": timeline.to_dict(), "retrieval": local_job.get("retrieval")}


@app.get("/vision/{job_id}")
def vision_preview(job_id: str):
    job = load_job(job_id)
    candidate = resolve_candidate(job)
    try:
        source, local_job, local_candidate = _ensure_youtube_media(job, candidate)
        media = media_stream_summary(source)
        duration = media["duration"]
        return {"job_id": job_id, "media": media, "scenes": detect_scene_changes(source, 0.0, duration), "subjects": detect_face_subjects(source, 0.0, duration), "retrieval": local_job.get("retrieval")}
    except Exception as exc:
        raise HTTPException(500, f"Vision analysis failed: {exc}") from exc


@app.get("/fonts")
def get_fonts():
    return {"fonts": list_fonts(FONTS)}


@app.post("/fonts")
async def post_font(file: UploadFile = File(...)):
    source = FONTS / f"upload-{uuid.uuid4().hex}{Path(file.filename or '').suffix.lower()}"
    size = 0
    try:
        with source.open("wb") as handle:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > 20 * 1024 * 1024:
                    raise HTTPException(413, "Font file exceeds 20 MB safety limit")
                handle.write(chunk)
        result = install_font(source, FONTS)
        return result
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    finally:
        source.unlink(missing_ok=True)


@app.get("/job/{job_id}")
def get_job(job_id: str):
    return load_job(job_id)


@app.post("/render/{job_id}")
def render_job(job_id: str, options: RenderOptions | None = None):
    job = load_job(job_id)
    candidate = resolve_candidate(job)
    options = options or RenderOptions()
    try:
        source, local_job, local_candidate = _ensure_youtube_media(job, candidate)
        timeline = build_timeline(source, local_job["transcript"], local_candidate)
        output = OUTPUTS / f"{job_id}_{candidate['id']}.mp4"
        render_info = render(source, local_job, local_candidate, output, timeline, options.preset, options.font_name, options.emoji_enabled, options.camera_enabled)
    except Exception as exc:
        raise HTTPException(500, f"Render failed: {exc}") from exc
    job.update({"status": "completed", "output": str(output), "selected_timeline": timeline.to_dict(), "render": {**options.model_dump(), **render_info}, "retrieval": local_job.get("retrieval", job.get("retrieval", {}))})
    save_job(job_id, job)
    return job


@app.get("/download/{job_id}")
def download(job_id: str):
    job = load_job(job_id); output = Path(job.get("output", ""))
    if not output.exists():
        raise HTTPException(404, "Output not found")
    return FileResponse(output, media_type="video/mp4", filename=output.name)
