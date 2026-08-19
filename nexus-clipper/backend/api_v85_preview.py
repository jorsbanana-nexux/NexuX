
# -- NexuX V9.0: Real-Time FFmpeg Preview API --

@app.post("/api/preview-render/{job_id}/{clip_index}")
async def preview_render(
    job_id: str,
    clip_index: int,
    req: Request,
    _=Depends(_require_auth),
):
    """Generate a 480p preview clip with overlays burned in.
    
    Renders a 5-second segment around the current playhead position.
    Target render time: <3 seconds.
    """
    job = _load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    body = await req.json()
    
    from engine.preview_renderer import generate_preview
    
    source_video = job.get("_source_video") or job.get("source_video_path", "")
    if not source_video or not Path(source_video).exists():
        raise HTTPException(500, "Source video not found")
    
    result = generate_preview(
        job_id=job_id,
        clip_index=clip_index,
        editor_state=body,
        source_video_path=Path(source_video),
        current_time=body.get("current_time", 0.0),
    )
    
    if not result.success:
        raise HTTPException(500, result.error or "Preview generation failed")
    
    return {
        "status": "success",
        "preview_url": result.output_url,
        "render_time": round(result.render_time, 2),
    }


@app.post("/api/preview-frame/{job_id}/{clip_index}")
async def preview_frame(
    job_id: str,
    clip_index: int,
    req: Request,
    _=Depends(_require_auth),
):
    """Generate a single PNG preview frame with overlays applied."""
    job = _load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    body = await req.json()
    timestamp = body.get("timestamp", 0.0)
    
    from engine.preview_renderer import generate_preview_frame
    
    source_video = job.get("_source_video") or job.get("source_video_path", "")
    if not source_video or not Path(source_video).exists():
        raise HTTPException(500, "Source video not found")
    
    result = generate_preview_frame(
        job_id=job_id,
        clip_index=clip_index,
        timestamp=timestamp,
        editor_state=body,
        source_video_path=Path(source_video),
    )
    
    if not result.success:
        raise HTTPException(500, result.error or "Preview frame generation failed")
    
    return {
        "status": "success",
        "frame_url": result.output_url,
        "render_time": round(result.render_time, 2),
    }
