from __future__ import annotations

from typing import Any

from analysis_world import AnalysisWorld
from editorial_intent import normalize_intent
from editorial_ranker import select_diverse
from editorial_reasoning import reason_candidates


def select_diverse_from_world_with_intent(
    world: AnalysisWorld,
    *,
    limit: int = 10,
    target_duration: float = 45.0,
) -> list[dict[str, Any]]:
    """Select candidates using explicit intent before multimodal editorial ranking."""
    world.validate()
    intent = normalize_intent(world.editorial.get("intent", {}))
    candidates = [dict(item) for item in world.candidates]
    reasoned = reason_candidates(candidates, intent=intent)

    # Preserve the existing multimodal ranker while making intent a first-class gate.
    # A generous pool avoids overfitting to one deterministic heuristic.
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
    return selected
