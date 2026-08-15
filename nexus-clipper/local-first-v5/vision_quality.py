from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

import cv2


def _probe(path: Path) -> dict[str, Any]:
    cmd = ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2000:] or "ffprobe failed")
    return json.loads(result.stdout)


def media_stream_summary(path: Path) -> dict[str, Any]:
    info = _probe(path)
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    if not video:
        raise ValueError("No video stream")
    width = int(video.get("width") or 0)
    height = int(video.get("height") or 0)
    fps_text = video.get("avg_frame_rate") or video.get("r_frame_rate") or "0/1"
    try:
        num, den = fps_text.split("/", 1)
        fps = float(num) / max(float(den), 1.0)
    except (ValueError, ZeroDivisionError):
        fps = 0.0
    duration = float(info.get("format", {}).get("duration") or video.get("duration") or 0.0)
    return {
        "path": str(path),
        "width": width,
        "height": height,
        "fps": fps,
        "duration": duration,
        "video_codec": video.get("codec_name"),
        "audio_present": audio is not None,
        "audio_codec": audio.get("codec_name") if audio else None,
        "audio_channels": int(audio.get("channels") or 0) if audio else 0,
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def detect_scene_changes(path: Path, start: float = 0.0, end: float | None = None, threshold: float = 0.34, sample_fps: float = 2.0) -> list[dict[str, Any]]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
    duration = frame_count / fps if frame_count else 0.0
    end = duration if end is None else min(end, duration)
    step = max(1.0 / max(sample_fps, 0.5), 0.05)
    t = max(0.0, start)
    previous = None
    scenes = [{"start": t}]
    try:
        while t < end:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
            ok, frame = cap.read()
            if not ok or frame is None:
                t += step
                continue
            gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (160, 90))
            gray = cv2.GaussianBlur(gray, (5, 5), 0)
            if previous is not None:
                diff = cv2.absdiff(gray, previous)
                score = float(diff.mean()) / 255.0
                if score >= threshold and t - float(scenes[-1]["start"]) >= 0.25:
                    scenes[-1]["end"] = t
                    scenes.append({"start": t, "change_score": round(score, 4)})
            previous = gray
            t += step
    finally:
        cap.release()
    if scenes:
        scenes[-1]["end"] = end
    result = []
    for item in scenes:
        if "end" not in item:
            continue
        result.append({"start": round(float(item["start"]), 3), "end": round(float(item["end"]), 3), "duration": round(float(item["end"] - item["start"]), 3), "change_score": float(item.get("change_score", 0.0))})
    return result


def detect_face_subjects(path: Path, start: float = 0.0, end: float | None = None, sample_fps: float = 3.0) -> list[dict[str, Any]]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
    duration = frame_count / fps if frame_count else 0.0
    end = duration if end is None else min(end, duration)
    detector = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"))
    if detector.empty():
        cap.release()
        return []
    step = max(1.0 / max(sample_fps, 0.5), 0.05)
    t = max(0.0, start)
    observations: list[dict[str, Any]] = []
    try:
        while t < end:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
            ok, frame = cap.read()
            if not ok or frame is None:
                t += step
                continue
            height, width = frame.shape[:2]
            gray = cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
            faces = detector.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=5, minSize=(max(24, width // 12), max(24, height // 12)))
            items = []
            for x, y, w, h in sorted(faces, key=lambda r: r[2] * r[3], reverse=True)[:6]:
                area = (w * h) / max(float(width * height), 1.0)
                items.append({"x": round(x / width, 5), "y": round(y / height, 5), "w": round(w / width, 5), "h": round(h / height, 5), "confidence": round(min(1.0, 0.35 + area * 12.0), 4), "kind": "face"})
            observations.append({"timestamp": round(t, 3), "faces": items})
            t += step
    finally:
        cap.release()
    return observations


def visual_quality(path: Path, start: float = 0.0, end: float | None = None, sample_fps: float = 2.0) -> dict[str, Any]:
    media = media_stream_summary(path)
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {path}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
    duration = frame_count / fps if frame_count else 0.0
    end = duration if end is None else min(end, duration)
    step = max(1.0 / max(sample_fps, 0.5), 0.05)
    t = max(0.0, start)
    brightness: list[float] = []
    sharpness: list[float] = []
    dark_frames = 0
    total = 0
    try:
        while t < end:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
            ok, frame = cap.read()
            if not ok or frame is None:
                t += step
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness.append(float(gray.mean()))
            sharpness.append(float(cv2.Laplacian(gray, cv2.CV_64F).var()))
            if float(gray.mean()) < 8.0:
                dark_frames += 1
            total += 1
            t += step
    finally:
        cap.release()
    if total == 0:
        raise RuntimeError("No decodable video frames")
    avg_brightness = sum(brightness) / len(brightness)
    avg_sharpness = sum(sharpness) / len(sharpness)
    black_ratio = dark_frames / total
    issues: list[str] = []
    if media["width"] < 720 or media["height"] < 720:
        issues.append("low_resolution")
    if media["fps"] < 20:
        issues.append("low_frame_rate")
    if black_ratio > 0.15:
        issues.append("black_or_dark_frames")
    if avg_brightness < 35:
        issues.append("underexposed")
    if avg_brightness > 225:
        issues.append("overexposed")
    if avg_sharpness < 30:
        issues.append("soft_or_blurry")
    score = 100.0
    score -= min(25.0, black_ratio * 100.0)
    score -= 10.0 if avg_brightness < 35 or avg_brightness > 225 else 0.0
    score -= min(15.0, max(0.0, (30.0 - avg_sharpness) * 0.5))
    score -= 10.0 if media["width"] < 720 or media["height"] < 720 else 0.0
    return {
        "passed": not issues,
        "score": round(max(0.0, min(100.0, score)), 2),
        "media": media,
        "sampled_frames": total,
        "avg_brightness": round(avg_brightness, 2),
        "avg_sharpness": round(avg_sharpness, 2),
        "dark_frame_ratio": round(black_ratio, 4),
        "issues": issues,
    }


def inspect_render(path: Path, expected_width: int | None = None, expected_height: int | None = None, min_duration: float | None = None, max_duration: float | None = None) -> dict[str, Any]:
    media = media_stream_summary(path)
    checks: dict[str, dict[str, Any]] = {}
    dimensions_ok = expected_width is None or expected_height is None or (media["width"] == expected_width and media["height"] == expected_height)
    duration_ok = (min_duration is None or media["duration"] >= min_duration) and (max_duration is None or media["duration"] <= max_duration)
    checks["resolution_check"] = {"passed": dimensions_ok, "actual": [media["width"], media["height"]], "expected": [expected_width, expected_height] if expected_width and expected_height else None}
    checks["duration_check"] = {"passed": duration_ok, "actual": round(media["duration"], 3), "min": min_duration, "max": max_duration}
    checks["audio_check"] = {"passed": media["audio_present"], "audio_codec": media["audio_codec"], "channels": media["audio_channels"]}
    visual = visual_quality(path)
    checks["visual_quality"] = {"passed": visual["passed"], "score": visual["score"], "issues": visual["issues"]}
    passed = sum(1 for check in checks.values() if check["passed"])
    total = len(checks)
    return {"checks": checks, "passed": passed, "total": total, "score": round(100.0 * passed / max(total, 1), 2), "verdict": "APPROVED" if passed == total else "NEEDS_FIX", "media": media}


def tool_state() -> dict[str, bool]:
    return {tool: shutil.which(tool) is not None for tool in ("ffmpeg", "ffprobe", "yt-dlp")}
