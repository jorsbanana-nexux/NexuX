
# -- NexuX V8.5: Multi-Platform Auto-Posting & Analytics API --

@app.get("/api/platforms")
async def list_supported_platforms(_=Depends(_require_auth)):
    """List all supported social media platforms with their specs."""
    from engine.autopost_engine import list_platforms
    return {"platforms": list_platforms()}


@app.post("/api/autopost/{job_id}")
async def auto_post_clips(
    job_id: str,
    req: Request,
    _=Depends(_require_auth),
):
    """Auto-post clips to multiple platforms simultaneously.
    
    Body:
    {
        "platforms": ["tiktok", "youtube_shorts", "instagram_reels"],
        "clip_index": 0,           // Which clip to post (optional, default: best)
        "title": "Custom title",    // Optional
        "description": "...",        // Optional
        "hashtags": ["viral"],      // Optional
        "schedule_time": "...",     // Optional ISO datetime
        "auto_fix": true             // Auto-fix video issues
    }
    """
    job = _load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    if job["status"] != "completed":
        raise HTTPException(400, "Job is not completed yet")
    
    from engine.autopost_engine import (
        post_to_all_platforms, results_to_api_dict,
        optimize_metadata_for_platform, PLATFORM_SPECS,
    )
    from engine.virality_score import score_to_api_dict, score_clip_virality
    
    body = await req.json()
    platforms = body.get("platforms", ["tiktok", "youtube_shorts"])
    clip_index = body.get("clip_index", 0)
    auto_fix = body.get("auto_fix", True)
    
    clips = json.loads(job.get("clips", "[]"))
    if not clips:
        raise HTTPException(400, "No clips found")
    
    clip = clips[clip_index] if clip_index < len(clips) else clips[0]
    
    # Get clip output path
    output_path = clip.get("output_path") or clip.get("path")
    if not output_path:
        raise HTTPException(400, "Clip has no output file")
    
    video_path = Path(output_path)
    if not video_path.exists():
        raise HTTPException(404, f"Video file not found: {video_path}")
    
    # Get credentials from environment or request
    credentials = {}
    for p in platforms:
        token_env = f"{p.upper().replace('-', '_')}_ACCESS_TOKEN"
        token = os.environ.get(token_env, "")
        if token:
            credentials[p] = {"access_token": token}
    
    # Generate virality score for metadata optimization
    analysis_bundle = json.loads(job.get("analysis_bundle", "null") or "null")
    full_segments = (analysis_bundle or {}).get("segments", [])
    clip_segs = [s for s in full_segments if s.get("start", 0) < clip["end"] and s.get("end", 0) > clip["start"]]
    
    v_score = score_clip_virality(
        clip=clip, transcript=clip_segs, full_segments=full_segments,
        clip_duration=clip["end"] - clip["start"],
        style_name=json.loads(job.get("request_data", "{}")).get("subtitle_style", "hormozi"),
    )
    
    # Base metadata
    base_title = body.get("title", "")
    base_description = body.get("description", "")
    base_hashtags = body.get("hashtags", [])
    
    if not base_title:
        # Auto-generate from clip text
        if clip_segs:
            base_title = clip_segs[0].get("text", "")[:80]
    
    if not base_hashtags:
        base_hashtags = ["viral", "shorts", "fyp"]
    
    results = post_to_all_platforms(
        video_path=video_path,
        title=base_title,
        description=base_description,
        hashtags=base_hashtags,
        platforms=platforms,
        credentials=credentials,
        virality_score=score_to_api_dict(v_score),
        auto_fix=auto_fix,
    )
    
    return {
        "status": "success",
        "job_id": job_id,
        "clip_index": clip_index,
        "results": results_to_api_dict(results),
    }


@app.get("/api/analytics/v2/{job_id}")
async def get_advanced_analytics(job_id: str, _=Depends(_require_auth)):
    """Get cross-platform analytics for a job.
    
    Returns:
    - Per-clip performance across all platforms
    - Virality prediction accuracy (predicted vs actual views)
    - Platform breakdown (which platform performs best)
    - Hook archetype performance
    - Engagement rates and insights
    - Performance predictions for future clips
    """
    job = _load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    clips = json.loads(job.get("clips", "[]"))
    analysis_bundle = json.loads(job.get("analysis_bundle", "null") or "null")
    
    from engine.analytics_engine import (
        analyze_clip_performance, analyze_job_performance,
        clip_analytics_to_api_dict, job_analytics_to_api_dict,
        ClipMetrics,
    )
    from engine.virality_score import score_to_api_dict, score_clip_virality
    
    full_segments = (analysis_bundle or {}).get("segments", [])
    style_name = json.loads(job.get("request_data", "{}")).get("subtitle_style", "hormozi")
    
    # Check for stored post IDs (from auto-posting)
    post_data = json.loads(job.get("publish_plan", "{}") or "{}")
    
    clip_analytics_list = []
    
    for i, clip in enumerate(clips):
        clip_segs = [s for s in full_segments if s.get("start", 0) < clip["end"] and s.get("end", 0) > clip["start"]]
        
        # Get virality score
        v_score = score_clip_virality(
            clip=clip, transcript=clip_segs, full_segments=full_segments,
            clip_duration=clip["end"] - clip["start"], style_name=style_name,
        )
        
        # Check if clip was posted (would have metrics from platform APIs)
        platform_metrics = {}
        post_ids = post_data.get("clips", {}).get(str(i), {}).get("post_ids", {})
        
        for platform, post_id in post_ids.items():
            # In production, fetch real metrics from platform APIs
            # For now, use stored/simulated metrics if available
            metrics = ClipMetrics(clip_id=post_id, platform=platform)
            platform_metrics[platform] = metrics
        
        # Analyze clip performance
        ca = analyze_clip_performance(
            clip_id=f"{job_id}_clip_{i}",
            job_id=job_id,
            virality_score=score_to_api_dict(v_score),
            platform_metrics=platform_metrics,
            clip_meta=clip,
        )
        clip_analytics_list.append(ca)
    
    # Analyze job performance
    job_analytics = analyze_job_performance(job_id, clip_analytics_list)
    
    return job_analytics_to_api_dict(job_analytics)


@app.post("/api/analytics/collect/{job_id}")
async def collect_analytics(job_id: str, req: Request, _=Depends(_require_auth)):
    """Collect fresh metrics from all platforms for a job's posted clips.
    
    Body:
    {
        "platforms": {
            "tiktok": {"post_id": "...", "access_token": "..."},
            "youtube_shorts": {"post_id": "...", "access_token": "..."}
        }
    }
    """
    from engine.analytics_engine import collect_clip_metrics, clip_analytics_to_api_dict
    
    body = await req.json()
    platforms_data = body.get("platforms", {})
    
    results = {}
    for platform, data in platforms_data.items():
        post_id = data.get("post_id", "")
        creds = {"access_token": data.get("access_token", "")}
        
        if post_id:
            metrics = collect_clip_metrics(platform, post_id, creds)
            results[platform] = clip_analytics_to_api_dict.__wrapped__(metrics) if hasattr(clip_analytics_to_api_dict, '__wrapped__') else {
                "platform": platform,
                "post_id": post_id,
                "views": metrics.views,
                "likes": metrics.likes,
                "comments": metrics.comments,
                "shares": metrics.shares,
                "saves": metrics.saves,
                "fetched_at": metrics.fetched_at,
            }
    
    return {
        "status": "success",
        "job_id": job_id,
        "platforms": results,
    }
