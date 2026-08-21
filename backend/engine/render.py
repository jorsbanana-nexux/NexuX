"""
NexuX V8.0 — Rendering Engine
===============================================
FFmpeg-powered clip rendering with:
- ASS/SSA dynamic subtitles (per-word styling)
- Ken Burns auto-zoom
- Color grading presets (8 styles)
- Multi-speaker color coding
- Background bar for readability
- Shadow effects
"""
import random, subprocess, json
from pathlib import Path
from typing import List, Dict, Optional
import logging

from .constants import (
    OUTPUT_DIR, ASPECT_RATIOS, VIDEO_CODECS, AUDIO_CODECS, COLOR_GRADES,
)
from .creative_brain import get_transition_filter, get_zoom_filter, ZOOM_STYLES
from .utils import (
    to_unix, rel_path, fmt_time, retry, run_ffmpeg,
)
from .subtitle_quality import group_words_for_readability, smart_line_break, MAX_LINE_LENGTH
from .styles import (
    resolve_style, get_animation_tag, get_position, hex_to_ass,
    SPEAKER_PALETTE,
)

log = logging.getLogger("nexus.render")



# ── Speed Ramp Presets (V8.0) ──
SPEED_RAMP_PRESETS = {
    'dramatic_slowmo': {
        'segments': [(0.0, 0.7, 1.0), (0.7, 0.85, 0.5), (0.85, 1.0, 1.0)],
        'description': 'Normal → slow-mo at key moment → normal',
    },
    'energy_build': {
        'segments': [(0.0, 0.5, 0.8), (0.5, 0.8, 1.0), (0.8, 1.0, 1.3)],
        'description': 'Gradual speed up to energetic finish',
    },
    'beat_drop': {
        'segments': [(0.0, 0.8, 1.0), (0.8, 0.85, 0.0), (0.85, 1.0, 1.5)],
        'description': 'Normal → freeze frame → burst',
    },
    'slow_intro': {
        'segments': [(0.0, 0.3, 0.5), (0.3, 1.0, 1.0)],
        'description': 'Slow dramatic intro → normal speed',
    },
    'pulse': {
        'segments': [(0.0, 0.25, 1.0), (0.25, 0.30, 0.3), (0.30, 0.55, 1.0), (0.55, 0.60, 0.3), (0.60, 1.0, 1.0)],
        'description': 'Pulsing speed changes on beat',
    },
}


def get_speed_ramp_filter(preset_name: str, clip_duration: float) -> str:
    """Generate FFmpeg setpts + atempo filter chain for speed ramping.
    
    Uses setpts for video speed and atempo for audio speed.
    Each segment specifies start_ratio, end_ratio (of clip), and speed_multiplier.
    """
    preset = SPEED_RAMP_PRESETS.get(preset_name)
    if not preset:
        return ''
    
    segments = preset['segments']
    filters = []
    
    for i, (start_ratio, end_ratio, speed) in enumerate(segments):
        seg_start = start_ratio * clip_duration
        seg_end = end_ratio * clip_duration
        seg_dur = seg_end - seg_start
        
        if speed == 0:
            # Freeze frame: use framestepper
            filters.append(f"select='between(t,{seg_start},{seg_end})'")
            continue
        
        # setpts for video: PTS = PTS / speed
        # We use trim + setpts for each segment
        pts_factor = 1.0 / speed
        
        # For audio: atempo can only handle 0.5-2.0 range
        # Chain multiple atempo for extreme speeds
        atempo_filters = []
        remaining = speed
        while remaining > 2.0:
            atempo_filters.append('atempo=2.0')
            remaining /= 2.0
        while remaining < 0.5:
            atempo_filters.append('atempo=0.5')
            remaining /= 0.5
        atempo_filters.append(f'atempo={remaining:.3f}')
        atempo_chain = ','.join(atempo_filters)
        
        filters.append(f'trim=start={seg_start}:end={seg_end},setpts={pts_factor:.4f}*PTS,{atempo_chain}')
    
    if not filters:
        return ''
    
    # Combine all segments with concat
    n = len(filters)
    filter_parts = []
    for i, f in enumerate(filters):
        filter_parts.append(f'[{i}:v]{f}[v{i}]')
    
    concat_inputs = ''.join(f'[v{i}]' for i in range(n))
    filter_parts.append(f'{concat_inputs}concat=n={n}:v=1:a=0[vout]')
    
    return ';'.join(filter_parts)


