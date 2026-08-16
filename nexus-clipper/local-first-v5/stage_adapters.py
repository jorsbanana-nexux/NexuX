"""Phase 13 concrete stage adapters for the canonical production pipeline.

Adapters expose existing NexuX implementations behind the Phase 12 stage contract.
They intentionally fail closed when required context is missing.
"""
from __future__ import annotations

from typing import Any, Mapping

import server as engine
from editorial_intelligence import apply_editorial_intelligence, generate_candidates
from editorial_ranker import select_diverse
from multimodal_editorial import critic, revision_actions
from publishing_analytics import build_publish_plan
from targeted_retrieval import download_segment, fetch_recon_audio, fetch_youtube_captions


def ingest_stage(ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    url = str(ctx.get("youtube_url") or "").strip()
    if not url:
        raise ValueError("ingest requires youtube_url")
    job_dir = ctx.get("job_dir")
    job_id = str(ctx.get("job_id") or "run")
    if not job_dir:
        raise ValueError("ingest requires job_dir")
    return {"source": {"type": "youtube", "url": url}, "job_dir": str(job_dir), "job_id": job_id, "retrieval_strategy": "caption-first-targeted", "confidence": 1.0, "provenance": ("stage_adapters.ingest",)}


def transcribe_stage(ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    url = str(ctx.get("youtube_url") or "").strip()
    job_dir = ctx.get("job_dir")
    job_id = str(ctx.get("job_id") or "run")
    language = ctx.get("language")
    if not url or not job_dir:
        raise ValueError("transcribe requires youtube_url and job_dir")
    transcript = fetch_youtube_captions(url, job_dir)
    source = "youtube_vtt"
    if not transcript:
        audio = fetch_recon_audio(url, job_dir, job_id)
        transcript = engine.transcribe_local(audio, language)
        source = "recon_audio_whisper"
    if language:
        transcript["language"] = language
    return {"transcript": transcript, "transcription_source": source, "confidence": 0.92 if source == "youtube_vtt" else 0.86, "provenance": ("stage_adapters.transcribe", source)}


def analyze_stage(ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    transcript = dict(ctx.get("transcript") or {})
    segments = transcript.get("segments") or []
    if not segments:
        raise ValueError("analyze requires transcript segments")
    candidates = generate_candidates(segments, max_candidates=int(ctx.get("max_candidates", 1200)))
    audio = dict(ctx.get("audio_profiles") or {})
    vision = dict(ctx.get("vision") or {})
    return {"candidates": candidates, "audio_profiles": audio, "vision": vision, "confidence": 0.8, "provenance": ("editorial_intelligence.generate_candidates",)}


def reason_stage(ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    candidates = [dict(x) for x in (ctx.get("candidates") or [])]
    if not candidates:
        raise ValueError("reason requires candidates")
    updated, decision = apply_editorial_intelligence(candidates, prompt=ctx.get("clip_prompt"), genre=ctx.get("genre", "auto"))
    return {"candidates": updated, "editorial_decision": decision.to_dict() if hasattr(decision, "to_dict") else decision, "confidence": float(getattr(decision, "confidence", 0.75)), "provenance": ("editorial_intelligence.apply_editorial_intelligence",)}


def plan_stage(ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    candidates = [dict(x) for x in (ctx.get("candidates") or [])]
    limit = max(1, int(ctx.get("clip_count", 1)) * 4)
    ranked = select_diverse(candidates, limit=limit, target_duration=float(ctx.get("target_duration", 45)), scene_boundaries=None, audio_profiles=dict(ctx.get("audio_profiles") or {}), transcript=dict(ctx.get("transcript") or {}), vision=dict(ctx.get("vision") or {}))
    if not ranked:
        raise RuntimeError("plan produced no viable candidates")
    return {"story_candidates": ranked, "confidence": 0.78, "provenance": ("editorial_ranker.select_diverse",)}


def direct_stage(ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    # Reuse the existing director outputs when present; Phase 6 remains an additive control layer.
    directives = dict(ctx.get("directives") or {})
    directives.setdefault("aspect_ratio", ctx.get("aspect_ratio", "9:16"))
    directives.setdefault("face_tracking", bool(ctx.get("face_tracking", True)))
    directives.setdefault("auto_zoom", bool(ctx.get("auto_zoom", True)))
    return {"directives": directives, "confidence": 0.7, "provenance": ("phase6.directors",)}


def render_stage(ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    # The concrete renderer is deliberately invoked through the existing canonical function.
    render_fn = ctx.get("render_fn")
    if not callable(render_fn):
        raise RuntimeError("render stage requires an injected render_fn to preserve canonical renderer ownership")
    result = render_fn(ctx)
    return {"render_result": result, "confidence": 0.99, "provenance": ("injected.canonical_renderer",)}


def critic_stage(ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    render_meta = list(ctx.get("render_meta") or [])
    report = critic(render_meta, requested_duration=float(ctx.get("target_duration", 45)), expected_aspect=str(ctx.get("aspect_ratio", "9:16")))
    return {"critique": report, "confidence": 0.82, "provenance": ("multimodal_editorial.critic",)}


def revise_stage(ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    critique = dict(ctx.get("critique") or {})
    required = bool(critique.get("revision_required", False))
    return {"revision_required": required, "revision_actions": revision_actions(critique), "confidence": 0.8, "provenance": ("multimodal_editorial.revision_actions",)}


def publish_stage(ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    candidates = list(ctx.get("story_candidates") or [])
    first = candidates[0] if candidates else {}
    plan = build_publish_plan(str(ctx.get("job_id") or "run"), first, ctx.get("publish_platforms"))
    return {"publish_plan": plan, "confidence": 0.9, "provenance": ("publishing_analytics.build_publish_plan",)}


def feedback_stage(ctx: Mapping[str, Any]) -> Mapping[str, Any]:
    return {"feedback_record": {"job_id": ctx.get("job_id"), "status": ctx.get("status", "completed"), "source": "phase13"}, "confidence": 0.5, "provenance": ("stage_adapters.feedback",)}


CONCRETE_STAGES = {
    "ingest": ingest_stage,
    "transcribe": transcribe_stage,
    "analyze": analyze_stage,
    "reason": reason_stage,
    "plan": plan_stage,
    "direct": direct_stage,
    "render": render_stage,
    "critic": critic_stage,
    "revise": revise_stage,
    "publish": publish_stage,
    "feedback": feedback_stage,
}
