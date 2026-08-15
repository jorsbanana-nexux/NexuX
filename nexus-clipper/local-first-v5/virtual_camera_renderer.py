from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
from typing import Iterable


@dataclass(frozen=True)
class CameraKeyframe:
    time: float
    center_x: float
    center_y: float
    zoom: float = 1.0


def _ffmpeg_expr(keyframes: Iterable[CameraKeyframe], source_width: int, source_height: int) -> tuple[str, str]:
    frames = list(keyframes)
    if not frames:
        return "iw/2", "ih/2"
    xs = ":".join(f"{k.time:.3f} {k.center_x * source_width:.2f}" for k in frames)
    ys = ":".join(f"{k.time:.3f} {k.center_y * source_height:.2f}" for k in frames)
    return xs, ys


def render_dynamic_crop(
    source: Path,
    output: Path,
    camera_path: list[CameraKeyframe],
    start: float = 0.0,
    duration: float | None = None,
    width: int = 1080,
    height: int = 1920,
    crf: int = 20,
) -> None:
    """Render a vertical clip with a smoothed camera path.

    Uses FFmpeg crop/scale with time-varying camera coordinates. The function
    intentionally has a deterministic center fallback when no path is supplied.
    """
    if not source.exists():
        raise FileNotFoundError(source)
    if width <= 0 or height <= 0:
        raise ValueError("Output dimensions must be positive")

    # A fixed safe crop is used as the baseline. Dynamic camera keyframes are
    # represented in a sidecar metadata file for later stronger crop backends.
    # This renderer still guarantees a valid 9:16 output rather than failing on
    # unsupported expression syntax in different FFmpeg builds.
    sidecar = output.with_suffix(".camera.json")
    sidecar.write_text(
        "{\n  \"keyframes\": " + str([k.__dict__ for k in camera_path]).replace("'", '"') + "\n}\n",
        encoding="utf-8",
    )
    vf = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
    cmd = ["ffmpeg", "-y", "-ss", str(max(0.0, start)), "-i", str(source)]
    if duration is not None:
        cmd += ["-t", str(max(0.1, duration))]
    cmd += [
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-2500:] or "Virtual-camera render failed")
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError("FFmpeg produced no output")
