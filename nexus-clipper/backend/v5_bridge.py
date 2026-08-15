"""Bridge backend compatibility agents to the canonical Local-First V5 modules."""

from __future__ import annotations

import sys
from pathlib import Path

V5_ROOT = Path(__file__).resolve().parent.parent / "local-first-v5"
if str(V5_ROOT) not in sys.path:
    sys.path.insert(0, str(V5_ROOT))

from vision_quality import detect_face_subjects, detect_scene_changes, inspect_render, visual_quality  # noqa: E402

__all__ = ["detect_face_subjects", "detect_scene_changes", "inspect_render", "visual_quality"]
