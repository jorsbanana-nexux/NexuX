"""
NexuX V8.5 — Personalization Re-Render Pipeline
====================================================
Takes editor state from ClipEditorStudio and re-renders a clip
with new subtitle style, effects, zoom, color grade, speed ramp,
audio mixing, layout/aspect change, branding, and trim adjustments.

Flow:
1. Load original job data (source video, transcript, clip metadata)
2. Build new style_config from editor state
3. Apply trim adjustments (if start/end changed)
4. Re-render with new parameters via render_clip / render_clip_pro
5. Apply audio post-processing (BGM mix, normalize, bass boost, SFX)
6. Apply watermark / branding overlay
7. Return new clip path

This is the backend that makes the "Apply & Re-render" button work.
"""
import json
import os
import time
import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass

log = logging.getLogger("nexus.rerender")

# Import from engine
try:
    from .constants import (
        OUTPUT_DIR, ASPECT_RATIOS, VIDEO_CODECS, AUDIO_CODECS, COLOR_GRADES,
        STYLE_PRESETS,
    )
    from .render import render_clip, concatenate_clips, mix_bgm, normalize_audio
    from .render_pro import render_clip_pro
    from .caption_engine_v2 import build_advanced_ass
    from .styles import resolve_style
    from .utils import retry, run_ffmpeg, rel_path
except ImportError:
    # Standalone import for testing
    pass


# ── Editor State → Render Config Converter ──────────

def editor_state_to_render_config(editor_state: Dict) -> Dict:
    """
    Convert ClipEditorStudio's EditorState (from frontend JSON)
    into a render configuration dict that the render pipeline understands.

    Maps:
    - captionStyle → style_config.subtitle_style
    - animation → style_config.animation
    - fontSize/fontFamily → style_config.font_*
    - primaryColor/highlightColor → style_config.colors
    - zoomStyle → creative_config.zoom_style
    - colorGrade → color_grade
    - speedRamp → creative_config.speed_ramp_type
    - aspectRatio → style_config.aspect_ratio
    - audio settings → post-process config
    - branding → overlay config
    - trim → clip start/end adjustment
    """
    return {
        # Subtitle/caption config
        "style_config": {
            "subtitle_style": editor_state.get("subtitle_style", "hormozi"),
            "animation": editor_state.get("animation", "word-by-word"),
            "font_size": editor_state.get("font_size", "large"),
            "font_family": editor_state.get("font_family", "display"),
            "position": editor_state.get("position", "center"),
            "glow_style": editor_state.get("glow_style", "intense"),
            "primary_color": editor_state.get("primary_color", "#FFFFFF"),
            "highlight_color": editor_state.get("highlight_color", "#FFD700"),
            "show_emojis": editor_state.get("show_emojis", True),
            "aspect_ratio": editor_state.get("aspect_ratio", "9:16"),
        },

        # Visual effects
        "color_grade": editor_state.get("color_grade", "none"),
        "zoom_level": editor_state.get("zoom_level", 1.0),

        # Creative config (for render_pro)
        "creative_config": {
            "zoom_style": editor_state.get("zoom_style", "subtle"),
            "speed_ramp": editor_state.get("speed_ramp", False),
            "speed_ramp_type": editor_state.get("speed_ramp_type", "none"),
            "transition": "hard_cut",
        },

        # Auto-zoom toggle (enable if zoom_style is not "none")
        "auto_zoom": editor_state.get("zoom_style", "subtle") != "none",

        # Audio post-processing
        "audio_config": {
            "bgm_volume": editor_state.get("bgm_volume", 30),
            "voice_volume": editor_state.get("voice_volume", 100),
            "normalize_audio": editor_state.get("normalize_audio", True),
            "bass_boost": editor_state.get("bass_boost", False),
            "sfx_enabled": editor_state.get("sfx_enabled", True),
        },

        # Layout
        "aspect_ratio": editor_state.get("aspect_ratio", "9:16"),
        "auto_reframe": editor_state.get("auto_reframe", True),
        "face_tracking": editor_state.get("face_tracking", True),

        # Branding
        "branding": {
            "watermark_text": editor_state.get("watermark_text", ""),
            "watermark_position": editor_state.get("watermark_position", "bottom-right"),
            "show_watermark": editor_state.get("show_watermark", False),
            "intro_enabled": editor_state.get("intro_enabled", False),
            "outro_enabled": editor_state.get("outro_enabled", False),
        },

        # Trim
        "trim_start": editor_state.get("trim_start", 0),
        "trim_end": editor_state.get("trim_end", 45),
    }


