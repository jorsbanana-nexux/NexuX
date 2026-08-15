from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Iterable


@dataclass(frozen=True)
class Detection:
    time: float
    x: float
    y: float
    w: float
    h: float
    confidence: float


@dataclass(frozen=True)
class TrackPoint:
    time: float
    track_id: int
    x: float
    y: float
    w: float
    h: float
    confidence: float


def _center(d: Detection) -> tuple[float, float]:
    return d.x + d.w / 2.0, d.y + d.h / 2.0


def assign_tracks(detections: Iterable[Detection], max_jump: float = 0.22) -> list[TrackPoint]:
    """Greedy deterministic multi-person identity continuity baseline.

    Detections should be normalized [0,1]. Tracks prefer nearest previous center,
    with a bounded jump; unmatched detections create new tracks.
    """
    ordered = sorted(detections, key=lambda d: d.time)
    active: dict[int, tuple[float, float]] = {}
    last_time: dict[int, float] = {}
    next_id = 0
    out: list[TrackPoint] = []
    for det in ordered:
        cx, cy = _center(det)
        best_id = None
        best_dist = float("inf")
        for tid, (px, py) in active.items():
            dist = hypot(cx - px, cy - py)
            if dist < best_dist and dist <= max_jump and det.time >= last_time.get(tid, -1.0):
                best_dist = dist
                best_id = tid
        if best_id is None:
            best_id = next_id
            next_id += 1
        active[best_id] = (cx, cy)
        last_time[best_id] = det.time
        out.append(TrackPoint(det.time, best_id, det.x, det.y, det.w, det.h, det.confidence))
    return out


def primary_track(points: Iterable[TrackPoint]) -> int | None:
    grouped: dict[int, list[TrackPoint]] = {}
    for p in points:
        grouped.setdefault(p.track_id, []).append(p)
    if not grouped:
        return None
    def score(items: list[TrackPoint]) -> float:
        area = sum(max(0.0, p.w) * max(0.0, p.h) for p in items) / len(items)
        conf = sum(p.confidence for p in items) / len(items)
        duration = items[-1].time - items[0].time if len(items) > 1 else 0.0
        return area * 0.50 + conf * 0.30 + min(1.0, duration / 30.0) * 0.20
    return max(grouped, key=lambda tid: score(grouped[tid]))
