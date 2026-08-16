from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from analysis_world import AnalysisWorld


@dataclass(frozen=True)
class EditorialEvidence:
    candidate_id: str
    text: str
    start: float
    end: float
    duration: float
    audio: dict[str, Any]
    scenes: tuple[dict[str, Any], ...]
    subjects: tuple[dict[str, Any], ...]
    confidence: float
    provenance: tuple[str, ...]


def build_editorial_evidence(world: AnalysisWorld) -> tuple[EditorialEvidence, ...]:
    scene_list = tuple(world.vision.get("scenes", []) or [])
    subject_list = tuple(world.vision.get("subjects", []) or [])
    audio_profiles = world.audio.get("profiles", {}) or {}
    candidates = world.candidates
    provenance_values = tuple(f"{key}:{value}" for key, value in world.provenance.items())
    world_confidence = float(world.confidence.get("world", 0.0))

    result: list[EditorialEvidence] = []
    for candidate in candidates:
        candidate_id = str(candidate.get("id", ""))
        start = float(candidate.get("start", 0.0))
        end = float(candidate.get("end", start))
        result.append(
            EditorialEvidence(
                candidate_id=candidate_id,
                text=str(candidate.get("text", "")),
                start=start,
                end=end,
                duration=max(0.0, end - start),
                audio=dict(audio_profiles.get(candidate_id, {}) or {}),
                scenes=scene_list,
                subjects=subject_list,
                confidence=float(candidate.get("confidence", world_confidence)),
                provenance=provenance_values,
            )
        )
    return tuple(result)


def ranking_context(world: AnalysisWorld) -> dict[str, Any]:
    evidence = build_editorial_evidence(world)
    return {
        "schema_version": world.schema_version,
        "job_id": world.job_id,
        "confidence": dict(world.confidence),
        "provenance": dict(world.provenance),
        "modalities": sorted(world.modalities),
        "candidates": [item.__dict__ for item in evidence],
        "intent": dict(world.editorial),
        "semantics": dict(world.editorial.get("semantics", {}) or {}),
    }
