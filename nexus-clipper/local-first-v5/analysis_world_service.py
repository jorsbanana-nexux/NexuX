from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from analysis_world import AnalysisWorld, build_analysis_world


def world_path(jobs_dir: Path, job_id: str) -> Path:
    return jobs_dir / f"{job_id}.analysis-world.json"


def persist_world(jobs_dir: Path, world: AnalysisWorld) -> Path:
    world.validate()
    path = world_path(jobs_dir, world.job_id)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(world.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
    return path


def load_world(jobs_dir: Path, job_id: str) -> dict[str, Any]:
    path = world_path(jobs_dir, job_id)
    if not path.exists():
        raise FileNotFoundError(f"AnalysisWorld not found for job {job_id}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "2.0":
        raise ValueError(f"Unsupported AnalysisWorld schema: {payload.get('schema_version')}")
    return payload


def build_and_persist_world(
    jobs_dir: Path,
    *,
    job_id: str,
    media: Mapping[str, Any] | None = None,
    transcript: Mapping[str, Any] | None = None,
    audio_profiles: Mapping[str, Mapping[str, Any]] | None = None,
    scenes: list[Mapping[str, Any]] | None = None,
    subjects: list[Mapping[str, Any]] | None = None,
    candidates: list[Mapping[str, Any]] | None = None,
    editorial: Mapping[str, Any] | None = None,
    provenance: Mapping[str, Any] | None = None,
    confidence: Mapping[str, float] | None = None,
) -> tuple[AnalysisWorld, Path]:
    world = build_analysis_world(
        job_id=job_id,
        media=media,
        transcript=transcript,
        audio_profiles=audio_profiles,
        scenes=scenes,
        subjects=subjects,
        candidates=candidates,
        editorial=editorial,
        provenance=provenance,
        confidence=confidence,
    )
    return world, persist_world(jobs_dir, world)
