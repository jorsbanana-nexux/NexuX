from __future__ import annotations

from typing import Any

from adaptive_context import adaptive_verify_context
from analysis_world import AnalysisWorld
from contextual_reasoning import contextual_score, enrich_world_with_context
from editorial_intent import normalize_intent
from editorial_ranker import select_diverse
from editorial_reasoning import reason_candidates
from narrative_reasoning import enrich_world_with_narrative, narrative_score


def select_diverse_from_world_with_intent(world: AnalysisWorld, *, limit: int = 10, target_duration: float = 45.0) -> list[dict[str, Any]]:
    """Select candidates using intent, narrative, adaptive context, and multimodal ranking."""
    world.validate()
    world = enrich_world_with_context(world)
    world = enrich_world_with_narrative(world)
    intent = normalize_intent(world.editorial.get("intent", {}))
    candidates = [dict(item) for item in world.candidates]
    reasoned = reason_candidates(candidates, intent=intent)
    for item in reasoned:
        item["narrative_score"] = round(narrative_score(item), 6)
        item["contextual_score"] = round(contextual_score(item), 6)
        adaptive = adaptive_verify_context(item, world.transcript)
        item["adaptive_context"] = adaptive.to_dict()
        item["adaptive_context_score"] = round(0.60 * adaptive.semantic_match + 0.40 * adaptive.confidence, 6)
        narrative = item.get("narrative_assessment", {}) or {}
        contextual = item.get("contextual_narrative", {}) or {}
        item["narrative_recommendation"] = narrative.get("recommendation", "REVIEW")
        item["narrative_reasons"] = list(narrative.get("reasons", []) or [])
        item["contextual_recommendation"] = contextual.get("recommendation", "REVIEW")
        item["contextual_reasons"] = list(contextual.get("reasons", []) or [])

    reasoned.sort(
        key=lambda item: (
            0.32 * float(item.get("intent_reasoning", {}).get("intent_score", 0.0))
            + 0.28 * float(item.get("narrative_score", 0.0))
            + 0.18 * float(item.get("contextual_score", 0.0))
            + 0.22 * float(item.get("adaptive_context_score", 0.0))
        ),
        reverse=True,
    )
    pool_size = max(limit * 4, min(len(reasoned), 40))
    pool = reasoned[:pool_size]
    audio_profiles = dict(world.audio.get("profiles", {}) or {})
    selected = select_diverse(pool, limit=limit, target_duration=target_duration, scene_boundaries=list(world.vision.get("scenes", []) or []), audio_profiles={key: dict(value) for key, value in audio_profiles.items()}, transcript=world.transcript, vision=dict(world.vision))
    for item in selected:
        item["analysis_world"] = {"schema_version": world.schema_version, "job_id": world.job_id, "modalities": sorted(world.modalities), "confidence": dict(world.confidence), "provenance": dict(world.provenance)}
        item["intent"] = intent.to_dict()
        item["narrative_reasoning"] = {"score": float(item.get("narrative_score", 0.0)), "recommendation": item.get("narrative_recommendation", "REVIEW"), "reasons": list(item.get("narrative_reasons", []) or [])}
        contextual = item.get("contextual_narrative", {}) or {}
        adaptive = item.get("adaptive_context", {}) or {}
        item["contextual_reasoning"] = {"score": float(item.get("contextual_score", 0.0)), "recommendation": contextual.get("recommendation", "REVIEW"), "reasons": list(contextual.get("reasons", []) or []), "promise_payoff_match": float(contextual.get("promise_payoff_match", 0.0)), "premature_cut_risk": float(contextual.get("premature_cut_risk", 0.0))}
        item["adaptive_context_reasoning"] = {"score": float(item.get("adaptive_context_score", 0.0)), "semantic_match": float(adaptive.get("semantic_match", 0.0)), "uncertainty": float(adaptive.get("uncertainty", 0.0)), "final_radius": float(adaptive.get("final_radius", 0.0)), "expansions": int(adaptive.get("expansions", 0)), "stop_reason": adaptive.get("stop_reason", "unknown"), "confidence": float(adaptive.get("confidence", 0.0))}
    return selected
