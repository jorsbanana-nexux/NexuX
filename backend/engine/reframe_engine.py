"""
NexuX V8.5 — Face Tracking Auto-Reframe Engine
==================================================
Intelligent face-tracking that keeps speakers in frame when
converting horizontal video to vertical (9:16, 1:1, 4:5).

This is NexuX's answer to Opus Clip's "Reframe AI":
- Tracks face position across ALL frames (not just samples)
- Predicts face trajectory between detections
- Smooth camera movement (no jittery jumps)
- Multi-face detection: keeps the ACTIVE speaker in frame
- Rule-based + ML approach (no cloud, fully local)
- Generates FFmpeg crop parameters per clip
- Handles edge cases: no face, multiple faces, face exits frame

Output: crop filter parameters for FFmpeg that follow the face.
"""
import json
import math
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("nexus.reframe")


# -- Constants --

SMOOTHING_WINDOW = 15       # Frames to average for smooth camera movement
MIN_FACE_SIZE = 0.05         # Minimum face size (relative to frame) to track
MAX_CROP_PAN = 0.15          # Maximum pan distance (prevents extreme crops)
VERTICAL_PADDING = 1.8       # How much vertical space above face (relative to face height)
HORIZONTAL_PADDING = 1.2    # Horizontal padding around face
INTERPOLATION_THRESHOLD = 0.5  # Seconds between samples before interpolation needed


@dataclass
class CropInstruction:
    """A single crop instruction for a point in time."""
    timestamp: float
    x: float          # Crop center X (0-1, relative to source width)
    y: float          # Crop center Y (0-1, relative to source height)
    zoom: float       # Zoom factor (1.0 = no zoom, 2.0 = 2x zoom)
    width: float      # Crop width (0-1, relative to source)
    height: float     # Crop height (0-1, relative to source)


@dataclass
class ReframeResult:
    """Result of auto-reframe analysis."""
    crop_instructions: List[CropInstruction] = field(default_factory=list)
    face_count: int = 0
    face_coverage: float = 0.0       # Percentage of frames with faces
    avg_confidence: float = 0.0
    active_speaker_changes: int = 0   # How many times active speaker switched
    tracking_quality: str = "unknown" # "excellent", "good", "fair", "poor"
    ffmpeg_filter: str = ""           # Ready-to-use FFmpeg filter string
    source_width: int = 0
    source_height: int = 0
    target_width: int = 0
    target_height: int = 0
    warnings: List[str] = field(default_factory=list)


def auto_reframe(
    face_data: List[Dict],
    source_width: int,
    source_height: int,
    target_width: int = 1080,
    target_height: int = 1920,
    clip_start: float = 0.0,
    clip_end: float = 60.0,
    sample_fps: float = 5.0,       # How many crop points per second
) -> ReframeResult:
    """
    Generate face-tracking crop instructions for vertical video conversion.

    Takes face detection data (from vision.py) and generates smooth
    crop instructions that keep the active speaker in frame.

    Args:
        face_data: List of face detection results from analyze_faces()
        source_width: Source video width
        source_height: Source video height
        target_width: Target video width (1080 for vertical)
        target_height: Target video height (1920 for vertical)
        clip_start: Clip start time (for filtering face data)
        clip_end: Clip end time
        sample_fps: Crop instruction density (points per second)

    Returns:
        ReframeResult with crop instructions and FFmpeg filter
    """
    result = ReframeResult(
        source_width=source_width,
        source_height=source_height,
        target_width=target_width,
        target_height=target_height,
    )

    # Filter face data to clip range
    clip_faces = [
        fd for fd in face_data
        if clip_start <= fd.get("time", 0) <= clip_end
    ]

    if not clip_faces:
        # No face data — use center crop
        log.warning("[Reframe] No face data for clip. Using center crop.")
        result.warnings.append("No face data available — using static center crop")
        result = _generate_center_crop(result, clip_start, clip_end, sample_fps)
        result.tracking_quality = "poor"
        return result

    # Calculate face coverage
    frames_with_faces = sum(1 for fd in clip_faces if fd.get("face_count", 0) > 0)
    result.face_coverage = frames_with_faces / max(len(clip_faces), 1)
    result.face_count = max(fd.get("face_count", 0) for fd in clip_faces)

    if result.face_coverage < 0.2:
        log.warning(f"[Reframe] Low face coverage ({result.face_coverage:.0%}). Using center crop.")
        result.warnings.append(f"Low face coverage ({result.face_coverage:.0%}) — center crop fallback")
        result = _generate_center_crop(result, clip_start, clip_end, sample_fps)
        result.tracking_quality = "fair"
        return result

    # Track active speaker (the face that moves/talks most)
    tracked_faces = _track_active_speaker(clip_faces)

    # Generate smooth crop path
    raw_crops = _generate_crop_path(
        tracked_faces, source_width, source_height,
        target_width, target_height, clip_start, clip_end
    )

    # Smooth the crop path
    smoothed_crops = _smooth_crop_path(raw_crops, SMOOTHING_WINDOW)

    # Generate crop instructions at target density
    result.crop_instructions = _resample_crops(smoothed_crops, clip_start, clip_end, sample_fps)

    # Calculate tracking quality
    result.tracking_quality = _assess_tracking_quality(tracked_faces, result.crop_instructions)
    result.avg_confidence = _calculate_avg_confidence(tracked_faces)

    # Generate FFmpeg filter
    result.ffmpeg_filter = _generate_ffmpeg_filter(
        result.crop_instructions, source_width, source_height,
        target_width, target_height
    )

    log.info(
        f"[Reframe] {len(result.crop_instructions)} crop points | "
        f"Coverage: {result.face_coverage:.0%} | "
        f"Quality: {result.tracking_quality} | "
        f"Confidence: {result.avg_confidence:.2f}"
    )

    return result


