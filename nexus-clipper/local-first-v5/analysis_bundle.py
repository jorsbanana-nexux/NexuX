from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class AnalysisBundle:
    """Immutable cross-stage analysis contract for one source job."""

    schema_version: str
    transcript: dict[str, Any]
    candidates: tuple[dict[str, Any], ...]
    scenes: tuple[dict[str, Any], ...]
    subjects: tuple[dict[str, Any], ...]
    audio_profiles: dict[str, dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["candidates"] = list(self.candidates)
        data["scenes"] = list(self.scenes)
        data["subjects"] = list(self.subjects)
        return data


def build_analysis_bundle(
    transcript: dict[str, Any],
    candidates: list[dict[str, Any]],
    scenes: list[dict[str, Any]],
    subjects: list[dict[str, Any]],
) -> AnalysisBundle:
    profiles: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        profile = candidate.get("audio_profile")
        candidate_id = candidate.get("id")
        if isinstance(profile, dict) and candidate_id:
            profiles[str(candidate_id)] = dict(profile)
    return AnalysisBundle(
        schema_version=SCHEMA_VERSION,
        transcript=transcript,
        candidates=tuple(dict(item) for item in candidates),
        scenes=tuple(dict(item) for item in scenes),
        subjects=tuple(dict(item) for item in subjects),
        audio_profiles=profiles,
    )