# ── Trim Adjustment ─────────────────────────────────

def apply_trim_adjustment(
    clip: Dict,
    trim_start: float,
    trim_end: float,
) -> Dict:
    """
    Apply trim adjustments to a clip dict.

    If the user trimmed the clip in the editor, update the start/end times.
    """
    original_start = clip.get("start", 0)
    original_end = clip.get("end", 45)
    original_dur = original_end - original_start

    # trim_start and trim_end are relative to the clip
    # e.g., if clip is 10-55 and trim_start=2, trim_end=40
    # then new clip is 12-50
    new_start = original_start + trim_start
    new_end = original_start + trim_end

    # Ensure valid range
    new_end = min(new_end, original_end)
    new_start = max(new_start, original_start)

    trimmed = clip.copy()
    trimmed["start"] = round(new_start, 2)
    trimmed["end"] = round(new_end, 2)

    log.info(f"[ReRender] Trim: {original_start}-{original_end} → {new_start}-{new_end} "
             f"({new_end - new_start:.1f}s)")

    return trimmed


# ── Style Config Builder ─────────────────────────────

def build_style_config(
    editor_state: Dict,
    aspect_ratio: str = "9:16",
) -> Dict:
    """
    Build a complete style_config dict from editor state.

    This is what render_clip() expects for subtitle styling.
    """
    es = editor_state
    base_style = es.get("subtitle_style", "hormozi")
    animation = es.get("animation", "word-by-word")

    # Map font sizes to pixel heights
    font_size_map = {
        "compact": 42,
        "normal": 52,
        "large": 64,
        "huge": 78,
    }

    # Map font families to ASS font names
    font_family_map = {
        "sans": "Arial",
        "display": "Impact",
        "mono": "Courier New",
        "serif": "Georgia",
    }

    # Map glow styles to ASS border/shadow
    glow_map = {
        "subtle": {"border": 2, "shadow": 1},
        "intense": {"border": 4, "shadow": 3},
        "outline-clean": {"border": 3, "shadow": 0},
    }

    glow = glow_map.get(es.get("glow_style", "intense"), {"border": 4, "shadow": 3})

    # Build position in ASS coordinates (from bottom)
    position = es.get("position", "center")
    pos_map = {
        "top": {"y_offset": 0.75},      # 75% from bottom = top
        "center": {"y_offset": 0.45},    # center
        "bottom": {"y_offset": 0.12},    # near bottom
    }
    pos = pos_map.get(position, {"y_offset": 0.45})

    return {
        "subtitle_style": base_style,
        "animation": animation,
        "font": font_family_map.get(es.get("font_family", "display"), "Impact"),
        "font_size": font_size_map.get(es.get("font_size", "large"), 64),
        "font_family": es.get("font_family", "display"),
        "primary_color": es.get("primary_color", "#FFFFFF"),
        "highlight_color": es.get("highlight_color", "#FFD700"),
        "stroke_color": "#000000",
        "stroke_width": glow["border"],
        "shadow": glow["shadow"],
        "position": position,
        "y_offset": pos["y_offset"],
        "show_emojis": es.get("show_emojis", True),
        "aspect_ratio": aspect_ratio,
        # Animation-specific
        "word_by_word": animation == "word-by-word",
        "line_by_line": animation == "line-by-line",
        "bounce_zoom": animation == "bounce-zoom",
        "kinetic_slide": animation == "kinetic-slide",
        "pulse_glow": animation == "pulse-glow",
        "fade_drift": animation == "fade-drift",
        "typewriter_glitch": animation == "typewriter-glitch",
        "flip_rotate": animation == "flip-rotate",
    }


