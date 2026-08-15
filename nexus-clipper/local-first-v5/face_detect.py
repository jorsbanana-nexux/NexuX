from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2

from virtual_camera import SubjectObservation, build_camera_path


def detect_face_observations(video: Path, start: float, end: float, sample_every: float = 0.25) -> list[SubjectObservation]:
    if end <= start:
        return []
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video: {video}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    if width <= 0 or height <= 0:
        cap.release()
        raise RuntimeError("Invalid video dimensions")
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    if cascade.empty():
        cap.release()
        return []

    out: list[SubjectObservation] = []
    t = max(0.0, start)
    while t < end:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=5, minSize=(max(32, width // 12), max(32, height // 12)))
        if len(faces):
            candidates: list[tuple[float, tuple[int, int, int, int]]] = []
            for x, y, w, h in faces:
                area = (w * h) / float(width * height)
                candidates.append((area, (int(x), int(y), int(w), int(h))))
            candidates.sort(reverse=True, key=lambda item: item[0])
            area, (x, y, w, h) = candidates[0]
            confidence = min(1.0, max(0.35, area * 12.0))
            out.append(SubjectObservation(t, x / width, y / height, w / width, h / height, confidence, "face"))
        t += max(0.05, sample_every)
    cap.release()
    return out


def build_face_camera_path(video: Path, start: float, end: float) -> list[dict[str, Any]]:
    observations = detect_face_observations(video, start, end)
    path = build_camera_path(observations)
    return [
        {"time": p.time, "cx": p.cx, "cy": p.cy, "crop_w": p.crop_w, "crop_h": p.crop_h, "confidence": p.confidence}
        for p in path
    ]
