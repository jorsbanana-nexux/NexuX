from __future__ import annotations

from pathlib import Path
from typing import Any

from vision_quality import detect_face_subjects, detect_scene_changes, visual_quality


class VisionService:
    """Canonical dispatch surface for scene, subject, and visual-quality analysis."""

    def scenes(self, video: Path, start: float = 0.0, end: float | None = None) -> list[dict[str, Any]]:
        return detect_scene_changes(video, start, end)

    def subjects(self, video: Path, start: float = 0.0, end: float | None = None) -> list[dict[str, Any]]:
        return detect_face_subjects(video, start, end)

    def quality(self, video: Path, start: float = 0.0, end: float | None = None) -> dict[str, Any]:
        return visual_quality(video, start, end)


vision_service = VisionService()
