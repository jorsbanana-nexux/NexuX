"""Bridge compatibility agents to the V7.0 engine modules.

Provides legacy-compatible function signatures that delegate to the V7.0
engine, plus retains visual_quality/inspect_render from the legacy module
until equivalent V7.0 functions are added.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Legacy root — still needed for visual_quality and inspect_render
LEGACY_ROOT = Path(__file__).resolve().parent.parent / "local-first-v5"
if str(LEGACY_ROOT) not in sys.path:
    sys.path.insert(0, str(LEGACY_ROOT))

# V7.0 engine imports (primary) — these use lazy imports for cv2/mediapipe
from engine.vision import detect_scene_changes as _v7_scene, analyze_faces as _v7_faces  # noqa: E402


def detect_scene_changes(path, start: float = 0.0, end=None, threshold: float = 30.0, sample_fps: float = 2.0):
    """Legacy-compatible wrapper over V7.0 engine.detect_scene_changes."""
    return _v7_scene(Path(path), job_id="bridge", threshold=threshold)


def detect_face_subjects(path, start: float = 0.0, end=None, sample_fps: float = 3.0):
    """Legacy-compatible wrapper over V7.0 engine.analyze_faces."""
    sample_every = max(1, int(30 / sample_fps)) if sample_fps > 0 else 15
    return _v7_faces(Path(path), job_id="bridge", sample_every=sample_every)


def visual_quality(path, start: float = 0.0, end=None, sample_fps: float = 2.0):
    """Lazy-loaded from legacy vision_quality module (requires cv2)."""
    try:
        from vision_quality import visual_quality as _vq  # noqa: E402
        return _vq(Path(path), start, end, sample_fps)
    except ImportError:
        return {"passed": False, "score": 0, "issues": ["cv2 not installed"]}


def inspect_render(path, expected_width=None, expected_height=None, min_duration=None, max_duration=None):
    """Lazy-loaded from legacy vision_quality module (requires cv2)."""
    try:
        from vision_quality import inspect_render as _ir  # noqa: E402
        return _ir(Path(path), expected_width, expected_height, min_duration, max_duration)
    except ImportError:
        return {"checks": {}, "passed": 0, "total": 0, "score": 0, "verdict": "NEEDS_FIX", "error": "cv2 not installed"}


__all__ = ["detect_face_subjects", "detect_scene_changes", "inspect_render", "visual_quality"]
