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
    modalities = world.modalities
    vision = modalities.get("vision", {}) or {}
    audio = modalities.get("audio", {}) or {}
    editorial = modalities.get("editorial", {}) or {}
    scene_list = tuple(vision.get("scenes", []) or [])
    subject_list = tuple(vision.get("subjects", []) or [])
    audio_profiles = audio.get("profiles", {}) or {}
    candidates = editorial.get("candidates", []) or []

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
                confidence=float(candidate.get("confidence", world.confidence)),
                provenance=(world.provenance.source, world.provenance.analysis_engine),
            )
        )
    return tuple(result)


def ranking_context(world: AnalysisWorld) -> dict[str, Any]:
    evidence = build_editorial_evidence(world)
    return {
        "schema_version": world.schema_version,
        "world_id": world.world_id,
        "confidence": world.confidence,
        "provenance": world.provenance.to_dict(),
        "candidates": [item.__dict__ for item in evidence],
        "intent": dict(world.modalities.get("intent", {}) or {}),
        "semantics": dict(world.modalities.get("semantics", {}) or {}),
    }
