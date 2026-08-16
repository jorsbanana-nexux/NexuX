from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from av_sync import verify_av_sync
from process_supervisor import supervised_run if False else None
from process_supervisor import run as supervised_run
from virtual_camera import CameraPoint
from vision_quality import inspect_render


@dataclass(frozen=True)
class CompositionSpec:
    width: int = 1080
    height: int = 1920
    crf: int = 20

    @property
    def aspect(self) -> float:
        return self.width / max(self.height, 1)


def spec_for_aspect_ratio(aspect_ratio: str) -> CompositionSpec:
    presets = {"9:16": (1080, 1920), "1:1": (1080, 1080), "16:9": (1920, 1080), "4:5": (1080, 1350), "2:3": (1080, 1620), "21:9": (1920, 822)}
    width, height = presets.get(aspect_ratio, presets["9:16"])
    return CompositionSpec(width=width, height=height)


def _piecewise_linear(points: list[tuple[float, float]], t_var: str = "t") -> str:
    if not points:
        return "0"
    points = sorted(points)
    if len(points) == 1:
        return f"{points[0][1]:.6f}"
    expr = f"{points[-1][1]:.6f}"
    for idx in range(len(points) - 2, -1, -1):
        t0, v0 = points[idx]
        t1, v1 = points[idx + 1]
        span = max(1e-6, t1 - t0)
        interp = f"({v0:.6f}+({v1 - v0:.6f})*(({t_var}-{t0:.6f})/{span:.6f}))"
        expr = f"if(lt({t_var},{t1:.6f}),{interp},{expr})"
    first_t, first_v = points[0]
    return f"if(lt({t_var},{first_t:.6f}),{first_v:.6f},{expr})"


def camera_crop_expressions(camera_points: list[CameraPoint], source_width: int, source_height: int, output_aspect: float = 9 / 16, layout_bias: float = 0.0) -> tuple[str, str, str, str]:
    if not camera_points:
        crop_w = min(source_width, int(source_height * output_aspect))
        crop_h = min(source_height, int(crop_w / max(output_aspect, 1e-6)))
        return str(crop_w), str(crop_h), f"(iw-{crop_w})/2", f"(ih-{crop_h})/2"
    max_crop = min(0.95, max(0.70, 0.92 + layout_bias))
    crop_w_norm = min(max(max(p.crop_w for p in camera_points), 0.65), max_crop)
    crop_w = max(2, int(source_width * crop_w_norm))
    crop_h = max(2, min(source_height, int(round(crop_w / output_aspect))))
    if crop_h > source_height:
        crop_h = source_height
        crop_w = max(2, int(round(crop_h * output_aspect)))
    xs = [(p.time, p.cx * source_width - crop_w / 2.0) for p in camera_points]
    ys = [(p.time, p.cy * source_height - crop_h / 2.0) for p in camera_points]
    return str(crop_w), str(crop_h), f"max(0,min(iw-{crop_w},{_piecewise_linear(xs)}))", f"max(0,min(ih-{crop_h},{_piecewise_linear(ys)}))"


def build_final_filter(edl_graph: str, camera_points: list[CameraPoint], ass_path: Path, source_width: int, source_height: int, spec: CompositionSpec = CompositionSpec(), *, layout_bias: float = 0.0) -> str:
    crop_w, crop_h, x, y = camera_crop_expressions(camera_points, source_width, source_height, spec.aspect, layout_bias)
    ass = str(ass_path).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")
    video = f"[vout]crop={crop_w}:{crop_h}:x='{x}':y='{y}',scale={spec.width}:{spec.height}:flags=lanczos,ass='{ass}'[vfinal]"
    return f"{edl_graph};{video}"


def run_ffmpeg(source: Path, output: Path, filter_complex: str, audio_label: str = "[aout]", spec: CompositionSpec = CompositionSpec(), *, job_id: str | None = None, normalize_audio: bool = True, voiceover_audio: Path | None = None, voiceover_mix: float = 0.85) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if job_id is None:
        match = re.match(r"([0-9a-f]{32})_", output.name)
        job_id = match.group(1) if match else None
    final_filter = filter_complex
    final_audio = audio_label
    if voiceover_audio is not None:
        final_filter += ";[aout]volume=0.35[orig];[1:a]volume={:.3f},aresample=async=1,apad[vo];[orig][vo]amix=inputs=2:duration=first:dropout_transition=2[amix]".format(max(0.0, min(2.0, voiceover_mix)))
        final_audio = "[amix]"
    if normalize_audio:
        final_filter += f";{final_audio}loudnorm=I=-16:TP=-1.5:LRA=11:linear=false[anorm]"
        final_audio = "[anorm]"
    cmd = ["ffmpeg", "-y", "-i", str(source)]
    if voiceover_audio is not None:
        cmd += ["-i", str(voiceover_audio)]
    cmd += ["-filter_complex", final_filter, "-map", "[vfinal]", "-map", final_audio, "-c:v", "libx264", "-preset", "medium", "-crf", str(spec.crf), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output)]
    result = supervised_run(cmd, key=f"render:{job_id}" if job_id else None, timeout=1800)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-3500:] or "Final composition render failed")
    if not output.exists() or output.stat().st_size == 0:
        raise RuntimeError("FFmpeg produced no final output")
    quality = inspect_render(output, expected_width=spec.width, expected_height=spec.height, min_duration=0.10)
    if quality["verdict"] != "APPROVED":
        raise RuntimeError(f"Output quality gate failed: {quality}")
    sync = verify_av_sync(output, tolerance=0.050)
    if not sync["passed"]:
        raise RuntimeError(f"Audio/video timestamp drift gate failed: {sync}")
