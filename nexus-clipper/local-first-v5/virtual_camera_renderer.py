from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Iterable


@dataclass(frozen=True)
class CameraKeyframe:
    time: float
    center_x: float
    center_y: float
    crop_w: float
    crop_h: float


def _piecewise_expression(keyframes: list[tuple[float, float]], t_expr: str = "t") -> str:
    if not keyframes:
        return "0"
    ordered = sorted(keyframes)
    if len(ordered) == 1:
        return f"{ordered[0][1]:.6f}"
    expr = f"{ordered[-1][1]:.6f}"
    for i in range(len(ordered) - 2, -1, -1):
        t0, v0 = ordered[i]
        t1, v1 = ordered[i + 1]
        if t1 <= t0:
            continue
        interp = f"({v0:.6f}+({v1 - v0:.6f})*({t_expr}-{t0:.6f})/{t1 - t0:.6f})"
        expr = f"if({t_expr}<{t1:.6f},{interp},{expr})"
    return f"if({t_expr}<{ordered[0][0]:.6f},{ordered[0][1]:.6f},{expr})"


def build_crop_filter(camera_path: Iterable[CameraKeyframe], out_w: int = 1080, out_h: int = 1920) -> str:
    points = list(camera_path)
    if not points:
        # Generic center crop. Input is scaled to cover the 9:16 target first.
        return f"scale={out_w}:{out_h}:force_original_aspect_ratio=increase,crop={out_w}:{out_h}"

    cx = _piecewise_expression([(p.time, p.center_x) for p in points])
    cy = _piecewise_expression([(p.time, p.center_y) for p in points])
    cw = _piecewise_expression([(p.time, max(0.08, min(0.95, p.crop_w))) for p in points])
    ch = _piecewise_expression([(p.time, max(0.14, min(1.0, p.crop_h))) for p in points])

    crop_w = f"iw*({cw})"
    crop_h = f"ih*({ch})"
    x = f"max(0,min(iw-({crop_w}),iw*({cx})-({crop_w})/2))"
    y = f"max(0,min(ih-({crop_h}),ih*({cy})-({crop_h})/2))"
    return f"crop=w={crop_w}:h={crop_h}:x={x}:y={y},scale={out_w}:{out_h}:force_original_aspect_ratio=decrease,pad={out_w}:{out_h}:(ow-iw)/2:(oh-ih)/2"


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
    if not source.exists():
        raise FileNotFoundError(source)
    if width <= 0 or height <= 0:
        raise ValueError("Output dimensions must be positive")

    vf = build_crop_filter(camera_path, width, height)
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