def render_clip(
    video_path: Path,
    job_id: str,
    clip: Dict,
    transcript: Dict,
    style_config: Dict,
    clip_index: int = 0,
    face_data: Optional[List[Dict]] = None,
    color_grade: str = "none",
    auto_zoom: bool = True,
    video_codec: str = "h264",
    audio_codec: str = "aac",
    creative_config: Optional[Dict] = None,
    speed_ramp: str = None,
) -> Path:
    """Render a single clip with full effects.
    
    Args:
        video_path: Source video
        job_id: Job identifier
        clip: Clip dict from analyze_content()
        transcript: Full transcript dict
        style_config: Subtitle style configuration
        clip_index: Index for output filename
        face_data: Optional face tracking for smart zoom
        color_grade: Color grade preset name
        auto_zoom: Enable Ken Burns effect
        video_codec: Video codec (h264/h265/vp9/av1)
        audio_codec: Audio codec (aac/mp3/opus)
    
    Returns:
        Path to rendered clip
    """
    out_dir = OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"clip_{clip_index:02d}.mp4"

    # Timing
    clip_dur = clip["end"] - clip["start"]
    start_time = max(0, clip["start"] - 0.5)
    clip_len = clip_dur + 1.0  # small padding

    # Resolution
    ratio = style_config.get("aspect_ratio", "9:16")
    w, h = ASPECT_RATIOS.get(ratio, (1080, 1920))

    # Codec configs
    vcodec = VIDEO_CODECS.get(video_codec, VIDEO_CODECS["h264"])
    acodec = AUDIO_CODECS.get(audio_codec, AUDIO_CODECS["aac"])

    # ── Build ASS Subtitle ──
    ass_path = _build_ass(transcript, clip, style_config, job_id, clip_index, w, h)
    ass_rel = rel_path(ass_path)
    video_rel = rel_path(video_path)
    output_rel = rel_path(output_path)

    # ── Video Filter Chain ──
    # Order: scale → crop → zoompan → ass (subtitles) → color_grade
    # Subtitles burned AFTER scaling so they render crisp at target resolution
    vf_parts = [
        f"scale={w}:{h}:force_original_aspect_ratio=increase",
        f"crop={w}:{h}",
    ]

    # Smart zoom — V8.0: uses creative brain zoom style if available
    if creative_config and creative_config.get("zoom_style"):
        zoom_style = creative_config.get("zoom_style", "subtle")
        if auto_zoom and clip_dur > 3:
            zoom_filter = get_zoom_filter(zoom_style, clip_dur, w, h)
            vf_parts.append(zoom_filter)
    elif auto_zoom and clip_dur > 3:
        zoom_filter = _build_smart_zoom(clip, face_data, w, h)
        vf_parts.append(zoom_filter)

    # Subtitle burn-in (after scale/crop/zoom so text is crisp at final resolution)
    if ass_rel:
        vf_parts.append(f"ass='{ass_rel}'")

    # Color grading
    grade_filter = COLOR_GRADES.get(color_grade, "")
    if grade_filter:
        vf_parts.append(grade_filter)

    vf = ",".join(vf_parts)

    # ── Transition filter (V8.0: creative brain) ──
    if creative_config and creative_config.get("transition"):
        transition_filter = get_transition_filter(
            creative_config.get("transition", "hard_cut"),
            clip_dur, w, h
        )
        if transition_filter:
            vf_parts.append(transition_filter)
            vf = ",".join(vf_parts)

    # ── Speed Ramp (V8.0) ──
    speed_ramp_filter = ''
    if speed_ramp and speed_ramp != 'none':
        speed_ramp_filter = get_speed_ramp_filter(speed_ramp, clip_dur)
        if speed_ramp_filter:
            log.info(f"[Render] Speed ramp: {speed_ramp} for {clip_dur:.1f}s clip")

    # ── Build FFmpeg Command ──
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-i", video_rel,
        "-t", str(clip_len),
        "-vf", vf,
        "-c:v", vcodec["codec"],
        "-preset", vcodec["preset"],
        "-crf", vcodec["crf"],
        "-c:a", acodec["codec"],
        "-b:a", acodec["bitrate"],
        "-movflags", "+faststart",  # Web-optimized
        output_rel,
    ]

    log.info(f"[Render] Clip {clip_index}: {clip_dur:.1f}s | "
             f"Style: {style_config.get('subtitle_style','?')} | "
             f"Color: {color_grade} | Zoom: {auto_zoom}")
    
    r = subprocess.run(
        cmd, capture_output=True, text=True,
        timeout=1200, cwd=to_unix(Path.cwd()))

    if r.returncode != 0:
        err = r.stderr[-800:] if len(r.stderr) > 800 else r.stderr
        raise RuntimeError(f"FFmpeg render failed: {err}")

    size_mb = output_path.stat().st_size / (1024 * 1024) if output_path.exists() else 0
    log.info(f"[Render] Clip {clip_index} OK: {output_path.name} ({size_mb:.1f} MB)")
    return output_path



