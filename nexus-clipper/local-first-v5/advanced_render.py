from __future__ import annotations

from pathlib import Path
from typing import Any

from caption_runtime import render_ass_safe
from captions import PRESETS
from compositor import build_final_filter, run_ffmpeg, spec_for_aspect_ratio
from multimodal_editorial import dynamic_layout_plan
from server import _hex_to_ass, _style_overrides
from virtual_camera import SubjectObservation, build_camera_path, path_to_dict
from vision_quality import inspect_render
from dataclasses import replace


def _camera(video: Path, clip: dict[str, Any], timeline: Any, req: Any) -> list[Any]:
    if not req.face_tracking:
        return []
    from server import sample_faces
    observations = sample_faces(video, float(clip["start"]), float(clip["end"]), sample_fps=3.0)
    mapped = []
    for obs in observations:
        t = timeline.source_to_output(obs.time)
        if t is not None:
            mapped.append(SubjectObservation(t, obs.x, obs.y, obs.w, obs.h, obs.confidence, obs.kind))
    points = build_camera_path(mapped)
    if req.auto_zoom or not points:
        return points
    return [replace(point, crop_w=0.92) for point in points]


def render_with_spec(video: Path, job: dict[str, Any], clip: dict[str, Any], output: Path, timeline: Any, req: Any, voiceover_path: Path | None = None) -> dict[str, Any]:
    from server import ffprobe, editorial_metadata, to_dict
    spec = spec_for_aspect_ratio(req.aspect_ratio)
    ass = output.with_suffix(".ass")
    editorial = editorial_metadata(clip["text"], emoji_enabled=req.emoji_enabled)
    style = PRESETS.get(req.subtitle_style, PRESETS["hormozi"])
    selected_animation = req.animation or style.get("animation", "pop")
    render_ass_safe(job["transcript"], timeline, ass, preset=req.subtitle_style if req.subtitle_style in PRESETS else "hormozi", font=req.font, headline=editorial.headline, emoji=editorial.emoji, canvas_w=spec.width, canvas_h=spec.height, overrides={**_style_overrides(req), "animation": selected_animation})
    media = job.get("meta") or ffprobe(video)
    video_stream = next((s for s in media.get("streams", []) if s.get("codec_type") == "video"), None)
    if not video_stream:
        raise RuntimeError("Video stream dimensions unavailable")
    source_w, source_h = int(video_stream["width"]), int(video_stream["height"])
    points = _camera(video, clip, timeline, req)
    genre = str(clip.get("genre", "general"))
    layout = dynamic_layout_plan(aspect_ratio=req.aspect_ratio, genre=genre, face_tracking=req.face_tracking, auto_zoom=req.auto_zoom)
    bias = 0.015 if layout["layout"] == "kinetic" else 0.0
    edl_graph = __import__("timeline").ffmpeg_filter_for_timeline(timeline)[0]
    filter_complex = build_final_filter(edl_graph, points, ass, source_w, source_h, spec, layout_bias=bias)
    run_ffmpeg(video, output, filter_complex, spec=spec, job_id=job.get("job_id"), normalize_audio=req.normalize_audio, voiceover_audio=voiceover_path)
    quality = inspect_render(output, expected_width=spec.width, expected_height=spec.height, min_duration=max(0.1, timeline.duration_after * 0.98), max_duration=timeline.duration_after + 0.25)
    if quality["verdict"] != "APPROVED":
        raise RuntimeError(f"Render quality gate failed: {quality}")
    return {
        "editorial": to_dict(editorial),
        "caption_preset": req.subtitle_style,
        "caption_animation": selected_animation,
        "camera": {"face_tracking": req.face_tracking, "auto_zoom": req.auto_zoom, "points": path_to_dict(points), "point_count": len(points)},
        "source_dimensions": {"width": source_w, "height": source_h},
        "output_dimensions": {"width": spec.width, "height": spec.height},
        "dynamic_layout": layout,
        "quality": quality,
        "broll": False,
        "audio_normalized": req.normalize_audio,
        "voiceover": str(voiceover_path) if voiceover_path else None,
    }
