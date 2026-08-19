
# -- NexuX V8.5: Virality Score & Caption Quality API --

@app.get("/api/virality/{job_id}")
async def get_virality_scores(job_id: str, _=Depends(_require_auth)):
    """Get virality scores for all clips in a job.
    
    Returns 0-100 scores with full breakdown on 8 dimensions:
    hook_power, retention_prediction, shareability, trend_alignment,
    emotional_impact, information_density, caption_virality, pacing_quality
    """
    job = _load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    clips = json.loads(job.get("clips", "[]"))
    analysis_bundle = json.loads(job.get("analysis_bundle", "null") or "null")
    
    if not clips:
        raise HTTPException(400, "No clips found for this job")
    
    from engine.virality_score import score_clip_virality, score_to_api_dict
    
    # Get transcript and segments from analysis
    transcript = analysis_bundle or {}
    full_segments = transcript.get("segments", [])
    full_duration = transcript.get("duration", 0)
    
    style_name = json.loads(job.get("request_data", "{}")).get("subtitle_style", "hormozi")
    
    scores = []
    for i, clip in enumerate(clips):
        clip_segs = [
            s for s in full_segments
            if s.get("start", 0) < clip["end"] and s.get("end", 0) > clip["start"]
        ]
        clip_dur = clip["end"] - clip["start"]
        
        # Generate hook text for this clip
        hook_text = None
        if clip_segs:
            first_text = clip_segs[0].get("text", "").strip()
            if len(first_text) > 60:
                cut = first_text[:60].rfind(" ")
                hook_text = first_text[:cut] + "..." if cut > 20 else first_text[:57] + "..."
            else:
                hook_text = first_text
            if i >= 2:
                hook_text = None
        
        score = score_clip_virality(
            clip=clip,
            transcript=clip_segs,
            full_segments=full_segments,
            clip_duration=clip_dur,
            hook_text=hook_text,
            style_name=style_name,
        )
        
        scores.append({
            "clip_index": i,
            "clip_start": clip["start"],
            "clip_end": clip["end"],
            "clip_duration": round(clip_dur, 1),
            **score_to_api_dict(score),
        })
    
    # Sort by composite score
    scores.sort(key=lambda x: x["composite"], reverse=True)
    
    return {
        "job_id": job_id,
        "total_clips": len(scores),
        "scores": scores,
        "best_clip": scores[0] if scores else None,
        "average_score": round(sum(s["composite"] for s in scores) / max(len(scores), 1), 1),
    }


@app.get("/api/caption-quality/{job_id}")
async def get_caption_quality(job_id: str, _=Depends(_require_auth)):
    """Get caption quality analysis for all clips in a job.
    
    Returns scores on: readability, animation_quality, emphasis_accuracy,
    timing_quality, visual_appeal (all 0-100)
    """
    job = _load_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    clips = json.loads(job.get("clips", "[]"))
    analysis_bundle = json.loads(job.get("analysis_bundle", "null") or "null")
    
    if not clips:
        raise HTTPException(400, "No clips found for this job")
    
    from engine.caption_engine_v2 import score_caption_quality
    from engine.subtitle_quality import process_subtitle_quality
    from engine.styles import resolve_style
    
    transcript = analysis_bundle or {}
    request_data = json.loads(job.get("request_data", "{}"))
    style_name = request_data.get("subtitle_style", "hormozi")
    style_config = resolve_style(style_name)
    
    results = []
    for i, clip in enumerate(clips):
        groups, quality_report = process_subtitle_quality(transcript, clip, style_config)
        
        caption_score = score_caption_quality(groups, style_config, style_name)
        
        results.append({
            "clip_index": i,
            "clip_start": clip["start"],
            "clip_end": clip["end"],
            **caption_score,
            "word_groups": len(groups),
        })
    
    avg_score = round(sum(r["score"] for r in results) / max(len(results), 1), 1)
    
    return {
        "job_id": job_id,
        "style": style_name,
        "total_clips": len(results),
        "results": results,
        "average_score": avg_score,
    }


@app.post("/api/generate-with-scoring")
async def generate_with_virality_scoring(req: Request, _=Depends(_require_auth)):
    """Generate clips AND return virality scores in one call.
    
    Like /api/generate but also runs virality scoring on each clip
    and returns the scores alongside the clips.
    """
    import uuid
    from engine.pipeline import run_pipeline
    from engine.virality_score import score_clip_virality, score_to_api_dict
    
    body = await req.json()
    url = body.get("youtube_url", "")
    if not url:
        raise HTTPException(400, "youtube_url is required")
    
    job_id = uuid.uuid4().hex[:12]
    request_data = {
        "youtube_url": url,
        "target_duration": body.get("target_duration", 45),
        "aspect_ratio": body.get("aspect_ratio", "9:16"),
        "subtitle_style": body.get("subtitle_style", "hormozi"),
        "max_clips": body.get("max_clips", 10),
        "whisper_model": body.get("whisper_model", "small"),
    }
    
    style_name = request_data["subtitle_style"]
    
    # Run pipeline
    result = await run_pipeline(
        url=url,
        job_id=job_id,
        progress_callback=None,
        **request_data,
    )
    
    clips = result.get("clips", [])
    transcript = result.get("analysis_bundle", {})
    full_segments = transcript.get("segments", [])
    
    # Score each clip
    scored_clips = []
    for i, clip in enumerate(clips):
        clip_segs = [
            s for s in full_segments
            if s.get("start", 0) < clip["end"] and s.get("end", 0) > clip["start"]
        ]
        clip_dur = clip["end"] - clip["start"]
        
        hook_text = None
        if clip_segs and i < 2:
            first_text = clip_segs[0].get("text", "").strip()
            if len(first_text) > 60:
                cut = first_text[:60].rfind(" ")
                hook_text = first_text[:cut] + "..." if cut > 20 else first_text[:57] + "..."
            else:
                hook_text = first_text
        
        v_score = score_clip_virality(
            clip=clip, transcript=clip_segs, full_segments=full_segments,
            clip_duration=clip_dur, hook_text=hook_text, style_name=style_name,
        )
        
        scored_clips.append({
            "clip_index": i,
            "start": clip["start"],
            "end": clip["end"],
            "duration": round(clip_dur, 1),
            "virality": score_to_api_dict(v_score),
            "output_path": clip.get("output_path"),
        })
    
    scored_clips.sort(key=lambda x: x["virality"]["composite"], reverse=True)
    
    return {
        "status": "success",
        "job_id": job_id,
        "total_clips": len(scored_clips),
        "clips": scored_clips,
        "best_clip": scored_clips[0] if scored_clips else None,
        "average_virality": round(
            sum(c["virality"]["composite"] for c in scored_clips) / max(len(scored_clips), 1), 1
        ),
    }
