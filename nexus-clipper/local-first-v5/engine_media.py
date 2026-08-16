from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def ffprobe(path: Path) -> dict[str, Any]:
    """Inspect a media artifact without coupling to the compatibility server."""
    command = [
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-1200:] or "FFprobe failed")
    return json.loads(result.stdout)