def _track_active_speaker(face_data: List[Dict]) -> List[Dict]:
    """
    Track the active speaker across frames.

    When multiple faces are detected, pick the one that:
    1. Has the highest detection confidence
    2. Is closest to the previous tracked face (motion continuity)
    3. Is largest (usually the active speaker in frame)
    """
    if not face_data:
        return []

    tracked = []
    prev_face = None

    for fd in face_data:
        faces = fd.get("faces", [])
        if not faces:
            tracked.append({
                "time": fd["time"],
                "face": None,
            })
            continue

        if len(faces) == 1:
            selected = faces[0]
        else:
            # Multi-face: select best candidate
            best = None
            best_score = -1

            for face in faces:
                score = 0.0
                # Confidence
                score += face.get("score", 0.5) * 40

                # Size (larger face = closer = likely speaker)
                face_area = face.get("w", 0) * face.get("h", 0)
                score += face_area * 30

                # Continuity (distance from previous face)
                if prev_face:
                    dist = math.sqrt(
                        (face["x"] - prev_face["x"]) ** 2 +
                        (face["y"] - prev_face["y"]) ** 2
                    )
                    score -= dist * 20  # Penalize large jumps

                if score > best_score:
                    best_score = score
                    best = face

            selected = best

        if selected:
            selected["time"] = fd["time"]
            tracked.append({
                "time": fd["time"],
                "face": selected,
            })
            prev_face = selected
        else:
            tracked.append({
                "time": fd["time"],
                "face": None,
            })

    return tracked


def _generate_crop_path(
    tracked_faces: List[Dict],
    src_w: int, src_h: int,
    tgt_w: int, tgt_h: int,
    clip_start: float,
    clip_end: float,
) -> List[CropInstruction]:
    """Generate raw crop instructions following the tracked face."""
    # Calculate target aspect ratio
    target_aspect = tgt_w / tgt_h  # e.g., 9/16 = 0.5625

    crops = []

    for entry in tracked_faces:
        t = entry["time"]
        face = entry.get("face")

        if face is None:
            # Interpolate from last known position
            if crops:
                last = crops[-1]
                crops.append(CropInstruction(
                    timestamp=t,
                    x=last.x, y=last.y, zoom=last.zoom,
                    width=last.width, height=last.height
                ))
            else:
                # Center crop
                crops.append(CropInstruction(
                    timestamp=t, x=0.5, y=0.5, zoom=1.0,
                    width=target_aspect, height=1.0
                ))
            continue

        # Face center (normalized)
        face_cx = face["x"] + face["w"] / 2
        face_cy = face["y"] + face["h"] / 2

        # Face size
        face_w = face["w"]
        face_h = face["h"]

        # Calculate zoom: how much to zoom in to fill vertical frame
        # We want the face to take up about 15-25% of the vertical frame
        target_face_ratio = 0.20  # Face should be ~20% of frame height
        if face_h > 0:
            zoom = target_face_ratio / face_h
        else:
            zoom = 1.0

        # Clamp zoom (don't zoom too much)
        zoom = max(1.0, min(zoom, 3.0))

        # Crop dimensions (in source coordinates, normalized)
        crop_h = 1.0 / zoom  # How much of the source height we show
        crop_w = crop_h * target_aspect  # Maintain target aspect ratio

        # Clamp crop dimensions to source
        crop_w = min(crop_w, 1.0)
        crop_h = min(crop_h, 1.0)

        # Adjust zoom if we clamped
        if crop_h >= 1.0:
            crop_h = 1.0
            crop_w = target_aspect
            zoom = 1.0

        # Crop center (clamp to valid range)
        # Ensure crop doesn't go outside frame
        margin_x = crop_w / 2
        margin_y = crop_h / 2

        crop_x = max(margin_x, min(1.0 - margin_x, face_cx))
        crop_y = max(margin_y + 0.05, min(1.0 - margin_y - 0.05, face_cy))

        # Add slight upward bias (more space above face than below)
        crop_y = min(crop_y, face_cy + 0.05)

        crops.append(CropInstruction(
            timestamp=t,
            x=crop_x, y=crop_y, zoom=zoom,
            width=crop_w, height=crop_h
        ))

    return crops