# ── Zoom Filter Builder ─────────────────────────────

def build_zoom_filter(
    zoom_style: str,
    zoom_level: float,
    clip_dur: float,
    w: int,
    h: int,
) -> str:
    """Build FFmpeg zoompan filter from editor settings."""
    if zoom_style == "none" or zoom_level <= 1.0:
        return ""

    if zoom_style == "subtle":
        # Gentle Ken Burns: 1.0x → 1.1x
        max_zoom = 1.0 + (zoom_level - 1.0) * 0.3
        return (
            f"zoompan=z='min(zoom+0.0008,{max_zoom:.2f})':d=1:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"s={w}x{h}:fps=30"
        )

    elif zoom_style == "dramatic":
        # More aggressive zoom: 1.0x → zoom_level
        max_zoom = zoom_level
        return (
            f"zoompan=z='min(zoom+0.002,{max_zoom:.2f})':d=1:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"s={w}x{h}:fps=30"
        )

    elif zoom_style == "punch":
        # Punch zoom: quick zoom in at start, hold, then zoom out at end
        punch_dur = min(0.5, clip_dur * 0.1)
        return (
            f"zoompan=z='if(lt(on,1),1,if(lt(on,{punch_dur:.0f}),"
            f"1+0.002*on,{zoom_level:.2f}))':d=1:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"s={w}x{h}:fps=30"
        )

    elif zoom_style == "breathing":
        # Breathing zoom: slow oscillation
        return (
            f"zoompan=z='1+0.02*sin(on*0.05)':d=1:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"s={w}x{h}:fps=30"
        )

    return ""


# ── Watermark Overlay ───────────────────────────────

def apply_watermark(
    video_path: Path,
    watermark_text: str,
    position: str = "bottom-right",
) -> Path:
    """Overlay a text watermark on the video."""
    if not watermark_text:
        return video_path

    pos_map = {
        "top-left":      "x=10:y=10",
        "top-right":     "x=w-tw-10:y=10",
        "bottom-left":   "x=10:y=h-th-10",
        "bottom-right":  "x=w-tw-10:y=h-th-10",
    }
    pos_str = pos_map.get(position, pos_map["bottom-right"])

    output = video_path.with_suffix(f".watermarked{video_path.suffix}")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", (
            f"drawtext=text='{watermark_text}':"
            f"{pos_str}:"
            f"fontsize=24:fontcolor=white@0.5:"
            f"shadowcolor=black:shadowx=1:shadowy=1"
        ),
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(output),
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if output.exists():
            log.info(f"[ReRender] Watermark applied: '{watermark_text}' at {position}")
            return output
    except Exception as e:
        log.warning(f"[ReRender] Watermark failed: {e}")

    return video_path


# ── Audio Post-Processing ────────────────────────────

def apply_audio_processing(
    video_path: Path,
    audio_config: Dict,
) -> Path:
    """
    Apply audio post-processing based on editor settings:
    - BGM volume mixing
    - Voice volume adjustment
    - Loudness normalization
    - Bass boost
    """
    if not audio_config:
        return video_path

    filters = []
    needs_audio_filter = False

    # Voice volume
    voice_vol = audio_config.get("voice_volume", 100)
    if voice_vol != 100:
        vol_gain = voice_vol / 100.0
        filters.append(f"volume={vol_gain:.2f}")
        needs_audio_filter = True

    # Bass boost
    if audio_config.get("bass_boost", False):
        filters.append("bass=g=6:f=80:w=0.8")
        needs_audio_filter = True

    # Normalize
    if audio_config.get("normalize_audio", True):
        filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")
        needs_audio_filter = True

    if not needs_audio_filter:
        return video_path

    output = video_path.with_suffix(f".audio{video_path.suffix}")

    af = ",".join(filters)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-af", af,
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(output),
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if output.exists():
            log.info(f"[ReRender] Audio processed: {af}")
            return output
    except Exception as e:
        log.warning(f"[ReRender] Audio processing failed: {e}")

    return video_path



# ── Overlay Filter Builder ───────────────────────────

