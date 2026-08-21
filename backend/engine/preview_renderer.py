"""
NexuX V9.0 — Real-Time FFmpeg Preview Renderer
=================================================
Generates quick low-resolution preview clips so the user can see
their text overlays, color grade, and zoom burned into the video
BEFORE committing to a full render.

- Preview clips: 480p, 5-second segment, <3s render time
- Preview frames: single PNG with overlays applied
- Uses FFmpeg drawtext (faster than ASS subtitles for preview)
"""
import subprocess
import os
import json
import time
import tempfile
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

log = logging.getLogger("nexus.preview")


@dataclass
class PreviewResult:
    success: bool
    output_path: Optional[str]
    output_url: Optional[str]
    render_time: float
    error: Optional[str] = None


def generate_preview(
    job_id: str,
    clip_index: int,
    editor_state: Dict,
    source_video_path: Path,
    current_time: float = 0.0,
) -> PreviewResult:
    """
    Generate a 480p preview clip with overlays burned in.
    
    Renders a 5-second segment around the current playhead position.
    Target: <3 seconds render time.
    """
    start_time = time.time()
    
    try:
        output_dir = Path(os.environ.get("NEXUX_OUTPUT_DIR", "output")) / f"{job_id}_preview"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"preview_{clip_index}_{int(current_time)}.mp4"
        
        # Preview settings: 480p, 5 seconds
        preview_w, preview_h = 270, 480  # 9:16 at 480p height
        aspect_ratio = editor_state.get("aspect_ratio", "9:16")
        if aspect_ratio == "1:1":
            preview_w, preview_h = 480, 480
        elif aspect_ratio == "16:9":
            preview_w, preview_h = 480, 270
        elif aspect_ratio == "4:5":
            preview_w, preview_h = 384, 480
        
        # 5-second segment around current_time
        segment_start = max(0, current_time - 1.0)
        segment_dur = 5.0
        
        elements = editor_state.get("elements", [])
        layout_mode = editor_state.get("layout_mode", "Fill")
        
        # ── Build filter chain ──
        vf_parts = []
        
        # Scale + crop (fast at 480p)
        if layout_mode == "Fill":
            vf_parts.append(f"scale={preview_w}:{preview_h}:force_original_aspect_ratio=increase")
            vf_parts.append(f"crop={preview_w}:{preview_h}")
        else:
            vf_parts.append(f"scale={preview_w}:{preview_h}:force_original_aspect_ratio=decrease")
            vf_parts.append(f"pad={preview_w}:{preview_h}:(ow-iw)/2:(oh-ih)/2:black")
        
        # Color grade
        grade = editor_state.get("color_grade", "none")
        grade_filters = {
            "none": "", "warm": "eq=saturation=1.15:brightness=0.03:gamma=1.05",
            "cool": "eq=saturation=0.90:brightness=-0.02:gamma=0.95",
            "vibrant": "eq=saturation=1.35:contrast=1.10:brightness=0.04",
            "cinematic": "eq=saturation=0.82:contrast=1.15:brightness=-0.04:gamma=1.02",
        }
        g = grade_filters.get(grade, "")
        if g:
            vf_parts.append(g)
        
        # Zoom
        zoom_style = editor_state.get("zoom_style", "none")
        zoom_level = editor_state.get("zoom_level", 1.0)
        if zoom_style != "none" and zoom_level > 1.0:
            if zoom_style == "subtle":
                max_z = 1.0 + (zoom_level - 1.0) * 0.3
                vf_parts.append(f"zoompan=z='min(zoom+0.001,{max_z:.2f})':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={preview_w}x{preview_h}:fps=24")
            elif zoom_style == "dramatic":
                vf_parts.append(f"zoompan=z='min(zoom+0.003,{zoom_level:.2f})':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={preview_w}x{preview_h}:fps=24")
        
        # Text overlays (drawtext — fast)
        sorted_elements = sorted(
            [e for e in elements if e.get("visible", True) and e.get("type") == "text"],
            key=lambda e: e.get("z_index", 0)
        )
        
        for el in sorted_elements:
            content = el.get("content", "").replace("\n", "\\n")
            if not content:
                continue
            
            # Position (relative to preview canvas)
            x_expr = f"(w*{el.get('x', 50)}.0/100)-(tw/2)"
            y_expr = f"(h*{el.get('y', 50)}.0/100)-(th/2)"
            
            # Timing (relative to segment start)
            el_start = max(0, float(el.get("start", 0)) - segment_start + current_time - segment_start)
            el_end = min(segment_dur, float(el.get("end", segment_dur)) - segment_start + current_time - segment_start)
            
            # Simpler timing for preview: just show if within segment
            el_abs_start = float(el.get("start", 0))
            el_abs_end = float(el.get("end", 999))
            # Convert to segment-relative time
            seg_rel_start = max(0, el_abs_start - segment_start)
            seg_rel_end = min(segment_dur, el_abs_end - segment_start)
            
            if seg_rel_end <= seg_rel_start:
                continue  # Element not visible in this segment
            
            font_size = max(8, int(el.get("font_size", 24) * (preview_w / 400)))
            
            fontcolor = el.get("color", "#FFFFFF")
            fc = fontcolor.replace("#", "0x") if fontcolor.startswith("#") else "0xFFFFFF"
            
            bg = el.get("bg_color", "transparent")
            box_str = ""
            if bg and bg != "transparent" and bg != "":
                bgc = bg.replace("#", "0x") if bg.startswith("#") else "0x000000"
                box_str = f":box=1:boxcolor={bgc}@0.85:boxborderw=4"
            
            # Simple fade in/out for preview
            anim_in = el.get("animation_in", "fade")
            fade_filter = ""
            if anim_in == "fade":
                fade_dur = min(0.3, (seg_rel_end - seg_rel_start) * 0.2)
                fade_filter = f",fade=t=in:st={seg_rel_start:.2f}:d={fade_dur:.2f}"
            
            drawtext = (
                f"drawtext=text='{content}':"
                f"x='{x_expr}':y='{y_expr}':"
                f"fontsize={font_size}:"
                f"fontcolor={fc}"
                f":borderw=1:bordercolor=0x000000"
                f"{box_str}"
                f":enable='between(t,{seg_rel_start:.2f},{seg_rel_end:.2f})'"
            )
            vf_parts.append(drawtext)
        
        # Watermark
        if editor_state.get("show_watermark", False) and editor_state.get("watermark_text", ""):
            wm_text = editor_state["watermark_text"]
            pos_map = {
                "top-left": "x=5:y=5", "top-right": "x=w-tw-5:y=5",
                "bottom-left": "x=5:y=h-th-5", "bottom-right": "x=w-tw-5:y=h-th-5",
            }
            wm_pos = pos_map.get(editor_state.get("watermark_position", "bottom-right"), pos_map["bottom-right"])
            vf_parts.append(f"drawtext=text='{wm_text}':{wm_pos}:fontsize=12:fontcolor=white@0.5")
        
        vf = ",".join(vf_parts)
        
        # Build FFmpeg command — fast preset for preview
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(segment_start),
            "-i", str(source_video_path),
            "-t", str(segment_dur),
            "-vf", vf,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart",
            str(output_path),
        ]
        
        log.info(f"[Preview] Job {job_id} clip {clip_index} | "
                 f"{len(sorted_elements)} elements | {preview_w}x{preview_h} | "
                 f"@ {segment_start:.1f}s")
        
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            err = r.stderr[-500:] if len(r.stderr) > 500 else r.stderr
            log.error(f"[Preview] FFmpeg failed: {err}")
            return PreviewResult(False, None, None, time.time() - start_time, err)
        
        render_time = time.time() - start_time
        file_size = output_path.stat().st_size / (1024 * 1024) if output_path.exists() else 0
        
        log.info(f"[Preview] Complete: {output_path.name} | {file_size:.1f}MB | {render_time:.1f}s")
        
        return PreviewResult(
            True, str(output_path),
            f"/output/{job_id}_preview/{output_path.name}",
            render_time
        )
        
    except Exception as e:
        log.error(f"[Preview] Failed: {e}", exc_info=True)
        return PreviewResult(False, None, None, time.time() - start_time, str(e))