def _build_smart_zoom(
    clip: Dict,
    face_data: Optional[List[Dict]],
    canvas_w: int,
    canvas_h: int,
) -> str:
    """Build FFmpeg zoompan filter using face tracking data.
    
    V8.0: Instead of random zoom, this tracks the speaker's face
    and smoothly follows them. If no face data, falls back to
    a gentle, deterministic Ken Burns effect.
    """
    clip_start = clip["start"]
    clip_end = clip["end"]
    clip_dur = clip_end - clip_start

    if face_data:
        # Get face positions within this clip's time range
        relevant = [
            fd for fd in face_data
            if clip_start <= fd.get("time", 0) <= clip_end
            and fd.get("faces")
        ]

        if relevant and len(relevant) >= 3:
            # Calculate average face position (normalized 0-1)
            avg_x = sum(f["faces"][0]["x"] + f["faces"][0]["w"] / 2
                        for f in relevant) / len(relevant)
            avg_y = sum(f["faces"][0]["y"] + f["faces"][0]["h"] / 2
                        for f in relevant) / len(relevant)

            # Determine zoom level based on face size
            avg_face_w = sum(f["faces"][0]["w"] for f in relevant) / len(relevant)
            # Larger face = less zoom needed; smaller face = more zoom
            if avg_face_w > 0.25:
                zoom_max = 1.05  # Face already large, gentle zoom
            elif avg_face_w > 0.12:
                zoom_max = 1.12  # Medium face, moderate zoom
            else:
                zoom_max = 1.20  # Small face, more aggressive zoom

            # Center on face position, clamped to valid range
            # zoompan x/y are in output pixel space at zoom factor
            center_x = f"{avg_x:.3f}"
            center_y = f"{avg_y:.3f}"

            # Build smooth zoompan that centers on the face
            zoom_filter = (
                f"zoompan=z='min(zoom+0.001,{zoom_max})':d=1:"
                f"x='iw*{center_x}-(iw/zoom*{center_x})':"
                f"y='ih*{center_y}-(ih/zoom*{center_y})':"
                f"s={canvas_w}x{canvas_h}"
            )
            log.info(f"[Render] Smart zoom: face-centered ({center_x}, {center_y}) "
                     f"zoom_max={zoom_max}")
            return zoom_filter

    # Fallback: deterministic gentle zoom (not random)
    # Use clip index as seed for variety, but predictable per clip
    zoom_max = 1.06 + (clip.get("clip_index", 0) * 0.01)
    zoom_max = min(zoom_max, 1.10)
    zoom_filter = (
        f"zoompan=z='min(zoom+0.0015,{zoom_max:.2f})':d=1:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"s={canvas_w}x{canvas_h}"
    )
    log.info(f"[Render] Smart zoom: Ken Burns fallback zoom_max={zoom_max:.2f}")
    return zoom_filter


