from __future__ import annotations

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

from scoring import rank_score, score_text
from youtube import download_youtube, probe_youtube

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
UPLOADS = DATA / "uploads"
JOBS = DATA / "jobs"
OUTPUTS = ROOT / "outputs"
for p in (UPLOADS, JOBS, OUTPUTS):
    p.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD = int(os.getenv("MAX_UPLOAD_MB", "1024")) * 1024 * 1024
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

app = FastAPI(title="NexuX Local-First V5", version="5.1.0")


class YouTubeImport(BaseModel):
    url: str = Field(..., min_length=10, max_length=2000)
    max_height: int = Field(1080, ge=360, le=2160)


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


def transcribe_local(video: Path) -> dict[str, Any]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("faster-whisper belum terpasang") from exc
    device = os.getenv("WHISPER_DEVICE", "cpu")
    compute = os.getenv("WHISPER_COMPUTE", "int8" if device == "cpu" else "float16")
    model = WhisperModel(WHISPER_MODEL, device=device, compute_type=compute)
    segments, info = model.transcribe(str(video), word_timestamps=True, vad_filter=True)
    out = []
    for idx, seg in enumerate(segments):
        words = []
        for w in (seg.words or []):
            words.append({"word": w.word, "start": float(w.start), "end": float(w.end)})
        out.append({"id": idx, "start": float(seg.start), "end": float(seg.end), "text": seg.text.strip(), "words": words})
    return {"language": info.language, "segments": out}


def build_candidates(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for i, start_seg in enumerate(segments):
        text_parts = []
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
                    "id": f"clip-{i:04d}-{j:04d}",
                    "start": start_seg["start"],
                    "end": end,
                    "duration": duration,
                    "text": text,
                    "viral_score": round(score.viral, 2),
                    "scores": score.__dict__,
                    "segment_ids": list(range(i, j + 1)),
                })
    result.sort(key=lambda x: x["viral_score"], reverse=True)
    selected = []
    for cand in result:
        if any(not (cand["end"] <= s["start"] or cand["start"] >= s["end"]) for s in selected):
            continue
        selected.append(cand)
        if len(selected) >= 10:
            break
    return selected


def make_ass(job: dict[str, Any], clip: dict[str, Any], out: Path) -> None:
    cs, ce = clip["start"], clip["end"]
    events = []
    for seg in job["transcript"]["segments"]:
        if seg["end"] < cs or seg["start"] > ce:
            continue
        words = seg.get("words") or []
        if not words:
            events.append((max(0, seg["start"] - cs), max(0.3, min(ce - cs, seg["end"] - cs)), seg["text"].upper()))
            continue
        for w in words:
            if w["end"] < cs or w["start"] > ce:
                continue
            events.append((max(0, w["start"] - cs), min(ce - cs, w["end"] - cs), w["word"].strip().upper()))
    header = """[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,72,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,2,2,80,80,320,1\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"""

    def ts(t: float) -> str:
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = t % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    lines = [header]
    for s, e, text in events:
        if e <= s:
            continue
        lines.append(f"Dialogue: 0,{ts(s)},{ts(e)},Default,,0,0,0,,{text}")
    out.write_text("\n".join(lines), encoding="utf-8")


def render(video: Path, job: dict[str, Any], clip: dict[str, Any], output: Path) -> None:
    ass = output.with_suffix(".ass")
    make_ass(job, clip, ass)
    duration = clip["end"] - clip["start"]
    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,ass='{}'".format(
        str(ass).replace("\\", "/").replace(":", "\\:")
    )
    cmd = [
        "ffmpeg", "-y", "-ss", str(max(0, clip["start"])), "-i", str(video), "-t", str(duration),
        "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-2000:] or "FFmpeg render failed")


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "ffprobe": shutil.which("ffprobe") is not None,
        "yt_dlp": shutil.which("yt-dlp") is not None,
        "whisper_model": WHISPER_MODEL,
    }


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
    try:
        video_path, meta = download_youtube(req.url, job_dir, max_height=req.max_height)
        media = ffprobe(video_path)
    except ValueError as exc:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(400, f"YouTube import failed: {exc}") from exc

    job = {
        "job_id": job_id,
        "status": "imported",
        "source": {"type": "youtube", "url": req.url, "metadata": meta},
        "video_path": str(video_path),
        "meta": media,
    }
    save_job(job_id, job)
    return job


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in {".mp4", ".mov", ".mkv", ".webm", ".avi"}:
        raise HTTPException(415, "Unsupported video extension")
    job_id = uuid.uuid4().hex
    target = UPLOADS / job_id / (Path(file.filename or f"video{ext}").name)
    target.parent.mkdir(parents=True, exist_ok=False)
    size = 0
    with target.open("wb") as handle:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD:
                handle.close()
                target.unlink(missing_ok=True)
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
    transcript = transcribe_local(Path(job["video_path"]))
    candidates = build_candidates(transcript["segments"])
    if not candidates:
        raise HTTPException(422, "No 20-60s standalone candidates found")
    job.update({
        "status": "analyzed",
        "transcript": transcript,
        "candidates": candidates,
        "selected_candidate_id": candidates[0]["id"],
    })
    save_job(job_id, job)
    return job


@app.get("/job/{job_id}")
def get_job(job_id: str):
    return load_job(job_id)


@app.post("/render/{job_id}")
def render_job(job_id: str):
    job = load_job(job_id)
    if not job.get("candidates"):
        raise HTTPException(409, "Analyze the job first")
    clip = next((x for x in job["candidates"] if x["id"] == job["selected_candidate_id"]), None)
    if not clip:
        raise HTTPException(422, "Selected clip is invalid")
    output = OUTPUTS / f"{job_id}_{clip['id']}.mp4"
    render(Path(job["video_path"]), job, clip, output)
    job.update({"status": "completed", "output": str(output)})
    save_job(job_id, job)
    return job


@app.get("/download/{job_id}")
def download(job_id: str):
    job = load_job(job_id)
    output = Path(job.get("output", ""))
    if not output.exists():
        raise HTTPException(404, "Output not found")
    return FileResponse(output, media_type="video/mp4", filename=output.name)
