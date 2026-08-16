from __future__ import annotations

import copy
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from fastapi import FastAPI

from analysis_bundle import build_analysis_bundle
from audio_intelligence import analyze_audio, audio_signals
from captions import PRESETS
from editorial import editorial_metadata, to_dict
from editorial_ranker import select_diverse
from face_sampling import sample_faces
from scoring import rank_score, score_text
from transcription import transcribe
from ui_contract import ANIMATIONS, ASPECT_RATIOS, POSITIONS
from virtual_camera import SubjectObservation, build_camera_path, path_to_dict
from youtube import download_youtube

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
UPLOADS = DATA / "uploads"
JOBS = DATA / "jobs"
OUTPUTS = ROOT / "outputs"
FONTS = ROOT / "assets" / "fonts"
for path in (UPLOADS, JOBS, OUTPUTS, FONTS):
    path.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD = int(os.getenv("MAX_UPLOAD_MB", "1024")) * 1024 * 1024
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

app = FastAPI(title="NexuX Local-First V6", version="6.3.0")


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "canonical_runtime": False,
        "runtime_module": "server_compat",
        "whisper_model": WHISPER_MODEL,
    }


@app.get("/api/styles")
async def styles() -> dict[str, Any]:
    return {
        "subtitle_styles": [
            {"id": key, "name": key.replace("_", " ").title(), "preview": {"font": value.get("font"), "font_size": value.get("size"), "animation": value.get("animation")}}
            for key, value in PRESETS.items()
        ],
        "aspect_ratios": list(ASPECT_RATIOS),
        "animations": list(ANIMATIONS),
        "positions": list(POSITIONS),
        "broll": False,
    }


def ffprobe(path: Path) -> dict[str, Any]:
    command = ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1200:] or "FFprobe failed")
    import json
    return json.loads(result.stdout)


def transcribe_local(video: Path, language: str | None = None) -> dict[str, Any]:
    return transcribe(video, language=language)


def build_candidates(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, start_segment in enumerate(segments):
        text_parts: list[str] = []
        end = float(start_segment["end"])
        for end_index in range(index, min(len(segments), index + 18)):
            text_parts.append(str(segments[end_index]["text"]))
            end = float(segments[end_index]["end"])
            duration = end - float(start_segment["start"])
            if duration > 60:
                break
            if 20 <= duration <= 60:
                text = " ".join(text_parts)
                opening = " ".join(s["text"] for s in segments[index:min(index + 3, end_index + 1)])
                score = rank_score(score_text(text, opening), duration)
                result.append({
                    "id": f"clip-{index:04d}-{end_index:04d}",
                    "start": float(start_segment["start"]),
                    "end": end,
                    "duration": duration,
                    "text": text,
                    "viral_score": round(score.viral, 2),
                    "scores": score.__dict__,
                    "segment_ids": list(range(index, end_index + 1)),
                    "editorial": to_dict(editorial_metadata(text, emoji_enabled=False)),
                })
    return sorted(result, key=lambda item: item["viral_score"], reverse=True)


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
        speech_segments = (transcript or {}).get("segments", [])
        for candidate in candidates:
            profile = analyze_audio(
                video,
                float(candidate["start"]),
                float(candidate["end"]),
                speech_segments=speech_segments,
            )
            audio_profiles[candidate["id"]] = audio_signals(profile)
            candidate["audio_profile"] = profile.to_dict()
    return select_diverse(
        candidates,
        limit=limit,
        target_duration=target_duration,
        scene_boundaries=scene_boundaries,
        audio_profiles=audio_profiles,
    )


def ensure_dirs() -> None:
    for path in (UPLOADS, JOBS, OUTPUTS, FONTS):
        path.mkdir(parents=True, exist_ok=True)


def _shift_transcript(transcript: dict[str, Any], offset: float) -> dict[str, Any]:
    result = copy.deepcopy(transcript)
    for segment in result.get("segments", []):
        segment["start"] = max(0.0, float(segment.get("start", 0.0)) - offset)
        segment["end"] = max(0.0, float(segment.get("end", 0.0)) - offset)
        for word in segment.get("words", []) or []:
            word["start"] = max(0.0, float(word.get("start", 0.0)) - offset)
            word["end"] = max(0.0, float(word.get("end", 0.0)) - offset)
    result["duration"] = max(0.0, float(result.get("duration", 0.0)) - offset)
    return result


__all__ = [
    "app",
    "DATA",
    "JOBS",
    "OUTPUTS",
    "build_analysis_bundle",
    "build_candidates",
    "ffprobe",
    "editorial_metadata",
    "to_dict",
    "sample_faces",
    "SubjectObservation",
    "build_camera_path",
    "path_to_dict",
    "download_youtube",
    "rerank_candidates",
    "transcribe_local",
    "MAX_UPLOAD",
    "WHISPER_MODEL",
]