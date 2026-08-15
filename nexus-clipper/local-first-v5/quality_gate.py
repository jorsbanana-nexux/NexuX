from __future__ import annotations

import ast
import importlib.util
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REQUIRED = [
    "app.py",
    "captions.py",
    "compositor.py",
    "editorial.py",
    "fonts.py",
    "scoring.py",
    "timeline.py",
    "virtual_camera.py",
    "youtube.py",
    "face_sampling.py",
]


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
    missing: list[str] = []
    for tool in ("ffmpeg", "ffprobe", "yt-dlp"):
        if shutil.which(tool) is None:
            missing.append(tool)
    return missing


def check_imports() -> list[str]:
    missing: list[str] = []
    for module in ("fastapi", "pydantic", "cv2", "numpy"):
        if importlib.util.find_spec(module) is None:
            missing.append(module)
    return missing


def main() -> int:
    syntax_failures = compile_all()
    missing_tools = check_tools()
    missing_imports = check_imports()
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
    print("QUALITY GATE: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