def _build_ass(
    transcript: Dict,
    clip: Dict,
    style_config: Dict,
    job_id: str,
    clip_idx: int,
    canvas_w: int,
    canvas_h: int,
) -> Path:
    """Build ASS subtitle file with dynamic per-word styling."""
    out_dir = OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    ass_path = out_dir / f"sub_{clip_idx:02d}.ass"

    s = resolve_style(style_config)
    pc = get_position(s["position"], canvas_w, canvas_h)

    # Speaker color map
    speaker_colors: Dict[str, int] = {}
    speakers_seen: List[str] = []

    def _spk_idx(spk: str) -> int:
        if spk not in speaker_colors:
            speaker_colors[spk] = len(speakers_seen) % len(SPEAKER_PALETTE)
            speakers_seen.append(spk)
        return speaker_colors[spk]

    pri_ass = hex_to_ass(s["primary"])
    hl_ass = hex_to_ass(s["highlight"])
    stk_ass = hex_to_ass(s["stroke"])
    bold = 1 if s["bold"] else 0
    sw = s["stroke_width"]
    al = pc["align"]
    mv = pc["marv"]
    fs = s["font_size"]
    font = s["font"]

    # ── ASS Header ──
    lines = [
        "[Script Info]",
        "Title: NexuX V8.0",
        "ScriptType: v8.00+",
        "WrapStyle: 0",
        "ScaledBorderAndShadow: yes",
        f"PlayResX: {canvas_w}",
        f"PlayResY: {canvas_h}",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
    ]

    # Default style
    shadow = 4 if s.get("shadow") else 0
    lines.append(
        f"Style: Default,{font},{fs},{pri_ass},{pri_ass},{stk_ass},{stk_ass},"
        f"{bold},0,0,0,100,100,0,0,1,{sw},{shadow},{al},80,80,{mv},1")

    # Highlight style
    lines.append(
        f"Style: Highlight,{font},{fs+6},{hl_ass},{hl_ass},{stk_ass},{stk_ass},"
        f"{bold},0,0,0,100,100,0,0,1,{sw},{shadow+2},{al},80,80,{mv},1")

    # Background bar style (for readability)
    if s.get("bg_bar"):
        bg_opacity = int(s.get("bg_opacity", 0.35) * 255)
        bg_color = f"&H{255-bg_opacity:02X}000000"
        lines.append(
            f"Style: BGBar,{font},{fs},{pri_ass},{pri_ass},{stk_ass},{bg_color},"
            f"0,0,0,0,100,100,0,0,3,0,0,{al},80,80,{mv},1")

    # Per-speaker styles
    for i, spc in enumerate(SPEAKER_PALETTE):
        sp_ass = hex_to_ass(spc)
        lines.append(
            f"Style: S{i},{font},{fs},{sp_ass},{sp_ass},{stk_ass},{stk_ass},"
            f"{bold},0,0,0,100,100,0,0,1,{sw},{shadow},{al},80,80,{mv},1")
        lines.append(
            f"Style: S{i}H,{font},{fs+6},{sp_ass},{sp_ass},{stk_ass},{stk_ass},"
            f"{bold},0,0,0,100,100,0,0,1,{sw},{shadow+2},{al},80,80,{mv},1")

    lines.extend([
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ])

    # ── Generate Dialogue Events ──
    cs, ce = clip["start"], clip["end"]
    word_counter = 0

    segments = transcript.get("segments", [])
    if not segments:
        # Minimal placeholder
        lines.append(
            f"Dialogue: 0,{fmt_time(0)},{fmt_time(clip['end']-clip['start'])},"
            f"Default,,0,0,0,,Subtitle data missing")

    for seg in segments:
        try:
            ss = float(seg.get("start", 0))
            se = float(seg.get("end", 0))
        except (TypeError, ValueError):
            continue

        # Skip segments outside clip range
        if se < cs or ss > ce:
            continue

        spk = seg.get("speaker", "SPEAKER_00")
        si = _spk_idx(spk)

        words = seg.get("words", [])
        if not words:
            # Fallback: single line per segment
            ls = max(0, ss - cs)
            le = max(ls + 0.5, se - cs)
            text = seg.get("text", "").strip()
            if not text:
                continue
            text = text.replace("\n", "\\N")
            tag = get_animation_tag(s["animation"])
            sty = f"S{si}H" if s["highlight_words"] else f"S{si}"
            
            # Add background bar if enabled
            if s.get("bg_bar") and text:
                lines.append(
                    f"Dialogue: -1,{fmt_time(ls)},{fmt_time(le)},"
                    f"BGBar,,0,0,0,,{{\\3a&H80&}}{text}")
            
            lines.append(
                f"Dialogue: 0,{fmt_time(ls)},{fmt_time(le)},"
                f"{sty},,0,0,0,,{tag}{text}")
            continue

        # Word-level subtitle
        for w in words:
            try:
                ws = float(w.get("start", ss))
                we = float(w.get("end", se))
            except (TypeError, ValueError):
                ws, we = ss, se

            if we < cs or ws > ce:
                continue

            ls = max(0, ws - cs)
            le = min(we - cs, ce - cs)
            if le <= ls:
                le = ls + 0.3

            txt = w.get("word", w.get("text", "")).strip()
            if not txt:
                continue

            tag = get_animation_tag(s["animation"], word_counter)
            word_counter += 1
            sty = f"S{si}H" if s["highlight_words"] else f"S{si}"

            # Background bar (layer -1)
            if s.get("bg_bar") and word_counter % 3 == 0:
                lines.append(
                    f"Dialogue: -1,{fmt_time(ls)},{fmt_time(le)},"
                    f"BGBar,,0,0,0,,{{\\3a&H80&}}{txt}")

            lines.append(
                f"Dialogue: 0,{fmt_time(ls)},{fmt_time(le)},"
                f"{sty},,0,0,0,,{tag}{txt}")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return ass_path


