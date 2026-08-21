"""
NexuX V8.0 — Mode 2: Multi-Source Compilation Engine
======================================================
Takes downloaded moments from multiple videos + narrative plan
and compiles them into one professional viral video.

Functions:
1. Assemble moments in narrative order
2. Add transitions between sources
3. Overlay TTS narration (replace original audio)
4. Add SFX at specified moments
5. Add text overlays (hook text + per-segment text)
6. Apply per-segment color grades and zoom
7. Generate styled thumbnail
8. Final render with all layers
"""
import subprocess
import json
import os
import shutil
import random
from pathlib import Path
from typing import Dict, List, Optional
from logging import getLogger

from .constants import OUTPUT_DIR, ASPECT_RATIOS, VIDEO_CODECS, AUDIO_CODECS, COLOR_GRADES
from .mode2_narrator import generate_tts_narration

log = getLogger("nexus.mode2.compiler")


def compile_video(
    job_id: str,
    keyword: str,
    moments: List[Dict],
    downloaded_files: Dict[int, List[Path]],
    production_plan: Dict,
    style_config: Dict,
    voice_enabled: bool = True,
    voice_name: str = "id-ID-ArdiNeural",
    sfx_enabled: bool = True,
    bgm_enabled: bool = True,
) -> Dict:
    """Compile multiple video moments into one viral video.
    
    Args:
        job_id: Unique job ID
        keyword: Search keyword
        moments: All analyzed moments
        downloaded_files: {video_idx: [file paths]}
        production_plan: LLM-generated plan (narrative, segments, SFX, etc.)
        style_config: Subtitle style config
        voice_enabled: TTS narration on/off
        voice_name: edge-tts voice name
        sfx_enabled: Sound effects on/off
        bgm_enabled: Background music on/off
    
    Returns:
        {"output_path": Path, "thumbnail_path": Path, "metadata": Dict}
    """
    out_dir = OUTPUT_DIR / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    
    ar = "9:16"
    w, h = ASPECT_RATIOS.get(ar, (1080, 1920))
    
    segments = production_plan.get("segments", [])
    narration_script = production_plan.get("narration_script", "")
    
    log.info(f"[Mode2] Compiling {len(segments)} segments from {len(downloaded_files)} sources")
    
    # ── Step 1: Generate TTS narration ──
    tts_audio = None
    if voice_enabled and narration_script:
        tts_path = out_dir / "narration_tts"
        tts_audio = generate_tts_narration(narration_script, tts_path, voice_name)
        if tts_audio:
            log.info(f"[Mode2] TTS narration generated: {tts_audio.name}")
        else:
            log.warning("[Mode2] TTS failed — using original audio")
    
    # ── Step 2: Process each segment ──
    segment_outputs = []
    total_duration = 0
    
    for seg_idx, seg in enumerate(segments):
        moment_idx = seg.get("moment_index", seg_idx)
        if moment_idx >= len(moments):
            continue
        
        moment = moments[moment_idx]
        video_idx = moment.get("video_idx", 0)
        files = downloaded_files.get(video_idx, [])
        
        if not files:
            log.warning(f"[Mode2] No downloaded file for segment {seg_idx} (video {video_idx})")
            continue
        
        # Use the first downloaded file for this video (matching the moment)
        # Find the file that covers the moment's time range
        source_file = files[0]  # Simplified — use first available
        
        # Process this segment
        seg_output = out_dir / f"seg_{seg_idx:02d}.mp4"
        
        zoom_style = seg.get("zoom_style", "subtle")
        color_grade = seg.get("color_grade", "none")
        text_overlay = seg.get("text_overlay", "")
        transition_in = seg.get("transition_in", "hard_cut")
        seg_dur = seg.get("duration_estimate", 10)
        
        # Build video filter chain
        vf_parts = [
            f"scale={w}:{h}:force_original_aspect_ratio=increase",
            f"crop={w}:{h}",
        ]
        
        # Zoom
        zoom_filter = _get_zoom_filter_pro(zoom_style, seg_dur, w, h)
        if zoom_filter:
            vf_parts.append(zoom_filter)
        
        # Color grade
        grade_filter = COLOR_GRADES.get(color_grade, "")
        if grade_filter:
            vf_parts.append(grade_filter)
        
        # Text overlay (drawtext)
        if text_overlay:
            safe_text = text_overlay.replace(":", "\\:").replace("'", "\\'").replace("%", "\\%")
            # Text appears with fade in/out
            fade_out = min(seg_dur - 0.3, 3.0)
            drawtext = (
                f"drawtext=text='{safe_text}'"
                f":fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                f":fontsize={int(h * 0.045)}"
                f":fontcolor=white"
                f":borderw=4:bordercolor=black@0.9"
                f":x=(w-text_w)/2"
                f":y=h*0.08"
                f":alpha='if(lt(t,0.3),t/0.3,if(gt(t,{fade_out}),max(0,({seg_dur}-t)/0.3),1))'"
            )
            vf_parts.append(drawtext)
        
        # Transition in (fade, zoom, etc.)
        if seg_idx > 0:  # No transition for first segment
            if transition_in == "fade":
                vf_parts.append(f"fade=t=in:st=0:d=0.3")
            elif transition_in == "dissolve":
                vf_parts.append(f"fade=t=in:st=0:d=0.5")
            elif transition_in == "zoom_in":
                vf_parts.append(f"zoompan=z='min(zoom+0.5,1.5)':d=1:s={w}x{h}")
            elif transition_in == "glitch":
                # Simulated glitch: quick scale pulse
                vf_parts.append("scale=1.02:1.02,scale=1:1")
            elif transition_in == "slide_up":
                vf_parts.append(f"fade=t=in:st=0:d=0.2")
        
        vf = ",".join(vf_parts)
        
        vcodec = VIDEO_CODECS.get("h264", VIDEO_CODECS["h264"])
        acodec = AUDIO_CODECS.get("aac", AUDIO_CODECS["aac"])
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(source_file),
            "-t", str(seg_dur),
            "-vf", vf,
            "-c:v", vcodec["codec"],
            "-preset", vcodec["preset"],
            "-crf", vcodec["crf"],
            "-c:a", acodec["codec"],
            "-b:a", acodec["bitrate"],
            "-movflags", "+faststart",
            str(seg_output),
        ]
        
        log.info(f"[Mode2] Rendering segment {seg_idx}: {zoom_style} | {color_grade} | {text_overlay[:20]}")
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if r.returncode != 0:
            log.error(f"[Mode2] Segment {seg_idx} render failed: {r.stderr[-300:]}")
            continue
        
        segment_outputs.append(seg_output)
        total_duration += seg_dur
    
    if not segment_outputs:
        log.error("[Mode2] No segments rendered successfully")
        return {"output_path": None, "thumbnail_path": None, "metadata": {}}
    
    # ── Step 3: Concatenate all segments ──
    concat_file = out_dir / "concat.txt"
    with open(concat_file, "w") as f:
        for p in segment_outputs:
            safe = str(p).replace("'", "\\'")
            f.write(f"file '{safe}'\n")
    
    merged_path = out_dir / "merged.mp4"
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        "-movflags", "+faststart",
        str(merged_path),
    ]
    
    log.info(f"[Mode2] Concatenating {len(segment_outputs)} segments")
    r = subprocess.run(cmd_concat, capture_output=True, text=True, timeout=120)
    
    if r.returncode != 0:
        log.error(f"[Mode2] Concat failed: {r.stderr[-300:]}")
        if segment_outputs:
            shutil.copy(segment_outputs[0], merged_path)
        else:
            return {"output_path": None, "thumbnail_path": None, "metadata": {}}
    
    # ── Step 4: Replace audio with TTS narration ──
    final_path = out_dir / "final_output.mp4"
    
    if tts_audio and tts_audio.exists():
        # Replace original audio with TTS, keeping original at low volume for ambience
        cmd_audio = [
            "ffmpeg", "-y",
            "-i", str(merged_path),
            "-i", str(tts_audio),
            "-filter_complex",
            f"[0:a]volume=0.15[orig];[1:a]volume=1.0[tts];[orig][tts]amix=inputs=2:duration=shortest:dropout_transition=0[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(final_path),
        ]
        log.info(f"[Mode2] Mixing TTS narration with ambient audio")
        r = subprocess.run(cmd_audio, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            log.warning(f"[Mode2] Audio mix failed — using TTS only")
            cmd_audio2 = [
                "ffmpeg", "-y",
                "-i", str(merged_path),
                "-i", str(tts_audio),
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                "-movflags", "+faststart",
                str(final_path),
            ]
            r2 = subprocess.run(cmd_audio2, capture_output=True, text=True, timeout=120)
            if r2.returncode != 0:
                shutil.copy(merged_path, final_path)
    else:
        shutil.copy(merged_path, final_path)
    
    # ── Step 5: Add SFX ──
    if sfx_enabled:
        sfx_output = out_dir / "with_sfx.mp4"
        all_sfx = []
        time_offset = 0
        
        for seg_idx, seg in enumerate(segments):
            for sfx in seg.get("sfx", []):
                all_sfx.append({
                    "type": sfx.get("type", "whoosh"),
                    "time": time_offset + sfx.get("time_offset", 0),
                })
            time_offset += seg.get("duration_estimate", 10)
        
        if all_sfx:
            sfx_path = _generate_sfx_track(all_sfx, total_duration, out_dir)
            if sfx_path and sfx_path.exists():
                cmd_sfx = [
                    "ffmpeg", "-y",
                    "-i", str(final_path),
                    "-i", str(sfx_path),
                    "-filter_complex",
                    f"[0:a]volume=1.0[a0];[1:a]volume=0.3[a1];[a0][a1]amix=inputs=2:duration=first:dropout_transition=0[aout]",
                    "-map", "0:v",
                    "-map", "[aout]",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-movflags", "+faststart",
                    str(sfx_output),
                ]
                r = subprocess.run(cmd_sfx, capture_output=True, text=True, timeout=120)
                if r.returncode == 0:
                    shutil.copy(sfx_output, final_path)
    
    # ── Step 6: Generate thumbnail ──
    thumbnail_path = _generate_thumbnail(final_path, production_plan, out_dir)
    
    # ── Step 7: Cleanup temp files ──
    for seg in segment_outputs:
        seg.unlink(missing_ok=True)
    concat_file.unlink(missing_ok=True)
    merged_path.unlink(missing_ok=True)
    if "sfx_output" in locals() and sfx_output.exists():
        sfx_output.unlink(missing_ok=True)
    
    # ── Metadata ──
    metadata = {
        "title": production_plan.get("title", f"{keyword} compilation"),
        "hashtags": production_plan.get("hashtags", []),
        "description": production_plan.get("description", ""),
        "bgm_mood": production_plan.get("bgm_mood", "energetic"),
        "total_duration": total_duration,
        "sources_used": len(set(m.get("video_idx", 0) for m in moments)),
        "keyword": keyword,
    }
    
    log.info(f"[Mode2] ✅ Compilation complete: {final_path.name} ({total_duration:.1f}s)")
    return {"output_path": final_path, "thumbnail_path": thumbnail_path, "metadata": metadata}


def _get_zoom_filter_pro(style: str, duration: float, w: int, h: int) -> str:
    """Get professional zoom filter for FFmpeg."""
    if style == "subtle":
        return f"zoompan=z='min(zoom+0.0008,1.15)':d={int(duration*30)}:s={w}x{h}"
    elif style == "slow_push":
        return f"zoompan=z='min(zoom+0.0015,1.25)':d={int(duration*30)}:s={w}x{h}"
    elif style == "punch":
        # Quick zoom in at start, hold
        return f"zoompan=z='if(lt(in_time,1),1+in_time*0.3,1.3)':d={int(duration*30)}:s={w}x{h}"
    elif style == "ken_burns":
        return f"zoompan=z='min(zoom+0.001,1.2)':x='iw/2+(iw/2)*sin(in_time/2)':y='ih/2+(ih/2)*cos(in_time/3)':d={int(duration*30)}:s={w}x{h}"
    elif style == "oscillate":
        return f"zoompan=z='1.1+0.05*sin(in_time*2)':d={int(duration*30)}:s={w}x{h}"
    elif style == "breath":
        return f"zoompan=z='1.05+0.03*sin(in_time*0.5)':d={int(duration*30)}:s={w}x{h}"
    return ""


def _generate_sfx_track(sfx_points: List[Dict], total_duration: float, out_dir: Path) -> Optional[Path]:
    """Generate a SFX audio track from procedural sound effects."""
    sfx_path = out_dir / "sfx_track.wav"
    
    SFX_CONFIG = {
        "whoosh": {"freq": 200, "dur": 0.3, "vol": 0.3},
        "impact": {"freq": 80, "dur": 0.15, "vol": 0.5},
        "ding": {"freq": 1200, "dur": 0.2, "vol": 0.25},
        "pop": {"freq": 400, "dur": 0.08, "vol": 0.3},
        "riser": {"freq": 100, "dur": 0.5, "vol": 0.2},
    }
    
    cmd = ["ffmpeg", "-y"]
    for i, sfx in enumerate(sfx_points):
        sfx_type = sfx.get("type", "whoosh")
        config = SFX_CONFIG.get(sfx_type, SFX_CONFIG["whoosh"])
        cmd.extend(["-f", "lavfi", "-i", f"sine=frequency={config['freq']}:duration={config['dur']}"])
    
    # Silent base
    cmd.extend(["-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={total_duration}"])
    
    fc_parts = []
    mix_parts = []
    base_idx = len(sfx_points)
    
    for i, sfx in enumerate(sfx_points):
        sfx_type = sfx.get("type", "whoosh")
        config = SFX_CONFIG.get(sfx_type, SFX_CONFIG["whoosh"])
        time = sfx.get("time", 0)
        fc_parts.append(f"[{i}:a]volume={config['vol']},adelay={int(time*1000)}|{int(time*1000)}[s{i}]")
        mix_parts.append(f"[s{i}]")
    
    fc_parts.append(f"[{base_idx}:a]volume=1.0[base]")
    mix_parts.append("[base]")
    
    fc = ";".join(fc_parts) + f";{''.join(mix_parts)}amix=inputs={len(mix_parts)}:duration=longest[aout]"
    
    cmd.extend(["-filter_complex", fc, "-map", "[aout]", "-c:a", "pcm_s16le", str(sfx_path)])
    
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        log.warning(f"[Mode2] SFX track generation failed: {r.stderr[-200:]}")
        return None
    return sfx_path


def _generate_thumbnail(video_path: Path, plan: Dict, out_dir: Path) -> Optional[Path]:
    """Generate an eye-catching thumbnail from the video.
    
    Picks a frame from the most dramatic moment and adds styled text overlay.
    """
    thumb_path = out_dir / "thumbnail.jpg"
    thumb_plan = plan.get("thumbnail", {})
    
    # Get video duration
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
            capture_output=True, text=True, timeout=10
        )
        duration = float(r.stdout.strip()) if r.returncode == 0 else 10
    except Exception:
        duration = 10
    
    # Pick the moment_index for thumbnail
    moment_idx = thumb_plan.get("moment_index", 0)
    segments = plan.get("segments", [])
    
    # Calculate timestamp: sum of previous segment durations + 1 second in
    timestamp = 1.0
    for i in range(min(moment_idx, len(segments))):
        timestamp += segments[i].get("duration_estimate", 10)
    timestamp = min(timestamp, duration - 1)
    
    # Extract frame
    frame_path = out_dir / "thumb_frame.jpg"
    cmd_frame = [
        "ffmpeg", "-y",
        "-ss", str(timestamp),
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "2",
        str(frame_path),
    ]
    r = subprocess.run(cmd_frame, capture_output=True, text=True, timeout=30)
    
    if not frame_path.exists():
        log.warning("[Mode2] Thumbnail frame extraction failed")
        return None
    
    # Add styled text overlay to thumbnail
    overlay_text = thumb_plan.get("overlay_text", "")
    style = thumb_plan.get("style", "energetic")
    
    if overlay_text:
        safe_text = overlay_text.replace(":", "\\:").replace("'", "\\'").replace("%", "\\%")
        
        # Style-specific colors
        if style == "dramatic":
            colors = "fontcolor=white:borderw=6:bordercolor=red@0.9"
        elif style == "mysterious":
            colors = "fontcolor=yellow:borderw=5:bordercolor=black@0.95"
        elif style == "energetic":
            colors = "fontcolor=white:borderw=5:bordercolor=orange@0.9"
        else:
            colors = "fontcolor=white:borderw=5:bordercolor=black@0.9"
        
        cmd_overlay = [
            "ffmpeg", "-y",
            "-i", str(frame_path),
            "-vf",
            f"drawtext=text='{safe_text}'"
            f":fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            f":fontsize=120"
            f":{colors}"
            f":x=(w-text_w)/2"
            f":y=h*0.35",
            "-q:v", "2",
            str(thumb_path),
        ]
        r = subprocess.run(cmd_overlay, capture_output=True, text=True, timeout=30)
        
        if r.returncode == 0 and thumb_path.exists():
            frame_path.unlink(missing_ok=True)
            log.info(f"[Mode2] Thumbnail generated: {thumb_path.name}")
            return thumb_path
    
    # Fallback: just use the frame
    shutil.copy(frame_path, thumb_path)
    frame_path.unlink(missing_ok=True)
    return thumb_path
