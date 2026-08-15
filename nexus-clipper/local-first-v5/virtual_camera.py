from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Iterable


@dataclass(frozen=True)
class SubjectObservation:
    time: float
    x: float
    y: float
    w: float
    h: float
    confidence: float = 1.0
    kind: str = "face"


@dataclass(frozen=True)
class CameraPoint:
    time: float
    cx: float
    cy: float
    crop_w: float
    crop_h: float
    confidence: float


def _center(o: SubjectObservation) -> tuple[float, float]:
    return o.x + o.w / 2.0, o.y + o.h / 2.0


def choose_primary_subject(observations: Iterable[SubjectObservation]) -> list[SubjectObservation]:
    """Choose a stable subject track using confidence, size and temporal continuity."""
    obs = sorted(observations, key=lambda x: x.time)
    if not obs:
        return []
    chosen: list[SubjectObservation] = []
    prev: tuple[float, float] | None = None
    for item in obs:
        cx, cy = _center(item)
        area = max(0.0, min(1.0, item.w * item.h))
        if prev is None:
            chosen.append(item)
            prev = (cx, cy)
            continue
        jump = ((cx - prev[0]) ** 2 + (cy - prev[1]) ** 2) ** 0.5
        # Prefer continuity; reject implausible one-frame jumps unless confidence is strong.
        if jump > 0.35 and item.confidence < 0.9:
            continue
        chosen.append(item)
        prev = (cx, cy)
    return chosen


def smooth_camera(points: list[CameraPoint], alpha: float = 0.18) -> list[CameraPoint]:
    """Exponential smoothing with bounded motion to prevent camera jitter."""
    if not points:
        return []
    alpha = max(0.01, min(1.0, alpha))
    out: list[CameraPoint] = []
    px, py = points[0].cx, points[0].cy
    for p in points:
        # Clamp per-sample movement before EMA.
        dx = max(-0.08, min(0.08, p.cx - px))
        dy = max(-0.08, min(0.08, p.cy - py))
        tx, ty = px + dx, py + dy
        sx = px + alpha * (tx - px)
        sy = py + alpha * (ty - py)
        out.append(CameraPoint(p.time, sx, sy, p.crop_w, p.crop_h, p.confidence))
        px, py = sx, sy
    return out


def build_camera_path(
    observations: Iterable[SubjectObservation],
    target_aspect: tuple[int, int] = (9, 16),
    min_crop_width: float = 0.42,
    max_crop_width: float = 0.92,
) -> list[CameraPoint]:
    obs = choose_primary_subject(observations)
    if not obs:
        return []
    target_w, target_h = target_aspect
    aspect = target_w / target_h
    points: list[CameraPoint] = []
    for o in obs:
        cx, cy = _center(o)
        # Keep enough context around the face/subject. Larger subject => tighter crop.
        subject_w = max(o.w, 0.12)
        crop_w = max(min_crop_width, min(max_crop_width, subject_w * 3.4))
        crop_h = min(1.0, crop_w / aspect)
        if crop_h > 1.0:
            crop_h = 1.0
            crop_w = crop_h * aspect
        # Prevent crop from exceeding frame boundaries.
        cx = max(crop_w / 2.0, min(1.0 - crop_w / 2.0, cx))
        cy = max(crop_h / 2.0, min(1.0 - crop_h / 2.0, cy))
        points.append(CameraPoint(o.time, cx, cy, crop_w, crop_h, o.confidence))
    return smooth_camera(points)


def normalize_legacy_faces(face_data: list[dict[str, Any]]) -> list[SubjectObservation]:
    """Convert legacy face-analysis samples to V5 observations."""
    out: list[SubjectObservation] = []
    for sample in face_data:
        faces = sample.get("faces") or []
        if not faces:
            continue
        # Largest/highest-confidence face is used for baseline primary-subject tracking.
        face = max(faces, key=lambda f: (float(f.get("score", 0.0)), float(f.get("w", 0.0)) * float(f.get("h", 0.0))))
        out.append(SubjectObservation(
            time=float(sample.get("time", 0.0)),
            x=float(face.get("x", 0.0)), y=float(face.get("y", 0.0)),
            w=float(face.get("w", 0.0)), h=float(face.get("h", 0.0)),
            confidence=float(face.get("score", 1.0)), kind="face",
        ))
    return out


def fallback_center_path(times: Iterable[float]) -> list[CameraPoint]:
    return [CameraPoint(float(t), 0.5, 0.5, 0.5625, 1.0, 0.0) for t in times]


def path_to_dict(points: Iterable[CameraPoint]) -> list[dict[str, Any]]:
    return [asdict(p) for p in points]
