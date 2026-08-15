from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterator

import cv2


def _open(path: Path):
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {path}")
    return cap


def _frame_iter(path: Path, start: float, end: float | None, sample_fps: float) -> Iterator[tuple[float, Any]]:
    cap = _open(path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
    duration = frame_count / fps if frame_count else 0.0
    begin = max(0.0, start)
    finish = duration if end is None else min(end, duration)
    begin_frame = int(begin * fps)
    step_frames = max(1, int(round(fps / max(sample_fps, 0.25))))
    cap.set(cv2.CAP_PROP_POS_FRAMES, begin_frame)
    frame_index = begin_frame
    try:
        while frame_index < int(finish * fps):
            ok, frame = cap.read()
            if not ok or frame is None:
                break
            if (frame_index - begin_frame) % step_frames == 0:
                yield frame_index / fps, frame
            frame_index += 1
    finally:
        cap.release()


def detect_scene_changes(path: Path, start: float = 0.0, end: float | None = None, threshold: float = 0.34, sample_fps: float = 2.0) -> list[dict[str, Any]]:
    scenes: list[dict[str, Any]] = [{"start": max(0.0, start)}]
    previous = None
    for timestamp, frame in _frame_iter(path, start, end, sample_fps):
        gray = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (160, 90))
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        if previous is not None:
            score = float(cv2.absdiff(gray, previous).mean()) / 255.0
            if score >= threshold and timestamp - float(scenes[-1]["start"]) >= 0.25:
                scenes[-1]["end"] = timestamp
                scenes.append({"start": timestamp, "change_score": round(score, 4)})
        previous = gray
    last_end = end
    if last_end is None:
        cap = _open(path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
        last_end = frame_count / fps if frame_count else scenes[-1]["start"]
        cap.release()
    scenes[-1]["end"] = min(float(last_end), max(float(last_end), float(scenes[-1]["start"])))
    return [
        {
            "start": round(float(item["start"]), 3),
            "end": round(float(item["end"]), 3),
            "duration": round(max(0.0, float(item["end"]) - float(item["start"])), 3),
            "change_score": float(item.get("change_score", 0.0)),
        }
        for item in scenes
        if float(item.get("end", 0.0)) >= float(item.get("start", 0.0))
    ]


def detect_face_subjects(path: Path, start: float = 0.0, end: float | None = None, sample_fps: float = 3.0) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    detector = None
    try:
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        detector = cv2.CascadeClassifier(str(cascade_path))
        if detector.empty():
            detector = None
    except (AttributeError, cv2.error):
        detector = None

    previous_gray = None
    for timestamp, frame in _frame_iter(path, start, end, sample_fps):
        height, width = frame.shape[:2]
        faces: list[dict[str, Any]] = []
        if detector is not None:
            gray = cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
            try:
                detections = detector.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=5, minSize=(max(24, width // 12), max(24, height // 12)))
            except cv2.error:
                detections = ()
            for x, y, w, h in sorted(detections, key=lambda rect: rect[2] * rect[3], reverse=True)[:6]:
                area = (w * h) / max(float(width * height), 1.0)
                faces.append({"x": round(x / width, 5), "y": round(y / height, 5), "w": round(w / width, 5), "h": round(h / height, 5), "confidence": round(min(1.0, 0.35 + area * 12.0), 4), "kind": "face"})

        detector_name = "haar"
        if not faces:
            detector_name = "motion"
            gray = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (7, 7), 0)
            if previous_gray is not None:
                delta = cv2.absdiff(gray, previous_gray)
                _, mask = cv2.threshold(delta, 18, 255, cv2.THRESH_BINARY)
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                mask = cv2.dilate(mask, kernel, iterations=2)
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                min_area = max(100.0, width * height * 0.004)
                for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:4]:
                    area = float(cv2.contourArea(contour))
                    if area < min_area:
                        continue
                    x, y, w, h = cv2.boundingRect(contour)
                    faces.append({"x": round(x / width, 5), "y": round(y / height, 5), "w": round(w / width, 5), "h": round(h / height, 5), "confidence": round(min(0.85, max(0.2, area / max(width * height * 0.25, 1.0))), 4), "kind": "motion"})
            previous_gray = gray
        observations.append({"timestamp": round(timestamp, 3), "faces": faces, "detector": detector_name})
    return observations


def visual_quality(path: Path, start: float = 0.0, end: float | None = None, sample_fps: float = 2.0) -> dict[str, Any]:
    from vision_quality import media_stream_summary

    media = media_stream_summary(path)
    brightness: list[float] = []
    sharpness: list[float] = []
    dark_frames = 0
    total = 0
    for _, frame in _frame_iter(path, start, end, sample_fps):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness.append(float(gray.mean()))
        sharpness.append(float(cv2.Laplacian(gray, cv2.CV_64F).var()))
        if float(gray.mean()) < 8.0:
            dark_frames += 1
        total += 1
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
    return {"passed": not issues, "score": round(max(0.0, min(100.0, score)), 2), "media": media, "sampled_frames": total, "avg_brightness": round(avg_brightness, 2), "avg_sharpness": round(avg_sharpness, 2), "dark_frame_ratio": round(black_ratio, 4), "issues": issues}