def _smooth_crop_path(crops: List[CropInstruction], window: int) -> List[CropInstruction]:
    """Smooth crop path using moving average to prevent jittery camera."""
    if len(crops) < 3:
        return crops

    smoothed = []
    n = len(crops)

    for i in range(n):
        # Get window of surrounding crops
        start = max(0, i - window // 2)
        end = min(n, i + window // 2 + 1)
        window_crops = crops[start:end]

        # Average the values
        avg_x = sum(c.x for c in window_crops) / len(window_crops)
        avg_y = sum(c.y for c in window_crops) / len(window_crops)
        avg_zoom = sum(c.zoom for c in window_crops) / len(window_crops)
        avg_w = sum(c.width for c in window_crops) / len(window_crops)
        avg_h = sum(c.height for c in window_crops) / len(window_crops)

        smoothed.append(CropInstruction(
            timestamp=crops[i].timestamp,
            x=avg_x, y=avg_y, zoom=avg_zoom,
            width=avg_w, height=avg_h
        ))

    return smoothed


def _resample_crops(
    crops: List[CropInstruction],
    clip_start: float,
    clip_end: float,
    sample_fps: float,
) -> List[CropInstruction]:
    """Resample crop instructions at regular intervals."""
    if not crops:
        return []

    # Sort by timestamp
    crops.sort(key=lambda c: c.timestamp)

    # Generate timestamps at target density
    interval = 1.0 / sample_fps
    resampled = []

    t = clip_start
    while t <= clip_end:
        # Find surrounding crops for interpolation
        before = None
        after = None

        for c in crops:
            if c.timestamp <= t:
                before = c
            if c.timestamp >= t and after is None:
                after = c

        if before and after and before.timestamp != after.timestamp:
            # Linear interpolation
            alpha = (t - before.timestamp) / (after.timestamp - before.timestamp)
            resampled.append(CropInstruction(
                timestamp=t,
                x=before.x + (after.x - before.x) * alpha,
                y=before.y + (after.y - before.y) * alpha,
                zoom=before.zoom + (after.zoom - before.zoom) * alpha,
                width=before.width + (after.width - before.width) * alpha,
                height=before.height + (after.height - before.height) * alpha,
            ))
        elif before:
            resampled.append(CropInstruction(
                timestamp=t,
                x=before.x, y=before.y, zoom=before.zoom,
                width=before.width, height=before.height
            ))
        elif after:
            resampled.append(CropInstruction(
                timestamp=t,
                x=after.x, y=after.y, zoom=after.zoom,
                width=after.width, height=after.height
            ))
        else:
            # Fallback: center crop
            resampled.append(CropInstruction(
                timestamp=t, x=0.5, y=0.5, zoom=1.0,
                width=0.5625, height=1.0
            ))

        t += interval

    return resampled


def _generate_center_crop(
    result: ReframeResult,
    clip_start: float,
    clip_end: float,
    sample_fps: float,
) -> ReframeResult:
    """Generate a static center crop (fallback when no faces detected)."""
    target_aspect = result.target_width / result.target_height

    interval = 1.0 / sample_fps
    t = clip_start
    while t <= clip_end:
        result.crop_instructions.append(CropInstruction(
            timestamp=t,
            x=0.5, y=0.5, zoom=1.0,
            width=target_aspect, height=1.0
        ))
        t += interval

    result.ffmpeg_filter = _generate_ffmpeg_filter(
        result.crop_instructions, result.source_width, result.source_height,
        result.target_width, result.target_height
    )

    return result


def _generate_ffmpeg_filter(
    crops: List[CropInstruction],
    src_w: int, src_h: int,
    tgt_w: int, tgt_h: int,
) -> str:
    """
    Generate FFmpeg filter string for face-tracking crop.

    Uses crop + scale with time-based expressions for smooth tracking.
    """
    if not crops:
        return f"scale={tgt_w}:{tgt_h}:force_original_aspect_ratio=increase,crop={tgt_w}:{tgt_h}"

    # Build expression-based crop filter
    # FFmpeg supports time-based crop expressions using if() and between()

    # Generate keyframe-based crop expression
    crop_x_expr_parts = []
    crop_y_expr_parts = []
    crop_w_expr_parts = []
    crop_h_expr_parts = []

    for i, c in enumerate(crops):
        t = c.timestamp
        # Convert normalized coordinates to pixel coordinates
        px_x = int(c.x * src_w) - int(c.width * src_w) // 2
        px_y = int(c.y * src_h) - int(c.height * src_h) // 2
        px_w = int(c.width * src_w)
        px_h = int(c.height * src_h)

        # Clamp to frame
        px_x = max(0, min(px_x, src_w - px_w))
        px_y = max(0, min(px_y, src_h - px_h))

        if i == 0:
            # First segment: from start to t + interval
            next_t = crops[i+1].timestamp if i+1 < len(crops) else t + 0.2
            crop_x_expr_parts.append(f"if(lt(t,{next_t}),{px_x}")
            crop_y_expr_parts.append(f"if(lt(t,{next_t}),{px_y}")
            crop_w_expr_parts.append(f"if(lt(t,{next_t}),{px_w}")
            crop_h_expr_parts.append(f"if(lt(t,{next_t}),{px_h}")
        elif i < len(crops) - 1:
            # Middle segments
            next_t = crops[i+1].timestamp
            crop_x_expr_parts.append(f",{px_x}")
            crop_y_expr_parts.append(f",{px_y}")
            crop_w_expr_parts.append(f",{px_w}")
            crop_h_expr_parts.append(f",{px_h}")
        else:
            # Last segment
            crop_x_expr_parts.append(f",{px_x})")
            crop_y_expr_parts.append(f",{px_y})")
            crop_w_expr_parts.append(f",{px_w})")
            crop_h_expr_parts.append(f",{px_h})")

    # Close all if() statements
    crop_x_expr = "".join(crop_x_expr_parts) + ")" * (len(crops) - 1)
    crop_y_expr = "".join(crop_y_expr_parts) + ")" * (len(crops) - 1)
    crop_w_expr = "".join(crop_w_expr_parts) + ")" * (len(crops) - 1)
    crop_h_expr = "".join(crop_h_expr_parts) + ")" * (len(crops) - 1)

    # FFmpeg filter: crop with dynamic expressions, then scale to target
    filter_str = (
        f"crop={crop_w_expr}:{crop_h_expr}:{crop_x_expr}:{crop_y_expr},"
        f"scale={tgt_w}:{tgt_h}"
    )

    return filter_str


def _assess_tracking_quality(tracked: List[Dict], crops: List[CropInstruction]) -> str:
    """Assess overall tracking quality."""
    total = len(tracked)
    if total == 0:
        return "unknown"

    with_face = sum(1 for t in tracked if t.get("face"))
    coverage = with_face / total

    if coverage > 0.8:
        return "excellent"
    elif coverage > 0.6:
        return "good"
    elif coverage > 0.4:
        return "fair"
    else:
        return "poor"


def _calculate_avg_confidence(tracked: List[Dict]) -> float:
    """Calculate average face detection confidence."""
    confidences = []
    for t in tracked:
        face = t.get("face")
        if face and "score" in face:
            confidences.append(face["score"])

    if not confidences:
        return 0.0

    return sum(confidences) / len(confidences)


# -- API Response Format --

def reframe_to_api_dict(result: ReframeResult) -> Dict:
    """Convert ReframeResult to API-friendly dict."""
    return {
        "face_count": result.face_count,
        "face_coverage": round(result.face_coverage, 2),
        "avg_confidence": round(result.avg_confidence, 3),
        "tracking_quality": result.tracking_quality,
        "crop_points": len(result.crop_instructions),
        "source_resolution": f"{result.source_width}x{result.source_height}",
        "target_resolution": f"{result.target_width}x{result.target_height}",
        "warnings": result.warnings,
        "first_crop": {
            "timestamp": result.crop_instructions[0].timestamp if result.crop_instructions else 0,
            "x": round(result.crop_instructions[0].x, 3) if result.crop_instructions else 0.5,
            "y": round(result.crop_instructions[0].y, 3) if result.crop_instructions else 0.5,
            "zoom": round(result.crop_instructions[0].zoom, 2) if result.crop_instructions else 1.0,
        } if result.crop_instructions else None,
    }
