from __future__ import annotations

import ast
import importlib.util
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = [
    "app.py",
    "server.py",
    "captions.py",
    "compositor.py",
    "editorial.py",
    "editorial_ranker.py",
    "audio_intelligence.py",
    "fonts.py",
    "scoring.py",
    "semantic_ranker.py",
    "timeline.py",
    "virtual_camera.py",
    "vision_quality.py",
    "youtube.py",
    "face_sampling.py",
]
AGENT_ROOT = ROOT.parent / "backend" / "agents"


def compile_all() -> list[str]:
    failures: list[str] = []
    for name in REQUIRED:
        path = ROOT / name
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except Exception as exc:  # pragma: no cover
            failures.append(f"{name}: {exc}")
    return failures


def check_tools() -> list[str]:
    return [tool for tool in ("ffmpeg", "ffprobe", "yt-dlp") if shutil.which(tool) is None]


def check_imports() -> list[str]:
    modules = ("fastapi", "pydantic", "cv2", "numpy", "faster_whisper")
    return [module for module in modules if importlib.util.find_spec(module) is None]


def check_agent_integrity() -> list[str]:
    forbidden = {
        "agent_11_scene_segmenter.py": ("i*5", "range(12)"),
        "agent_12_subject_tracker.py": ('"center_x": 950', '"center_y": 500'),
        "agent_13_quality_checker.py": ('"score": 95', '"resolution": "1920x1080"'),
        "agent_21_quality_inspector.py": ('"passed":True', '"passed": True'),
        "agent_20_professional_editor.py": ("setpts=", "zoompan", "hflip", "eq=saturation="),
    }
    failures: list[str] = []
    for filename, needles in forbidden.items():
        path = AGENT_ROOT / filename
        if not path.exists():
            failures.append(f"Missing agent file: {filename}")
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle in text:
                failures.append(f"Forbidden legacy pattern in {filename}: {needle}")
    return failures


def main() -> int:
    syntax_failures = compile_all()
    missing_tools = check_tools()
    missing_imports = check_imports()
    agent_failures = check_agent_integrity()
    if syntax_failures:
        print("SYNTAX FAIL")
        print("\n".join(syntax_failures))
        return 1
    if missing_tools:
        print("MISSING MEDIA TOOLS:", ", ".join(missing_tools))
        return 2
    if missing_imports:
        print("MISSING PYTHON IMPORTS:", ", ".join(missing_imports))
        return 3
    if agent_failures:
        print("AGENT INTEGRITY FAIL")
        print("\n".join(agent_failures))
        return 4
    print("QUALITY GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
