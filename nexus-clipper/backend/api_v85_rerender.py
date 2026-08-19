
# -- NexuX V8.5: Re-render Endpoint for Personalization Editor --

@app.post("/api/rerender/{job_id}/{clip_index}")
async def rerender_clip(
    job_id: str,
    clip_index: int,
    req: Request,
    _=Depends(_require_auth),
):
    """Re-render a specific clip with personalization settings from ClipEditorStudio.
    
    Takes the editor state from the frontend and re-renders the clip with
    new subtitle style, effects, color grade, zoom, audio, layout, branding, and trim.
    
    Body: EditorState from ClipEditorStudio (all personalization settings)
    
    Returns:
    - status: "success" | "processing" | "error"
    - output_path: Path to re-rendered clip
    - changes_applied: List of changes made
    - render_time_seconds: Time taken
    """
    job = _load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(400, "Job must be completed before re-rendering")
    
    clips = json.loads(job.get("clips", "[]"))
    if clip_index < 0 or clip_index >= len(clips):
        raise HTTPException(400, f"Invalid clip index: {clip_index}")
    
    body = await req.json()
    
    from engine.rerender_pipeline import rerender_clip_with_personalization
    
    # Get source video path
    source_video = job.get("_source_video") or job.get("source_video_path", "")
    source_video_path = Path(source_video) if source_video else None
    
    # Get transcript / analysis bundle
    analysis_bundle = json.loads(job.get("analysis_bundle", "null") or "null")
    transcript = analysis_bundle if analysis_bundle else {"segments": []}
    
    # Get face tracking data
    face_data = []
    face_data_path = Path(os.environ.get("NEXUX_OUTPUT_DIR", "output")) / job_id / "face_tracking.json"
    if face_data_path.exists():
        try:
            face_data = json.loads(face_data_path.read_text())
        except Exception:
            pass
    
    log.info(f"[ReRender] Job {job_id} clip {clip_index} | "
             f"style={body.get('subtitle_style', 'hormozi')} | "
             f"grade={body.get('color_grade', 'none')} | "
             f"zoom={body.get('zoom_style', 'subtle')} | "
             f"aspect={body.get('aspect_ratio', '9:16')}")
    
    # Run the re-render pipeline
    result = rerender_clip_with_personalization(
        job_data=job,
        clip_index=clip_index,
        editor_state=body,
        source_video_path=source_video_path,
        transcript=transcript,
        face_data=face_data if face_data else None,
        use_pro=True,
    )
    
    if result["status"] == "error":
        raise HTTPException(500, result.get("error", "Re-render failed"))
    
    return result


@app.post("/api/rerender/{job_id}/all")
async def rerender_all(
    job_id: str,
    req: Request,
    _=Depends(_require_auth),
):
    """Re-render ALL clips in a job with the same personalization settings.
    
    Used when user clicks "Apply to All" in the editor.
    """
    job = _load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(400, "Job must be completed before re-rendering")
    
    body = await req.json()
    
    from engine.rerender_pipeline import rerender_all_clips
    
    source_video = job.get("_source_video") or job.get("source_video_path", "")
    source_video_path = Path(source_video) if source_video else None
    
    analysis_bundle = json.loads(job.get("analysis_bundle", "null") or "null")
    transcript = analysis_bundle if analysis_bundle else {"segments": []}
    
    face_data = []
    face_data_path = Path(os.environ.get("NEXUX_OUTPUT_DIR", "output")) / job_id / "face_tracking.json"
    if face_data_path.exists():
        try:
            face_data = json.loads(face_data_path.read_text())
        except Exception:
            pass
    
    results = rerender_all_clips(
        job_data=job,
        editor_state=body,
        source_video_path=source_video_path,
        transcript=transcript,
        face_data=face_data if face_data else None,
    )
    
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")
    
    return {
        "status": "success" if error_count == 0 else "partial",
        "job_id": job_id,
        "total_clips": len(results),
        "success_count": success_count,
        "error_count": error_count,
        "results": results,
    }
