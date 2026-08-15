from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2

from virtual_camera import SubjectObservation


def sample_faces(
    video: Path,
    start: float,
    end: float,
    sample_fps: float = 3.0,
) -> list[SubjectObservation]:
    """Sample faces with OpenCV Haar cascade; deterministic fallback is empty."""
    if end <= start or not video.exists():
        return []
    cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(str(cascade_path))
    if detector.empty():
        return []

    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        return []
    observations: list[SubjectObservation] = []
    step = 1.0 / max(sample_fps, 0.5)
    t = start
    try:
        while t < end + 1e-6:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
            ok, frame = cap.read()
            if not ok or frame is None:
                t += step
                continue
            h, w = frame.shape[:2]
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            faces = detector.detectMultiScale(
                gray,
                scaleFactor=1.08,
                minNeighbors=5,
                minSize=(max(24, int(w * 0.05)), max(24, int(h * 0.05))),
            )
            ranked = sorted(faces, key=lambda r: r[2] * r[3], reverse=True)
            for x, y, fw, fh in ranked[:4]:
                observations.append(
                    SubjectObservation(
                        time=float(t),
                        x=float(x) / w,
                        y=float(y) / h,
                        w=float(fw) / w,
                        h=float(fh) / h,
                        confidence=min(1.0, (fw * fh) / max(1.0, w * h * 0.05)),
                        kind="face",
                    )
                )
            t += step
    finally:
        cap.release()
    return observations
