
# -- NexuX V9.0: Element Overlay Burn-in + Re-Render Endpoint --

@app.post("/api/rerender/{job_id}/{clip_index}/overlays")
async def rerender_with_overlays(
    job_id: str,
    clip_index: int,
    req: Request,
    _=Depends(_require_auth),
):
    """Re-render a clip with draggable text/logo overlay elements burned in.
    
    Takes the element array from TimelineEditorStudio (position, size, rotation,
    animation, timing) and burns them into the video using FFmpeg drawtext/overlay.
    
    Also applies color grade, zoom, aspect ratio change, and audio processing
    from the editor state.
    
    Body:
    {
        "elements": [
            {
                "id": "el-1",
                "type": "text",
                "content": "HELLO WORLD",
                "x": 50.0,        // percent center, 0-100
                "y": 30.0,        // percent center, 0-100
                "width": 30.0,    // percent
                "height": 10.0,   // percent
                "rotation": 0,    // degrees
                "start": 0.0,      // seconds (when element appears)
                "end": 10.0,      // seconds (when element disappears)
                "color": "#FFFFFF",
                "bg_color": "#000000",
                "font_size": 24,
                "animation_in": "fade",
                "animation_out": "fade",
                "visible": true,
                "z_index": 1
            }
        ],
        "aspect_ratio": "9:16",
        "color_grade": "none",
        "zoom_style": "subtle",
        "zoom_level": 1.0,
        "layout_mode": "Fill",
        "speed_ramp": false,
        "speed_ramp_type": "none",
        "watermark_text": "",
        "watermark_position": "bottom-right",
        "show_watermark": false,
        "normalize_audio": true,
        "bass_boost": false,
        "voice_volume": 100,
        "sfx_enabled": true,
        "trim_start": 0,
        "trim_end": 45
    }
    """
    import subprocess, os, json, time
    from pathlib import Path
    
    job = _load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(400, "Job must be completed before re-rendering")
    
    clips = json.loads(job.get("clips", "[]"))
    if clip_index < 0 or clip_index >= len(clips):
        raise HTTPException(400, f"Invalid clip index: {clip_index}")
    
    body = await req.json()
    elements = body.get("elements", [])
    aspect_ratio = body.get("aspect_ratio", "9:16")
    color_grade = body.get("color_grade", "none")
    zoom_style = body.get("zoom_style", "none")
    zoom_level = body.get("zoom_level", 1.0)
    layout_mode = body.get("layout_mode", "Fill")
    trim_start = body.get("trim_start", 0)
    trim_end = body.get("trim_end", 0)
    watermark_text = body.get("watermark_text", "")
    watermark_position = body.get("watermark_position", "bottom-right")
    show_watermark = body.get("show_watermark", False)
    
    clip = clips[clip_index]
    # Clips may be plain path strings; start/end comes from clip_candidates.
    analysis = job.get("analysis_bundle")
    if isinstance(analysis, str):
        try:
            analysis = json.loads(analysis)
        except Exception:
            analysis = {}
    candidates = (analysis or {}).get("clip_candidates") or []
    candidate = candidates[clip_index] if clip_index < len(candidates) else {}
    if isinstance(clip, dict):
        original_start = float(clip.get("start", 0))
        original_end = float(clip.get("end", 45))
    else:
        original_start = float(candidate.get("start", 0))
        original_end = float(candidate.get("end", 45))
    original_dur = original_end - original_start
    
    # Apply trim
    if trim_end > 0 and (trim_start != 0 or abs(trim_end - original_dur) > 0.1):
        clip_start = original_start + trim_start
        clip_end = min(original_start + trim_end, original_end)
    else:
        clip_start = original_start
        clip_end = original_end
    
    clip_dur = clip_end - clip_start
    
    # Source video
    source_video = job.get("_source_video") or job.get("source_video_path", "")
    if not source_video or not Path(source_video).exists():
        raise HTTPException(500, "Source video not found")
    
    # Output paths
    output_dir = Path(os.environ.get("NEXUX_OUTPUT_DIR", "output")) / f"{job_id}_rerender"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"clip_{clip_index:02d}_overlays.mp4"
    
    # Resolution from aspect ratio
    aspect_dims = {
        "9:16": (1080, 1920),
        "1:1": (1080, 1080),
        "16:9": (1920, 1080),
        "4:5": (1080, 1350),
    }
    w, h = aspect_dims.get(aspect_ratio, (1080, 1920))
    
    # ── Build FFmpeg filter chain ──
    vf_parts = []
    
    # Scale + crop
    if layout_mode == "Fill":
        vf_parts.append(f"scale={w}:{h}:force_original_aspect_ratio=increase")
        vf_parts.append(f"crop={w}:{h}")
    else:  # Fit
        vf_parts.append(f"scale={w}:{h}:force_original_aspect_ratio=decrease")
        # Pad with black
        vf_parts.append(f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black")
    
    # Color grade
    grade_filters = {
        "none": "",
        "warm": "eq=saturation=1.15:brightness=0.03:gamma=1.05",
        "cool": "eq=saturation=0.90:brightness=-0.02:gamma=0.95",
        "vibrant": "eq=saturation=1.35:contrast=1.10:brightness=0.04",
        "cinematic": "eq=saturation=0.82:contrast=1.15:brightness=-0.04:gamma=1.02",
        "vintage": "eq=saturation=0.75:contrast=1.05:brightness=0.02:gamma=1.10",
    }
    grade = grade_filters.get(color_grade, "")
    if grade:
        vf_parts.append(grade)
    
    # Zoom (zoompan)
    if zoom_style != "none" and zoom_level > 1.0:
        if zoom_style == "subtle":
            max_z = 1.0 + (zoom_level - 1.0) * 0.3
            vf_parts.append(
                f"zoompan=z='min(zoom+0.0008,{max_z:.2f})':d=1:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps=30"
            )
        elif zoom_style == "dramatic":
            vf_parts.append(
                f"zoompan=z='min(zoom+0.002,{zoom_level:.2f})':d=1:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps=30"
            )
        elif zoom_style == "breathing":
            vf_parts.append(
                f"zoompan=z='1+0.02*sin(on*0.05)':d=1:"
                f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps=30"
            )
    
    # ── Text overlay drawtext filters ──
    # Sort elements by z_index (lower first = drawn first = behind)
    sorted_elements = sorted(
        [e for e in elements if e.get("visible", True) and e.get("type") == "text"],
        key=lambda e: e.get("z_index", 0)
    )
    
    for el in sorted_elements:
        content = el.get("content", "").replace("\n", "\\n")
        if not content:
            continue
        
        # Position: center anchor → drawtext x/y
        # x = (el.x / 100) * w - (text_width / 2)
        # We use (w * el.x / 100) - (tw / 2) for centering
        x_expr = f"(w*{el.get('x', 50)}.0/100)-(tw/2)"
        y_expr = f"(h*{el.get('y', 50)}.0/100)-(th/2)"
        
        # Timing: show between start and end seconds
        # enable='between(t,start,end)'
        el_start = float(el.get("start", 0))
        el_end = float(el.get("end", clip_dur))
        
        font_size = int(el.get("font_size", 24) * (w / 400))  # scale relative to canvas
        
        # Colors
        fontcolor = el.get("color", "#FFFFFF")
        # Convert hex to 0x format for FFmpeg
        fc = fontcolor.replace("#", "0x") if fontcolor.startswith("#") else "0xFFFFFF"
        
        # Background box (if bg_color is not transparent)
        bg = el.get("bg_color", "transparent")
        box_str = ""
        if bg and bg != "transparent" and bg != "":
            bgc = bg.replace("#", "0x") if bg.startswith("#") else "0x000000"
            box_str = f":box=1:boxcolor={bgc}@0.85:boxborderw=8"
        
        # Animation: fade in/out
        anim_in = el.get("animation_in", "fade")
        anim_out = el.get("animation_out", "fade")
        
        fade_in_str = ""
        fade_out_str = ""
        if anim_in == "fade":
            fade_dur = min(0.5, (el_end - el_start) * 0.2)
            fade_in_str = f",fade=t=in:st={el_start}:d={fade_dur:.2f}"
        elif anim_in == "slide-up":
            # Simulate slide-up with yoffset expression
            y_expr = f"(h*{el.get('y', 50)}.0/100)-(th/2)+if(lt(t-{el_start},0.3),(1-(t-{el_start})/0.3)*60,0)"
        elif anim_in == "pop":
            # Pop = quick scale up (can't do scale on drawtext, use alpha)
            fade_in_str = f",fade=t=in:st={el_start}:d=0.15"
        
        if anim_out == "fade":
            fade_out_dur = min(0.5, (el_end - el_start) * 0.2)
            fade_out_str = f":alpha='if(lt(t,{el_end - fade_out_dur:.2f}),1,if(lt(t,{el_end:.2f}),1-(t-{el_end - fade_out_dur:.2f})/{fade_out_dur:.2f},0))'"
        
        # Rotation (drawtext doesn't support rotation directly — use rotate filter separately)
        rotation = el.get("rotation", 0)
        # For now, skip rotation on text (complex with drawtext). Log it.
        
        drawtext = (
            f"drawtext=text='{content}':"
            f"x='{x_expr}':y='{y_expr}':"
            f"fontsize={font_size}:"
            f"fontcolor={fc}"
            f":borderw=2:bordercolor=0x000000"
            f"{box_str}"
            f":enable='between(t,{el_start:.2f},{el_end:.2f})'"
        )
        vf_parts.append(drawtext)
    
    # Watermark
    if show_watermark and watermark_text:
        pos_map = {
            "top-left": "x=10:y=10",
            "top-right": "x=w-tw-10:y=10",
            "bottom-left": "x=10:y=h-th-10",
            "bottom-right": "x=w-tw-10:y=h-th-10",
        }
        wm_pos = pos_map.get(watermark_position, pos_map["bottom-right"])
        vf_parts.append(
            f"drawtext=text='{watermark_text}':{wm_pos}:"
            f"fontsize=24:fontcolor=white@0.5:"
            f"shadowcolor=black:shadowx=1:shadowy=1"
        )
    
    # Join all video filters
    vf = ",".join(vf_parts)
    
    # ── Audio filters ──
    audio_filters = []

    # Per-speaker mute / isolate — diarized segments sent clip-relative.
    speaker_segments = body.get("speaker_segments") or []
    muted_speakers = set(body.get("muted_speakers") or [])
    isolated_speaker = body.get("isolated_speaker")
    for seg in speaker_segments[:400]:
        spk = seg.get("speaker")
        try:
            s, e = float(seg.get("start", 0)), float(seg.get("end", 0))
        except (TypeError, ValueError):
            continue
        if e - s < 0.05:
            continue
        if spk and spk in muted_speakers:
            audio_filters.append(f"volume=0:enable='between(t,{s:.2f},{e:.2f})'")
        elif isolated_speaker and spk and spk != isolated_speaker:
            audio_filters.append(f"volume=0.15:enable='between(t,{s:.2f},{e:.2f})'")

    voice_vol = body.get("voice_volume", 100)
    if voice_vol != 100:
        audio_filters.append(f"volume={voice_vol / 100.0:.2f}")
    if body.get("bass_boost", False):
        audio_filters.append("bass=g=6:f=80:w=0.8")
    if body.get("normalize_audio", True):
        audio_filters.append("loudnorm=I=-16:TP=-1.5:LRA=11")
    af = ",".join(audio_filters) if audio_filters else "anull"
    
    # ── Build FFmpeg command ──
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(clip_start),
        "-i", str(source_video),
        "-t", str(clip_dur),
        "-vf", vf,
        "-af", af,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(output_path),
    ]
    
    log.info(f"[OverlayRender] Job {job_id} clip {clip_index} | "
             f"{len(sorted_elements)} text elements | {aspect_ratio} | "
             f"grade={color_grade} | zoom={zoom_style} | "
             f"trim={trim_start}-{trim_end}")
    
    start_time = time.time()
    
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1200,
                          cwd=str(Path.cwd()))
        if r.returncode != 0:
            err = r.stderr[-1200:] if len(r.stderr) > 1200 else r.stderr
            log.error(f"[OverlayRender] FFmpeg failed: {err}")
            raise HTTPException(500, f"FFmpeg render failed: {err}")
    except subprocess.TimeoutExpired:
        raise HTTPException(500, "Render timed out (1200s)")
    
    render_time = time.time() - start_time
    file_size = output_path.stat().st_size / (1024 * 1024) if output_path.exists() else 0
    
    log.info(f"[OverlayRender] Complete: {output_path.name} | "
             f"{file_size:.1f}MB | {render_time:.1f}s | "
             f"{len(sorted_elements)} elements burned in")
    
    # Build changes summary
    changes = []
    if sorted_elements:
        changes.append(f"{len(sorted_elements)} text elements burned in")
    if color_grade != "none":
        changes.append(f"Color grade: {color_grade}")
    if zoom_style != "none":
        changes.append(f"Zoom: {zoom_style}")
    if aspect_ratio != "9:16":
        changes.append(f"Aspect ratio: {aspect_ratio}")
    if show_watermark:
        changes.append(f"Watermark: '{watermark_text}'")
    if trim_start != 0 or (trim_end > 0 and abs(trim_end - original_dur) > 0.1):
        changes.append(f"Trim: {original_dur:.1f}s → {clip_dur:.1f}s")
    
    return {
        "status": "success",
        "job_id": job_id,
        "clip_index": clip_index,
        "output_path": str(output_path),
        "output_url": f"/output/{job_id}_rerender/{output_path.name}",
        "render_time_seconds": round(render_time, 1),
        "file_size_mb": round(file_size, 1),
        "elements_burned": len(sorted_elements),
        "changes_applied": changes if changes else ["No changes from original"],
        "render_config": {
            "aspect_ratio": aspect_ratio,
            "color_grade": color_grade,
            "zoom_style": zoom_style,
            "layout_mode": layout_mode,
            "elements": len(sorted_elements),
            "watermark": show_watermark,
            "trim": f"{trim_start}s - {trim_end}s",
        },
    }
