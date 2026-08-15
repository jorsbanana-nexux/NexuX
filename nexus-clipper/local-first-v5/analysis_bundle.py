from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

SCHEMA_VERSION = "1.0"


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True)
class AnalysisBundle:
    """Deeply immutable cross-stage analysis contract for one source job."""

    schema_version: str
    transcript: Mapping[str, Any]
    candidates: tuple[Mapping[str, Any], ...]
    scenes: tuple[Mapping[str, Any], ...]
    subjects: tuple[Mapping[str, Any], ...]
    audio_profiles: Mapping[str, Mapping[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "transcript": _thaw(self.transcript),
            "candidates": [_thaw(item) for item in self.candidates],
            "scenes": [_thaw(item) for item in self.scenes],
            "subjects": [_thaw(item) for item in self.subjects],
            "audio_profiles": _thaw(self.audio_profiles),
        }


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
        transcript=_freeze(transcript),
        candidates=tuple(_freeze(dict(item)) for item in candidates),
        scenes=tuple(_freeze(dict(item)) for item in scenes),
        subjects=tuple(_freeze(dict(item)) for item in subjects),
        audio_profiles=_freeze(profiles),
    )