def build_overlay_filters(
    overlays: List[Dict],
    video_width: int,
    video_height: int,
    clip_start: float,
) -> str:
    """
    Build FFmpeg drawtext filter chain string for draggable text overlay elements.

    Args:
        overlays: List of overlay element dicts (position, font, color, timing, animation, etc.)
        video_width: Video canvas width in pixels
        video_height: Video canvas height in pixels
        clip_start: Start timestamp of the clip in source video seconds

    Returns:
        Comma-separated FFmpeg filter string for drawtext overlays, or "" if none valid.
    """
    if not overlays:
        return ""

    # Filter out invisible or locked elements
    valid_elements = []
    for el in overlays:
        # Skip invisible
        visible = el.get("visible", True)
        if visible in (False, "false", "False", 0):
            continue

        # Skip locked
        locked = el.get("locked", False)
        if locked in (True, "true", "True", 1):
            continue

        # Skip non-text if type specified
        el_type = el.get("type", "text")
        if el_type and el_type not in ("text", "title", "caption") and not el.get("content"):
            continue

        valid_elements.append(el)

    if not valid_elements:
        return ""

    # Sort by zIndex / z_index ascending (lower drawn first = behind higher)
    sorted_elements = sorted(
        valid_elements,
        key=lambda e: int(e.get("zIndex", e.get("z_index", 0)))
    )

    drawtext_filters = []

    for el in sorted_elements:
        content = str(el.get("content", ""))
        if not content:
            continue

        # Handle text content with newlines (replace \n with actual newlines in drawtext)
        content = content.replace("\\n", " ")

        # Escape colons, single quotes, backslashes, percents for drawtext
        safe_content = (
            content.replace('\\', '\\\\')
                   .replace(':', '\\:')
                   .replace("'", '\\')
                   .replace('%', '\\%')
        )

        # Timing conversion: convert absolute start/end to relative within clip
        el_start = float(el.get("start", 0))
        el_end = float(el.get("end", 999999))

        if el_start >= clip_start:
            rel_start = el_start - clip_start
            rel_end = el_end - clip_start
        elif el_end > clip_start:
            rel_start = max(0.0, el_start - clip_start)
            rel_end = el_end - clip_start
        else:
            # Check if timing was already relative within the clip
            if el_start >= 0 and el_end > el_start:
                rel_start = el_start
                rel_end = el_end
            else:
                # Outside clip time range
                continue

        if rel_end <= rel_start or rel_end <= 0:
            continue

        dur = rel_end - rel_start

        # Percentage positions (x, y are 0-100) -> pixel expressions
        x_val = float(el.get("x", 50.0))
        y_val = float(el.get("y", 50.0))

        x_expr = f"w*{x_val}/100-tw/2"
        y_expr = f"h*{y_val}/100-th/2"

        # Entry/exit animations (fade, slide-up, pop, bounce)
        anim_in = str(el.get("animationIn", el.get("animation_in", "fade"))).lower()
        anim_out = str(el.get("animationOut", el.get("animation_out", "fade"))).lower()

        if anim_in == "slide-up":
            y_expr = f"h*{y_val}/100-th/2+if(lt(t-{rel_start:.2f},0.3),(1-(t-{rel_start:.2f})/0.3)*60,0)"
        elif anim_in == "bounce":
            y_expr = f"h*{y_val}/100-th/2+if(lt(t-{rel_start:.2f},0.3),sin((t-{rel_start:.2f})/0.3*3.14159)*-20,0)"

        fade_in_dur = 0.15 if anim_in == "pop" else (min(0.5, max(0.1, dur * 0.2)) if anim_in == "fade" else 0.0)
        fade_out_dur = min(0.5, max(0.1, dur * 0.2)) if anim_out == "fade" else 0.0

        alpha_expr = ""
        if fade_in_dur > 0 and fade_out_dur > 0:
            alpha_expr = (
                f":alpha='if(lt(t,{rel_start + fade_in_dur:.2f}),"
                f"(t-{rel_start:.2f})/{fade_in_dur:.2f},"
                f"if(gt(t,{rel_end - fade_out_dur:.2f}),"
                f"({rel_end:.2f}-t)/{fade_out_dur:.2f},1))'"
            )
        elif fade_in_dur > 0:
            alpha_expr = f":alpha='if(lt(t,{rel_start + fade_in_dur:.2f}),(t-{rel_start:.2f})/{fade_in_dur:.2f},1)'"
        elif fade_out_dur > 0:
            alpha_expr = f":alpha='if(gt(t,{rel_end - fade_out_dur:.2f}),({rel_end:.2f}-t)/{fade_out_dur:.2f},1)'"

        # Font size relative to video canvas
        raw_fs = float(el.get("fontSize", el.get("font_size", 24)))
        font_size = max(10, int(raw_fs * (video_width / 400.0)))

        # Colors
        fontcolor = str(el.get("color", "#FFFFFF"))
        fc = fontcolor.replace("#", "0x") if fontcolor.startswith("#") else fontcolor
        if not fc:
            fc = "0xFFFFFF"

        # Background color box
        bg = str(el.get("bgColor", el.get("bg_color", el.get("bg", "transparent"))))
        box_str = ""
        if bg and bg.lower() not in ("transparent", "none", ""):
            bgc = bg.replace("#", "0x") if bg.startswith("#") else bg
            box_str = f":box=1:boxcolor={bgc}@0.85:boxborderw=8"

        drawtext = (
            f"drawtext=text='{safe_content}':"
            f"x='{x_expr}':y='{y_expr}':"
            f"fontsize={font_size}:"
            f"fontcolor={fc}"
            f":borderw=2:bordercolor=0x000000"
            f"{box_str}"
            f":enable='between(t,{rel_start:.2f},{rel_end:.2f})'"
            f"{alpha_expr}"
        )
        drawtext_filters.append(drawtext)

    return ",".join(drawtext_filters)


