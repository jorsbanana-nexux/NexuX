
# -- NexuX V8.5: Hook Detection & Auto-Reframe API --

@app.get("/api/hooks/{job_id}")
async def get_hook_analysis(job_id: str, _=Depends(_require_auth)):
    """Get hook detection analysis for all clips in a job.
    
    Analyzes the first 3 seconds of each clip and finds the best
    possible hook (opening line). Can recommend shifting clip start
    to capture a stronger hook.
    
    Returns per clip:
    - best_start: optimal clip start time
    - hook_score: 0-100 hook strength
    - hook_archetype: which hook type was detected
    - should_shift: whether to shift clip start
    - alternatives: other candidate hooks
    """
    job = _load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    clips = json.loads(job.get("clips", "[]"))
    analysis_bundle = json.loads(job.get("analysis_bundle", "null") or "null")
    
    if not clips:
        raise HTTPException(400, "No clips found for this job")
    
    from engine.hook_detection import detect_best_hook, hook_to_api_dict
    
    full_segments = (analysis_bundle or {}).get("segments", [])
    
    hooks = []
    for i, clip in enumerate(clips):
        hook = detect_best_hook(
            segments=full_segments,
            clip_start=clip["start"],
            clip_end=clip["end"],
            max_shift=5.0,
        )
        hooks.append({
            "clip_index": i,
            "original_start": clip["start"],
            **hook_to_api_dict(hook),
        })
    
    # Sort by hook score
    hooks.sort(key=lambda h: h["hook_score"], reverse=True)
    
    shifted = sum(1 for h in hooks if h.get("should_shift", False))
    avg_score = sum(h["hook_score"] for h in hooks) / max(len(hooks), 1)
    
    return {
        "job_id": job_id,
        "total_clips": len(hooks),
        "hooks": hooks,
        "best_hook": hooks[0] if hooks else None,
        "average_hook_score": round(avg_score, 1),
        "clips_needing_shift": shifted,
    }


@app.post("/api/hooks/optimize/{job_id}")
async def optimize_hooks(job_id: str, _=Depends(_require_auth)):
    """Re-optimize clip start times based on hook detection.
    
    Shifts clip start times to capture the best possible hook for each clip.
    Updates the job's clips in the database.
    """
    job = _load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    clips = json.loads(job.get("clips", "[]"))
    analysis_bundle = json.loads(job.get("analysis_bundle", "null") or "null")
    
    if not clips:
        raise HTTPException(400, "No clips found for this job")
    
    from engine.hook_detection import detect_best_hook
    
    full_segments = (analysis_bundle or {}).get("segments", [])
    
    optimized_clips = []
    shifts = []
    
    for i, clip in enumerate(clips):
        hook = detect_best_hook(
            segments=full_segments,
            clip_start=clip["start"],
            clip_end=clip["end"],
            max_shift=5.0,
        )
        
        if hook.should_shift and abs(hook.shift_amount) > 0.5:
            new_start = hook.best_start
            # Keep clip duration the same
            clip_dur = clip["end"] - clip["start"]
            new_end = new_start + clip_dur
            
            optimized_clip = clip.copy()
            optimized_clip["start"] = round(new_start, 2)
            optimized_clip["end"] = round(new_end, 2)
            optimized_clip["hook_optimized"] = True
            optimized_clip["hook_archetype"] = hook.hook_archetype
            optimized_clip["hook_score"] = round(hook.hook_score, 1)
            optimized_clips.append(optimized_clip)
            
            shifts.append({
                "clip_index": i,
                "old_start": clip["start"],
                "new_start": round(new_start, 2),
                "shift": round(hook.shift_amount, 2),
                "hook_score": round(hook.hook_score, 1),
                "hook_archetype": hook.hook_archetype,
            })
        else:
            optimized_clips.append(clip)
    
    # Update job in database
    job["clips"] = optimized_clips
    _save_job(job)
    
    return {
        "status": "success",
        "job_id": job_id,
        "clips_optimized": len(shifts),
        "total_clips": len(clips),
        "shifts": shifts,
    }


@app.get("/api/reframe/{job_id}")
async def get_reframe_analysis(
    job_id: str,
    target_width: int = 1080,
    target_height: int = 1920,
    _=Depends(_require_auth),
):
    """Get auto-reframe (face tracking) analysis for all clips in a job.
    
    Generates face-tracking crop instructions that keep the active
    speaker in frame when converting to vertical video.
    
    Query params:
    - target_width: Target video width (default 1080)
    - target_height: Target video height (default 1920)
    """
    job = _load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    clips = json.loads(job.get("clips", "[]"))
    
    if not clips:
        raise HTTPException(400, "No clips found for this job")
    
    from engine.reframe_engine import auto_reframe, reframe_to_api_dict
    
    # Load face tracking data
    import os
    face_data_path = Path(os.environ.get("NEXUX_OUTPUT_DIR", "output")) / job_id / "face_tracking.json"
    
    face_data = []
    if face_data_path.exists():
        try:
            face_data = json.loads(face_data_path.read_text())
        except Exception as e:
            log.warning(f"Failed to load face data: {e}")
    
    # Source video dimensions (would come from video info in production)
    source_width = 1920
    source_height = 1080
    
    results = []
    for i, clip in enumerate(clips):
        reframe = auto_reframe(
            face_data=face_data,
            source_width=source_width,
            source_height=source_height,
            target_width=target_width,
            target_height=target_height,
            clip_start=clip["start"],
            clip_end=clip["end"],
        )
        
        results.append({
            "clip_index": i,
            "clip_start": clip["start"],
            "clip_end": clip["end"],
            **reframe_to_api_dict(reframe),
            "ffmpeg_filter": reframe.ffmpeg_filter[:200] + "..." if len(reframe.ffmpeg_filter) > 200 else reframe.ffmpeg_filter,
        })
    
    return {
        "job_id": job_id,
        "target_resolution": f"{target_width}x{target_height}",
        "total_clips": len(results),
        "results": results,
    }
