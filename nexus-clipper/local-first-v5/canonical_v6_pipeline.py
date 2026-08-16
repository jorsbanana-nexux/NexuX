from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from analysis_bundle import build_analysis_bundle
from analysis_world_service import build_and_persist_world
from contracts import GenerateRequest
from editorial_intelligence import generate_candidates
from editorial_intent import EditorialIntent
from editorial_ranker import select_diverse_from_world
from multimodal_editorial import (
    apply_cleanup_to_candidate,
    apply_editorial_intelligence,
    critic,
    dynamic_layout_plan,
    detect_filler_segments,
    revision_actions,
)
from publishing_analytics import build_publish_plan
from runtime_adapter import CanonicalRuntime, default_runtime
from targeted_retrieval import download_segment, fetch_recon_audio, fetch_youtube_captions
from voiceover import synthesize_sync


def _shift_transcript(transcript: dict[str, Any], offset: float) -> dict[str, Any]:
    result = {**transcript, "segments": []}
    for segment in transcript.get("segments", []):
        item = dict(segment)
        item["start"] = max(0.0, float(segment.get("start", 0.0)) - offset)
        item["end"] = max(0.0, float(segment.get("end", 0.0)) - offset)
        item["words"] = [
            {**dict(word), "start": max(0.0, float(word.get("start", 0.0)) - offset), "end": max(0.0, float(word.get("end", 0.0)) - offset)}
            for word in segment.get("words", []) or []
        ]
        result["segments"].append(item)
    result["duration"] = max(0.0, float(transcript.get("duration", 0.0)) - offset)
    result["source"] = f"{transcript.get('source', 'unknown')}:shifted"
    return result


def _shift_candidate(candidate: dict[str, Any], offset: float) -> dict[str, Any]:
    result = dict(candidate)
    result["start"] = max(0.0, float(candidate["start"]) - offset)
    result["end"] = max(result["start"], float(candidate["end"]) - offset)
    result["duration"] = result["end"] - result["start"]
    return result


def _reconnaissance(runtime: CanonicalRuntime, job_dir: Path, url: str, language: str | None, job_id: str) -> tuple[dict[str, Any], str]:
    transcript = fetch_youtube_captions(url, job_dir)
    if transcript:
        if language:
            transcript["language"] = language
        transcript["source"] = "youtube_vtt"
        return transcript, "youtube_vtt"
    audio = fetch_recon_audio(url, job_dir, job_id)
    transcript = runtime.transcribe_local(audio, language)
    transcript["source"] = "recon_audio_whisper"
    return transcript, "recon_audio_whisper"


def _max_candidates(req: GenerateRequest) -> int:
    return min(40, max(req.clip_count * 4, 12))


def _world_confidence(candidates: list[dict[str, Any]], audio_profiles: dict[str, dict[str, Any]], transcript: dict[str, Any]) -> dict[str, float]:
    transcript_confidence = 0.9 if transcript.get("segments") else 0.0
    candidate_confidence = min(1.0, 0.55 + min(len(candidates), 20) / 100.0)
    audio_confidence = 0.85 if audio_profiles else 0.0
    return {
        "transcript": transcript_confidence,
        "candidates": candidate_confidence,
        "audio": audio_confidence,
        "world": round((transcript_confidence + candidate_confidence + audio_confidence) / 3.0, 3),
    }


def _editorial_intent(req: GenerateRequest) -> EditorialIntent:
    return EditorialIntent(
        objective=req.editorial_objective,
        audience=req.audience,
        platform=(req.publish_platforms or ["generic"])[0],
        tone=req.editorial_tone,
        style=req.editorial_style,
        target_duration=float(req.target_duration),
        limit=int(req.clip_count),
        required_topics=tuple(req.required_topics),
        excluded_topics=tuple(req.excluded_topics),
    )