# ── Concatenate Clips ───────────────────────────────

def concatenate_clips(job_id: str, clip_paths: List[Path]) -> Path:
    """Concatenate multiple clips into final video."""
    out_dir = OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    final = out_dir / f"{job_id}_final.mp4"

    if len(clip_paths) == 1:
        # Single clip, just copy
        import shutil
        shutil.copy(clip_paths[0], final)
        return final

    cf = out_dir / "concat.txt"
    with open(cf, "w", encoding="utf-8") as f:
        for cp in clip_paths:
            f.write(f"file '{rel_path(cp)}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", rel_path(cf),
        "-c", "copy",
        rel_path(final),
    ]

    r = subprocess.run(cmd, capture_output=True, text=True,
                       timeout=300, cwd=to_unix(Path.cwd()))
    if r.returncode != 0:
        err = r.stderr[-500:] if len(r.stderr) > 500 else r.stderr
        raise RuntimeError(f"Concat failed: {err}")

    size_mb = final.stat().st_size / (1024 * 1024)
    log.info(f"[Concat] Final: {final.name} ({size_mb:.1f} MB)")
    return final


# ── Audio Processing ────────────────────────────────

def mix_bgm(
    video_path: Path,
    bgm_path: Path,
    output_path: Path,
    volume_db: float = -18.0,
    fade_in: float = 2.0,
    fade_out: float = 3.0,
) -> Path:
    """Mix background music into video."""
    cmd = [
        "ffmpeg", "-y",
        "-i", rel_path(video_path),
        "-i", rel_path(bgm_path),
        "-filter_complex",
        f"[1:a]volume={volume_db}dB,"
        f"afade=t=in:d={fade_in},"
        f"afade=t=out:st={fade_in}:d={fade_out}[bgm];"
        f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=3[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        rel_path(output_path),
    ]
    run_ffmpeg(cmd, timeout=300, description="BGM Mix")
    return output_path


def normalize_audio(
    video_path: Path,
    output_path: Path,
    target_db: float = -16.0,
) -> Path:
    """Normalize audio loudness to broadcast standard."""
    cmd = [
        "ffmpeg", "-y",
        "-i", rel_path(video_path),
        "-af", f"loudnorm=I={target_db}:TP=-1.5:LRA=11",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        rel_path(output_path),
    ]
    run_ffmpeg(cmd, timeout=300, description="Audio Normalize")
    return output_path
