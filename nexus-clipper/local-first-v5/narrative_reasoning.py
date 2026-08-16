from __future__ import annotations

from typing import Any, Mapping

from analysis_world import AnalysisWorld, build_analysis_world
from narrative_model import NarrativeAssessment, assess_narrative


def assess_world_candidates(world: AnalysisWorld) -> dict[str, NarrativeAssessment]:
    transcript = world.transcript
    return {str(candidate.get("id", "")): assess_narrative(candidate, transcript) for candidate in world.candidates}


def enrich_world_with_narrative(world: AnalysisWorld) -> AnalysisWorld:
    assessments = assess_world_candidates(world)
    candidates: list[dict[str, Any]] = []
    for candidate in world.candidates:
        item = dict(candidate)
        assessment = assessments.get(str(candidate.get("id", "")))
        if assessment:
            item["narrative_assessment"] = assessment.to_dict()
        candidates.append(item)
    editorial = dict(world.editorial)
    editorial["narrative_engine"] = {"schema_version": "1.0", "candidates": len(assessments)}
    return build_analysis_world(
        job_id=world.job_id,
        media=dict(world.media),
        transcript=dict(world.transcript),
        audio_profiles=dict(world.audio.get("profiles", {}) or {}),
        scenes=list(world.vision.get("scenes", []) or []),
        subjects=list(world.vision.get("subjects", []) or []),
        candidates=candidates,
        editorial=editorial,
        provenance={**dict(world.provenance), "narrative": "narrative_reasoning:v1"},
        confidence=dict(world.confidence),
    )


def narrative_score(candidate: Mapping[str, Any]) -> float:
    assessment = candidate.get("narrative_assessment") or {}
    return float(assessment.get("editorial_quality", 0.0) or 0.0)


def narrative_decision(candidate: Mapping[str, Any]) -> str:
    assessment = candidate.get("narrative_assessment") or {}
    return str(assessment.get("recommendation", "REVIEW"))