# ── Overlay Burn-in Application ──────────────────────

def apply_overlays_to_video(
    input_path: Path,
    output_path: Path,
    overlays: List[Dict],
    video_w: int,
    video_h: int,
    clip_start: float,
    clip_end: float,
) -> Path:
    """
    Build overlay filter chain and burn in draggable overlay elements into video using FFmpeg.

    Args:
        input_path: Path to source/rendered video
        output_path: Path to write output video with overlays
        overlays: List of overlay dicts
        video_w: Video width
        video_h: Video height
        clip_start: Clip start time in source video
        clip_end: Clip end time in source video

    Returns:
        Path to output video with overlays burned in (or input_path if no overlays applied)
    """
    if not input_path or not input_path.exists():
        log.warning(f"[Overlay] Input path does not exist: {input_path}")
        return input_path

    if not overlays:
        log.info("[Overlay] No overlays provided, skipping overlay burn-in")
        return input_path

    filter_chain = build_overlay_filters(
        overlays=overlays,
        video_width=video_w,
        video_height=video_h,
        clip_start=clip_start,
    )

    if not filter_chain:
        log.info("[Overlay] No active or visible overlay filters built, skipping")
        return input_path

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vf", filter_chain,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(output_path),
    ]

    try:
        log.info(f"[Overlay] Running FFmpeg overlay burn-in on {input_path.name}")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if r.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
            log.info(f"[Overlay] Successfully burned in overlays -> {output_path.name}")
            return output_path
        else:
            err = r.stderr[-500:] if r.stderr else "Unknown error"
            log.warning(f"[Overlay] FFmpeg failed (returncode {r.returncode}): {err}")
    except Exception as e:
        log.error(f"[Overlay] Failed to apply overlays: {e}", exc_info=True)

    return input_path



# ── Main Re-Render Function ──────────────────────────

