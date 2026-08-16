from __future__ import annotations

from typing import Any, Mapping


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def plan_visual_direction(*, subjects: list[Mapping[str, Any]] | None = None, scenes: list[Mapping[str, Any]] | None = None, aspect_ratio: str = "9:16", face_tracking: bool = True, auto_zoom: bool = True) -> dict[str, Any]:
    subjects = [dict(item) for item in (subjects or [])]
    scenes = [dict(item) for item in (scenes or [])]
    active = [item for item in subjects if float(item.get("confidence", 1.0) or 0.0) >= 0.5]
    return {
        "director": "visual",
        "aspect_ratio": aspect_ratio,
        "tracking_mode": "subject_tracking" if active and face_tracking else "center_safe_crop",
        "zoom_mode": "adaptive_micro_zoom" if auto_zoom and active else "disabled",
        "subject_count": len(active),
        "scene_count": len(scenes),
        "camera_policy": {"preserve_face_safe_area": True, "avoid_aggressive_crop": True, "max_zoom": 1.12, "smooth_motion": True},
        "confidence": _clamp(0.45 + min(0.4, len(active) * 0.12) + min(0.15, len(scenes) * 0.01)),
        "evidence": {"subjects": len(active), "scenes": len(scenes)},
    }
