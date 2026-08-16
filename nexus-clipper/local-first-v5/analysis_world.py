from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

SCHEMA_VERSION = "2.0"
SUPPORTED_MODALITIES = frozenset({"media", "transcript", "audio", "vision", "candidates", "editorial"})


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


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


@dataclass(frozen=True)
class AnalysisWorld:
    """Immutable, versioned evidence graph for one canonical source job."""

    schema_version: str
    job_id: str
    media: Mapping[str, Any]
    transcript: Mapping[str, Any]
    audio: Mapping[str, Any]
    vision: Mapping[str, Any]
    candidates: tuple[Mapping[str, Any], ...]
    editorial: Mapping[str, Any]
    provenance: Mapping[str, Any]
    confidence: Mapping[str, float]

    @property
    def modalities(self) -> frozenset[str]:
        available = set()
        for name, value in (
            ("media", self.media),
            ("transcript", self.transcript),
            ("audio", self.audio),
            ("vision", self.vision),
            ("candidates", self.candidates),
            ("editorial", self.editorial),
        ):
            if value:
                available.add(name)
        return frozenset(available)

    def validate(self) -> "AnalysisWorld":
        _require(self.schema_version == SCHEMA_VERSION, f"Unsupported AnalysisWorld schema: {self.schema_version}")
        _require(bool(self.job_id), "AnalysisWorld.job_id is required")
        _require(isinstance(self.transcript, Mapping), "transcript must be a mapping")
        _require(isinstance(self.candidates, tuple), "candidates must be immutable")
        _require(all(isinstance(item, Mapping) for item in self.candidates), "candidate entries must be mappings")
        _require(all(0.0 <= float(value) <= 1.0 for value in self.confidence.values()), "confidence values must be in [0,1]")
        _require(set(self.provenance).issubset(SUPPORTED_MODALITIES | {"world"}), "unknown provenance modality")
        return self

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "schema_version": self.schema_version,
            "job_id": self.job_id,
            "modalities": sorted(self.modalities),
            "media": _thaw(self.media),
            "transcript": _thaw(self.transcript),
            "audio": _thaw(self.audio),
            "vision": _thaw(self.vision),
            "candidates": [_thaw(item) for item in self.candidates],
            "editorial": _thaw(self.editorial),
            "provenance": _thaw(self.provenance),
            "confidence": _thaw(self.confidence),
        }


def build_analysis_world(
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
) -> AnalysisWorld:
    world = AnalysisWorld(
        schema_version=SCHEMA_VERSION,
        job_id=job_id,
        media=_freeze(dict(media or {})),
        transcript=_freeze(dict(transcript or {})),
        audio=_freeze({"profiles": dict(audio_profiles or {})}),
        vision=_freeze({"scenes": list(scenes or []), "subjects": list(subjects or [])}),
        candidates=tuple(_freeze(dict(item)) for item in (candidates or [])),
        editorial=_freeze(dict(editorial or {})),
        provenance=_freeze(dict(provenance or {"world": "analysis_world:v2"})),
        confidence=_freeze({str(key): float(value) for key, value in (confidence or {}).items()}),
    )
    return world.validate()