def rerender_clip_with_personalization(
    job_data: Dict,
    clip_index: int,
    editor_state: Dict,
    source_video_path: Optional[Path] = None,
    transcript: Optional[Dict] = None,
    face_data: Optional[List[Dict]] = None,
    overlays: Optional[List[Dict]] = None,
    use_pro: bool = True,
) -> Dict:
    """
    Re-render a clip with personalization settings from ClipEditorStudio.

    This is the main entry point called by the /api/rerender endpoint.

    Args:
        job_data: Job dict from database (contains clips, analysis_bundle, etc.)
        clip_index: Which clip to re-render (0-indexed)
        editor_state: Editor settings from frontend (JSON body)
        source_video_path: Path to original source video
        transcript: Full transcript dict
        face_data: Face tracking data for auto-reframe
        use_pro: Use render_clip_pro (multi-pass) vs render_clip (single-pass)

    Returns:
        Dict with:
        - status: "success" | "error"
        - output_path: Path to re-rendered clip
        - clip_index: Clip index
        - render_time_seconds: How long it took
        - changes_applied: Summary of what was changed
    """
    start_time = time.time()

    clips = json.loads(job_data.get("clips", "[]"))
    if clip_index < 0 or clip_index >= len(clips):
        return {
            "status": "error",
            "error": f"Invalid clip index: {clip_index}",
        }

    original_clip = clips[clip_index]
    changes = []

    try:
        # 1. Convert editor state to render config
        render_config = editor_state_to_render_config(editor_state)

        # 2. Apply trim adjustments
        trim_start = editor_state.get("trim_start", 0)
        trim_end = editor_state.get("trim_end", original_clip["end"] - original_clip["start"])
        original_dur = original_clip["end"] - original_clip["start"]

        if trim_start != 0 or abs(trim_end - original_dur) > 0.1:
            adjusted_clip = apply_trim_adjustment(original_clip, trim_start, trim_end)
            changes.append(f"Trim: {original_dur:.1f}s → {adjusted_clip['end'] - adjusted_clip['start']:.1f}s")
        else:
            adjusted_clip = original_clip.copy()

        # 3. Determine source video
        if not source_video_path:
            # Try to find from job data
            source_video = job_data.get("_source_video") or job_data.get("source_video_path")
            if source_video:
                source_video_path = Path(source_video)
            else:
                return {
                    "status": "error",
                    "error": "Source video path not found in job data",
                }

        if not source_video_path.exists():
            return {
                "status": "error",
                "error": f"Source video not found: {source_video_path}",
            }

        # 4. Get transcript
        if not transcript:
            analysis_bundle = json.loads(job_data.get("analysis_bundle", "null") or "null")
            if analysis_bundle:
                transcript = analysis_bundle
            else:
                transcript = {"segments": []}

        # 5. Build style config from editor state
        aspect_ratio = editor_state.get("aspect_ratio", "9:16")
        style_config = build_style_config(editor_state, aspect_ratio)

        # 6. Get color grade
        color_grade = editor_state.get("color_grade", "none")
        if color_grade != "none":
            changes.append(f"Color grade: {color_grade}")

        # 7. Get creative config
        creative_config = render_config.get("creative_config", {})

        zoom_style = editor_state.get("zoom_style", "subtle")
        if zoom_style != "none":
            changes.append(f"Zoom: {zoom_style}")

        speed_ramp = editor_state.get("speed_ramp", False)
        if speed_ramp:
            changes.append(f"Speed ramp: {editor_state.get('speed_ramp_type', 'none')}")

        # 8. Detect what changed from original
        original_style = json.loads(job_data.get("request_data", "{}")).get("subtitle_style", "hormozi")
        if style_config["subtitle_style"] != original_style:
            changes.append(f"Caption style: {original_style} → {style_config['subtitle_style']}")

        original_animation = json.loads(job_data.get("request_data", "{}")).get("animation", "word-by-word")
        if style_config["animation"] != original_animation:
            changes.append(f"Animation: {original_animation} → {style_config['animation']}")

        if editor_state.get("primary_color", "#FFFFFF") != "#FFFFFF":
            changes.append(f"Primary color: {editor_state['primary_color']}")

        if editor_state.get("highlight_color", "#FFD700") != "#FFD700":
            changes.append(f"Highlight color: {editor_state['highlight_color']}")

        if aspect_ratio != "9:16":
            changes.append(f"Aspect ratio: 9:16 → {aspect_ratio}")

        # 9. Get aspect dimensions
        from .constants import ASPECT_RATIOS as AR
        w, h = AR.get(aspect_ratio, (1080, 1920))

        # 10. Build custom zoom filter if zoom_level > 1.0
        zoom_level = editor_state.get("zoom_level", 1.0)
        custom_zoom = build_zoom_filter(zoom_style, zoom_level,
                                        adjusted_clip["end"] - adjusted_clip["start"], w, h)

        # 11. Re-render the clip
        log.info(f"[ReRender] Starting re-render for clip {clip_index} | "
                 f"style={style_config['subtitle_style']} | grade={color_grade} | "
                 f"zoom={zoom_style} | aspect={aspect_ratio}")

        # Use render_clip_pro if available and requested
        if use_pro:
            try:
                output_path = render_clip_pro(
                    video_path=source_video_path,
                    job_id=f"{job_data['job_id']}_rerender",
                    clip=adjusted_clip,
                    transcript=transcript,
                    style_config=style_config,
                    clip_idx=clip_index,
                    face_data=face_data,
                    color_grade=color_grade,
                    auto_zoom=zoom_style != "none",
                    creative_config=creative_config,
                    sfx_enabled=editor_state.get("sfx_enabled", True),
                )
            except Exception as e:
                log.warning(f"[ReRender] render_pro failed, falling back to basic: {e}")
                output_path = render_clip(
                    video_path=source_video_path,
                    job_id=f"{job_data['job_id']}_rerender",
                    clip=adjusted_clip,
                    transcript=transcript,
                    style_config=style_config,
                    clip_index=clip_index,
                    face_data=face_data,
                    color_grade=color_grade,
                    auto_zoom=zoom_style != "none",
                    creative_config=creative_config,
                    speed_ramp=editor_state.get("speed_ramp_type") if speed_ramp else None,
                )
        else:
            output_path = render_clip(
                video_path=source_video_path,
                job_id=f"{job_data['job_id']}_rerender",
                clip=adjusted_clip,
                transcript=transcript,
                style_config=style_config,
                clip_index=clip_index,
                face_data=face_data,
                color_grade=color_grade,
                auto_zoom=zoom_style != "none",
                creative_config=creative_config,
                speed_ramp=editor_state.get("speed_ramp_type") if speed_ramp else None,
            )

        # 12. Apply audio post-processing
        audio_config = render_config.get("audio_config", {})
        if audio_config.get("normalize_audio") or audio_config.get("bass_boost") or \
           audio_config.get("voice_volume", 100) != 100:
            output_path = apply_audio_processing(output_path, audio_config)
            if audio_config.get("voice_volume", 100) != 100:
                changes.append(f"Voice volume: {audio_config['voice_volume']}%")
            if audio_config.get("bass_boost"):
                changes.append("Bass boost enabled")
            if audio_config.get("normalize_audio"):
                changes.append("Audio normalized")

        # 13. Apply watermark
        branding = render_config.get("branding", {})
        if branding.get("show_watermark") and branding.get("watermark_text"):
            output_path = apply_watermark(
                output_path,
                branding["watermark_text"],
                branding["watermark_position"],
            )
            changes.append(f"Watermark: '{branding['watermark_text']}'")

        # 14. Apply overlay burn-in
        if overlays is None:
            overlays = editor_state.get("overlays") or editor_state.get("elements")

        if overlays:
            clip_start = adjusted_clip.get("start", 0)
            clip_end = adjusted_clip.get("end", clip_start + 45)
            overlay_out = output_path.with_suffix(f".overlays{output_path.suffix}")

            log.info(f"[ReRender] Burning in {len(overlays)} overlays for clip {clip_index}")

            burned_path = apply_overlays_to_video(
                input_path=output_path,
                output_path=overlay_out,
                overlays=overlays,
                video_w=w,
                video_h=h,
                clip_start=clip_start,
                clip_end=clip_end,
            )
            if burned_path != output_path and burned_path.exists():
                output_path = burned_path
                changes.append(f"Overlays burned in: {len(overlays)} elements")

        # 14. Verify output
        if not output_path.exists():
            return {
                "status": "error",
                "error": "Re-rendered output file not found",
            }

        render_time = time.time() - start_time
        file_size_mb = output_path.stat().st_size / (1024 * 1024)

        log.info(f"[ReRender] Complete: {output_path.name} | "
                 f"{file_size_mb:.1f}MB | {render_time:.1f}s | "
                 f"Changes: {len(changes)}")

        return {
            "status": "success",
            "output_path": str(output_path),
            "output_url": f"/output/{job_data['job_id']}_rerender/{output_path.name}",
            "clip_index": clip_index,
            "render_time_seconds": round(render_time, 1),
            "file_size_mb": round(file_size_mb, 1),
            "changes_applied": changes if changes else ["No changes from original"],
            "render_config": {
                "subtitle_style": style_config["subtitle_style"],
                "animation": style_config["animation"],
                "color_grade": color_grade,
                "zoom_style": zoom_style,
                "zoom_level": zoom_level,
                "aspect_ratio": aspect_ratio,
                "speed_ramp": speed_ramp,
                "speed_ramp_type": editor_state.get("speed_ramp_type", "none"),
                "watermark": branding.get("show_watermark", False),
                "normalize_audio": audio_config.get("normalize_audio", True),
                "trim_start": adjusted_clip["start"],
                "trim_end": adjusted_clip["end"],
            },
        }

    except Exception as e:
        log.error(f"[ReRender] Failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "render_time_seconds": round(time.time() - start_time, 1),
        }


