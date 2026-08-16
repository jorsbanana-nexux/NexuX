from __future__ import annotations

from typing import Any

from analysis_world import AnalysisWorld, build_analysis_world
from contextual_narrative import verify_context


def enrich_world_with_context(world: AnalysisWorld, *, radius: float = 18.0) -> AnalysisWorld:
    world.validate()
    enriched: list[dict[str, Any]] = []
    for raw in world.candidates:
        candidate = dict(raw)
        assessment = verify_context(candidate, world.transcript, radius=radius)
        candidate["contextual_narrative"] = assessment.to_dict()
        enriched.append(candidate)
    editorial = dict(world.editorial)
    editorial["contextual_verification"] = {"enabled": True, "radius_seconds": float(radius), "candidate_count": len(enriched)}
    provenance = dict(world.provenance)
    provenance["contextual_narrative"] = "contextual_narrative:v1"
    confidence = dict(world.confidence)
    if enriched:
        confidence["context"] = round(sum(float(x["contextual_narrative"].get("confidence", 0.0)) for x in enriched) / len(enriched), 3)
        confidence["world"] = round(sum(float(x) for x in confidence.values()) / max(1, len(confidence)), 3)
    return build_analysis_world(job_id=world.job_id, media=world.media, transcript=world.transcript, audio_profiles=world.audio.get("profiles", {}), scenes=world.vision.get("scenes", []), subjects=world.vision.get("subjects", []), candidates=enriched, editorial=editorial, provenance=provenance, confidence=confidence)


def contextual_score(candidate: dict[str, Any]) -> float:
    assessment = candidate.get("contextual_narrative", {}) or {}
    quality = float(assessment.get("context_integrity", 0.0)); match = float(assessment.get("promise_payoff_match", 0.0)); risk = float(assessment.get("premature_cut_risk", 0.0))
    return max(0.0, min(1.0, 0.55 * quality + 0.30 * match - 0.35 * risk))