async def run_generation(job_id: str, req: GenerateRequest, runtime: CanonicalRuntime | None = None) -> None:
    runtime = runtime or default_runtime()
    job = runtime.read_job(job_id)
    try:
        runtime.cancel_flags.setdefault(job_id, False)
        if job.get("status") == "cancelled" or runtime.cancel_flags.get(job_id):
            return
        intent = _editorial_intent(req)
        job_dir = runtime.data_dir / "uploads" / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        source_probe = runtime.probe_youtube(req.youtube_url)
        runtime.set_job(job, status="processing", stage="reconnaissance", progress=5, source={"type":"youtube","url":req.youtube_url,"max_height":1080,"metadata":source_probe.metadata}, job_dir=str(job_dir), retrieval={"strategy":"caption-first-targeted"}, editorial_intent=intent.to_dict())

        transcript, recon_source = await asyncio.to_thread(_reconnaissance, runtime, job_dir, req.youtube_url, req.language, job_id)
        runtime.set_job(job, stage="candidate_generation", progress=24, transcript=transcript, retrieval={"strategy":"caption-first-targeted","recon_source":recon_source}, editorial_intent=intent.to_dict())
        if runtime.cancel_flags.get(job_id):
            runtime.set_job(job, status="cancelled", stage="cancelled")
            return

        candidates = generate_candidates(transcript.get("segments", []), max_candidates=1200)
        if not candidates:
            raise RuntimeError("No viable editorial candidates found")
        candidates = [{**candidate,"editorial_context":{"prompt":getattr(req,"clip_prompt",None),"genre":getattr(req,"genre","auto"),"target_duration":req.target_duration,"intent":intent.to_dict()}} for candidate in candidates]
        candidates, decision = apply_editorial_intelligence(candidates, prompt=getattr(req,"clip_prompt",None), genre=getattr(req,"genre","auto"))

        editorial_state={"intent":intent.to_dict(),"prompt":getattr(req,"clip_prompt",None),"genre":getattr(req,"genre","auto"),"target_duration":req.target_duration,"decision":decision.to_dict(),"stage":"pre_retrieval"}
        initial_world, initial_world_path = build_and_persist_world(runtime.jobs_dir, job_id=job_id, media=source_probe.metadata, transcript=transcript, candidates=candidates[:min(80,max(req.clip_count*12,40))], editorial=editorial_state, provenance={"world":"analysis_world:v2","transcript":transcript.get("source","unknown")}, confidence=_world_confidence(candidates,{},transcript))
        narrowed = select_diverse_from_world(initial_world, limit=min(_max_candidates(req),max(req.clip_count*4,12)), target_duration=float(req.target_duration))
        if not narrowed:
            raise RuntimeError("Initial editorial narrowing produced no candidates")

        prefetched: dict[str,dict[str,Any]] = {}
        audio_profiles: dict[str,dict[str,Any]] = {}
        world_scenes: list[dict[str,Any]] = []
        world_subjects: list[dict[str,Any]] = []
        enriched_candidates: list[dict[str,Any]] = []
        for idx, candidate in enumerate(narrowed):
            if runtime.cancel_flags.get(job_id):
                runtime.set_job(job,status="cancelled",stage="cancelled")
                return
            runtime.set_job(job,stage=f"building analysis world {idx+1}/{len(narrowed)}",progress=28+int(18*idx/max(1,len(narrowed))))
            video,retrieval=await asyncio.to_thread(download_segment,req.youtube_url,job_dir,candidate["id"],float(candidate["start"]),float(candidate["end"]),6.0,8.0,1080)
            media=await asyncio.to_thread(runtime.ffprobe,video)
            offset=float(retrieval["retrieved_start"])
            local_candidate=_shift_candidate(candidate,offset)
            local_transcript=_shift_transcript(transcript,offset)
            duration=float(media.get("format",{}).get("duration") or local_transcript.get("duration") or 0.0)
            scenes=await asyncio.to_thread(runtime.detect_scene_changes,video,0.0,duration or None)
            audio_profile=await asyncio.to_thread(runtime.analyze_audio,video,0.0,duration or max(0.0,float(local_candidate["end"])),speech_segments=local_transcript.get("segments",[]))
            audio_features=runtime.audio_signals(audio_profile)
            subject_samples=await asyncio.to_thread(runtime.detect_face_subjects,video,float(local_candidate["start"]),float(local_candidate["end"]))
            enriched={**candidate,"audio_profile":audio_profile.to_dict(),"audio_signals":audio_features,"vision_subject_count":len(subject_samples)}
            enriched_candidates.append(enriched)
            prefetched[candidate["id"]]={"video":video,"media":media,"retrieval":retrieval,"local_candidate":local_candidate,"local_transcript":local_transcript,"scenes":scenes,"audio_profile":audio_profile.to_dict(),"audio_signals":audio_features,"subjects":subject_samples}
            audio_profiles[str(candidate["id"])]=audio_profile.to_dict()
            world_scenes.extend([{**scene,"candidate_id":candidate["id"]} for scene in scenes])
            world_subjects.extend([{**subject,"candidate_id":candidate["id"]} for subject in subject_samples])

        editorial_state={"intent":intent.to_dict(),"prompt":getattr(req,"clip_prompt",None),"genre":getattr(req,"genre","auto"),"target_duration":req.target_duration,"decision":decision.to_dict(),"stage":"multimodal_editorial"}
        world,world_path=build_and_persist_world(runtime.jobs_dir,job_id=job_id,media=source_probe.metadata,transcript=transcript,audio_profiles=audio_profiles,scenes=world_scenes,subjects=world_subjects,candidates=enriched_candidates,editorial=editorial_state,provenance={"world":"analysis_world:v2","transcript":transcript.get("source","unknown"),"audio":"audio_intelligence","vision":"vision_service","intent":"editorial_intent:v1"},confidence=_world_confidence(enriched_candidates,audio_profiles,transcript))
        final_candidates=select_diverse_from_world(world,limit=req.clip_count,target_duration=float(req.target_duration))
        if not final_candidates:
            raise RuntimeError("AnalysisWorld editorial selection produced no candidates")

        filler_cuts=detect_filler_segments(transcript.get("segments",[]),min_pause=float(getattr(req,"pause_threshold",0.42))) if getattr(req,"remove_fillers_pauses",True) else []
        render_meta: list[dict[str,Any]]=[]
        rendered: list[str]=[]
        all_subject_samples: list[dict[str,Any]]=[]
        audio_evidence: list[dict[str,Any]]=[]

        for idx,candidate in enumerate(final_candidates):
            if runtime.cancel_flags.get(job_id):
                runtime.set_job(job,status="cancelled",stage="cancelled")
                return
            evidence=prefetched[candidate["id"]]
            video=evidence["video"]; retrieval=evidence["retrieval"]; media=evidence["media"]; local_candidate=dict(evidence["local_candidate"]); local_transcript=dict(evidence["local_transcript"]); audio_profile=dict(evidence["audio_profile"]); audio_features=dict(evidence["audio_signals"]); subject_samples=list(evidence["subjects"])
            local_candidate["cleanup_plan"]=apply_cleanup_to_candidate(local_candidate,filler_cuts).get("cleanup") if getattr(req,"remove_fillers_pauses",True) else {"enabled":False,"cuts":[],"removed_seconds":0.0}
            runtime.set_job(job,stage=f"rendering {idx+1}/{len(final_candidates)}",progress=50+int(38*idx/max(1,len(final_candidates))))
            timeline=await asyncio.to_thread(runtime.build_timeline,video,local_transcript,local_candidate)
            all_subject_samples.append({"candidate_id":local_candidate["id"],"observations":subject_samples})
            audio_evidence.append({"candidate_id":local_candidate["id"],"profile":audio_profile,"signals":audio_features})
            voiceover_path=None
            if getattr(req,"voice_over",False):
                vo_text=getattr(req,"voice_over_text",None) or local_candidate.get("text","")
                voiceover_path=runtime.outputs_dir/f"{job_id}_clip_{idx+1:02d}_voiceover.mp3"
                await asyncio.to_thread(synthesize_sync,vo_text,voiceover_path,getattr(req,"voice_style","male_narrator"))
            output=runtime.outputs_dir/f"{job_id}_clip_{idx+1:02d}.mp4"
            info=await asyncio.to_thread(runtime.render_with_spec,video,{**job,"job_id":job_id,"transcript":local_transcript,"meta":media},local_candidate,output,timeline,req,voiceover_path)
            rendered.append(f"/output/{output.name}")
            render_meta.append({"candidate_id":local_candidate["id"],"timeline":timeline.to_dict(),"render":info,"editorial_rank":candidate.get("editorial_rank"),"editorial_signals":candidate.get("editorial_signals"),"editorial_evidence":candidate.get("editorial_evidence"),"intent_reasoning":candidate.get("intent_reasoning"),"analysis_world":candidate.get("analysis_world"),"virality":local_candidate.get("virality_score"),"prompt_relevance":local_candidate.get("prompt_relevance"),"genre":local_candidate.get("genre",decision.genre),"dynamic_layout":dynamic_layout_plan(aspect_ratio=req.aspect_ratio,genre=decision.genre,face_tracking=req.face_tracking,auto_zoom=req.auto_zoom),"retrieval":retrieval,"audio_profile":audio_profile,"audio_signals":audio_features,"voiceover":str(voiceover_path) if voiceover_path else None})
            runtime.set_job(job,progress=50+int(40*(idx+1)/len(final_candidates)),render_meta=render_meta,audio_evidence=audio_evidence)

        analysis_bundle=build_analysis_bundle(transcript,final_candidates,world_scenes,all_subject_samples)
        critique_report=critic(render_meta,requested_duration=float(req.target_duration),expected_aspect=req.aspect_ratio)
        revision={"requested":critique_report.get("revision_required",False),"actions":revision_actions(critique_report),"attempt":int(job.get("revision",0))}
        publish_plan=build_publish_plan(job_id,final_candidates[0] if final_candidates else {},getattr(req,"publish_platforms",None))
        runtime.set_job(job,status="completed",stage="completed",progress=100,output_path=rendered[0] if rendered else None,clips=rendered,candidates=final_candidates,selected_candidate_id=final_candidates[0]["id"] if final_candidates else None,analysis_bundle=analysis_bundle.to_dict(),analysis_world={"path":str(world_path),"schema_version":world.schema_version,"modalities":sorted(world.modalities),"confidence":dict(world.confidence),"provenance":dict(world.provenance)},render_meta=render_meta,audio_evidence=audio_evidence,broll=False,critique=critique_report,revision=revision,publish_plan=publish_plan,editorial_intent=intent.to_dict(),editorial_decision=decision.to_dict(),retrieval={"strategy":"caption-first-targeted","recon_source":recon_source,"full_video_downloaded":False,"targeted_segments":len(prefetched),"initial_world":str(initial_world_path)})
    except Exception as exc:
        if runtime.cancel_flags.get(job_id): runtime.set_job(job,status="cancelled",stage="cancelled",error="Job cancelled")
        else: runtime.set_job(job,status="failed",stage="failed",error=str(exc))
    finally:
        runtime.cancel_flags.pop(job_id,None)