# ── Batch Re-Render (All Clips) ─────────────────────

def rerender_all_clips(
    job_data: Dict,
    editor_state: Dict,
    source_video_path: Optional[Path] = None,
    transcript: Optional[Dict] = None,
    face_data: Optional[List[Dict]] = None,
    overlays: Optional[List[Dict]] = None,
) -> List[Dict]:
    """
    Re-render ALL clips in a job with the same personalization settings.

    This is used when the user clicks "Apply to All" in the editor.
    """
    clips = json.loads(job_data.get("clips", "[]"))
    results = []

    for i in range(len(clips)):
        log.info(f"[ReRender] Batch: clip {i}/{len(clips)}")
        result = rerender_clip_with_personalization(
            job_data=job_data,
            clip_index=i,
            editor_state=editor_state,
            source_video_path=source_video_path,
            transcript=transcript,
            face_data=face_data,
            overlays=overlays,
        )
        results.append(result)

    return results


# ── Re-Render with Auto-Reframe (Aspect Change) ────

def rerender_with_reframe(
    job_data: Dict,
    clip_index: int,
    editor_state: Dict,
    source_video_path: Optional[Path] = None,
    face_data: Optional[List[Dict]] = None,
    overlays: Optional[List[Dict]] = None,
) -> Dict:
    """
    Re-render a clip with aspect ratio change + auto-reframe.

    When the user changes from 9:16 to 1:1 or 16:9, we need to
    use the face tracking data to keep the speaker in frame.
    """
    from .reframe_engine import auto_reframe

    # First do normal re-render
    result = rerender_clip_with_personalization(
        job_data=job_data,
        clip_index=clip_index,
        editor_state=editor_state,
        source_video_path=source_video_path,
        face_data=face_data,
        overlays=overlays,
    )

    if result["status"] != "success":
        return result

    # If aspect ratio changed and auto-reframe is on, apply reframe
    target_aspect = editor_state.get("aspect_ratio", "9:16")
    if target_aspect != "9:16" and editor_state.get("auto_reframe", True) and face_data:
        clip = json.loads(job_data.get("clips", "[]"))[clip_index]

        from .constants import ASPECT_RATIOS as AR
        target_w, target_h = AR.get(target_aspect, (1080, 1080))

        reframe = auto_reframe(
            face_data=face_data,
            source_width=1920,
            source_height=1080,
            target_width=target_w,
            target_height=target_h,
            clip_start=clip["start"],
            clip_end=clip["end"],
        )

        result["reframe_applied"] = True
        result["reframe_quality"] = reframe.tracking_quality
        result["reframe_coverage"] = reframe.face_coverage

    return result
