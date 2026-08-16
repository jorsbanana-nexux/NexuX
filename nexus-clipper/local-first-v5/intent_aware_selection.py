from __future__ import annotations

from typing import Any

from analysis_world import AnalysisWorld
from editorial_intent import normalize_intent
from editorial_ranker import select_diverse
from editorial_reasoning import reason_candidates
from narrative_reasoning import assess_world_candidates, enrich_world_with_narrative, narrative_score


def select_diverse_from_world_with_intent(
    world: AnalysisWorld,
    *,
    limit: int = 10,
    target_duration: float = 45.0,
) -> list[dict[str, Any]]:
    """Select candidates using intent plus explicit narrative judgment before multimodal ranking."""
    world.validate()
    world = enrich_world_with_narrative(world)
    intent = normalize_intent(world.editorial.get("intent", {}))
    candidates = [dict(item) for item in world.candidates]
    reasoned = reason_candidates(candidates, intent=intent)
    for item in reasoned:
        item["narrative_score"] = round(narrative_score(item), 6)
        assessment = item.get("narrative_assessment", {})
        item["narrative_recommendation"] = assessment.get("recommendation", "REVIEW")
        item["narrative_reasons"] = list(assessment.get("reasons", []) or [])

    # Narrative quality is a bounded gate, not a replacement for multimodal scoring.
    # Keep a sufficiently large pool so narrative heuristics cannot erase stronger alternatives.
    reasoned.sort(key=lambda item: 0.55 * float(item.get("intent_reasoning", {}).get("intent_score", 0.0)) + 0.45 * float(item.get("narrative_score", 0.0)), reverse=True)
    pool_size = max(limit * 4, min(len(reasoned), 40))
    pool = reasoned[:pool_size]
    audio_profiles = dict(world.audio.get("profiles", {}) or {})
    selected = select_diverse(
        pool,
        limit=limit,
        target_duration=target_duration,
        scene_boundaries=list(world.vision.get("scenes", []) or []),
        audio_profiles={key: dict(value) for key, value in audio_profiles.items()},
        transcript=world.transcript,
        vision=dict(world.vision),
    )
    for item in selected:
        item["analysis_world"] = {
            "schema_version": world.schema_version,
            "job_id": world.job_id,
            "modalities": sorted(world.modalities),
            "confidence": dict(world.confidence),
            "provenance": dict(world.provenance),
        }
        item["intent"] = intent.to_dict()
        item["narrative_reasoning"] = {
            "score": float(item.get("narrative_score", 0.0)),
            "recommendation": item.get("narrative_recommendation", "REVIEW"),
            "reasons": list(item.get("narrative_reasons", []) or []),
        }
    return selected
