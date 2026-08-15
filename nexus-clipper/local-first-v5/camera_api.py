from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException

from face_detect import build_face_camera_path


def camera_plan(video_path: str, start: float, end: float) -> dict[str, Any]:
    path = Path(video_path)
    if not path.exists():
        raise HTTPException(404, "Video artifact not found")
    try:
        points = build_face_camera_path(path, start, end)
    except Exception as exc:
        raise HTTPException(500, f"Camera analysis failed: {exc}") from exc
    return {
        "fallback": len(points) == 0,
        "algorithm": "opencv-haar + continuity + EMA smoothing",
        "output": {"width": 1080, "height": 1920},
        "points": points,
    }