def generate_preview_frame(
    job_id: str,
    clip_index: int,
    timestamp: float,
    editor_state: Dict,
    source_video_path: Path,
) -> PreviewResult:
    """Generate a single PNG frame with overlays applied."""
    start_time = time.time()
    
    try:
        output_dir = Path(os.environ.get("NEXUX_OUTPUT_DIR", "output")) / f"{job_id}_preview"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"frame_{clip_index}_{int(timestamp)}.png"
        
        preview_w, preview_h = 270, 480
        aspect_ratio = editor_state.get("aspect_ratio", "9:16")
        if aspect_ratio == "1:1":
            preview_w, preview_h = 480, 480
        elif aspect_ratio == "16:9":
            preview_w, preview_h = 480, 270
        
        elements = editor_state.get("elements", [])
        
        # Build filter chain (same as generate_preview but for single frame)
        vf_parts = [
            f"scale={preview_w}:{preview_h}:force_original_aspect_ratio=increase",
            f"crop={preview_w}:{preview_h}",
        ]
        
        # Color grade
        grade = editor_state.get("color_grade", "none")
        grade_filters = {
            "none": "", "warm": "eq=saturation=1.15:brightness=0.03:gamma=1.05",
            "cool": "eq=saturation=0.90:brightness=-0.02:gamma=0.95",
            "vibrant": "eq=saturation=1.35:contrast=1.10:brightness=0.04",
            "cinematic": "eq=saturation=0.82:contrast=1.15:brightness=-0.04:gamma=1.02",
        }
        g = grade_filters.get(grade, "")
        if g:
            vf_parts.append(g)
        
        # Text overlays — only visible at this timestamp
        for el in sorted(
            [e for e in elements if e.get("visible", True) and e.get("type") == "text"],
            key=lambda e: e.get("z_index", 0)
        ):
            el_start = float(el.get("start", 0))
            el_end = float(el.get("end", 999))
            if not (el_start <= timestamp <= el_end):
                continue
            
            content = el.get("content", "").replace("\n", "\\n")
            if not content:
                continue
            
            x_expr = f"(w*{el.get('x', 50)}.0/100)-(tw/2)"
            y_expr = f"(h*{el.get('y', 50)}.0/100)-(th/2)"
            font_size = max(8, int(el.get("font_size", 24) * (preview_w / 400)))
            
            fontcolor = el.get("color", "#FFFFFF")
            fc = fontcolor.replace("#", "0x") if fontcolor.startswith("#") else "0xFFFFFF"
            
            bg = el.get("bg_color", "transparent")
            box_str = ""
            if bg and bg != "transparent" and bg != "":
                bgc = bg.replace("#", "0x") if bg.startswith("#") else "0x000000"
                box_str = f":box=1:boxcolor={bgc}@0.85:boxborderw=4"
            
            vf_parts.append(
                f"drawtext=text='{content}':x='{x_expr}':y='{y_expr}':"
                f"fontsize={font_size}:fontcolor={fc}"
                f":borderw=1:bordercolor=0x000000{box_str}"
            )
        
        vf = ",".join(vf_parts)
        
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp),
            "-i", str(source_video_path),
            "-frames:v", "1",
            "-vf", vf,
            str(output_path),
        ]
        
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            return PreviewResult(False, None, None, time.time() - start_time, r.stderr[-300:])
        
        return PreviewResult(
            True, str(output_path),
            f"/output/{job_id}_preview/{output_path.name}",
            time.time() - start_time
        )
        
    except Exception as e:
        return PreviewResult(False, None, None, time.time() - start_time, str(e))
