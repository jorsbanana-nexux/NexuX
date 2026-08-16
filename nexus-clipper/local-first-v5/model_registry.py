from __future__ import annotations
from dataclasses import dataclass, field
from typing import Mapping

SCHEMA_VERSION = "1.0"

@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    family: str
    tasks: frozenset[str]
    modalities: frozenset[str]
    local: bool = True
    quality: float = 0.5
    speed: float = 0.5
    vram_gb: float = 0.0
    metadata: Mapping[str, str] = field(default_factory=dict)

    def validate(self) -> "ModelSpec":
        if not self.model_id or not self.family or not self.tasks or not self.modalities:
            raise ValueError("model identity, tasks, and modalities are required")
        if not 0 <= self.quality <= 1 or not 0 <= self.speed <= 1 or self.vram_gb < 0:
            raise ValueError("invalid quality/speed/vram")
        return self

class ModelRegistry:
    def __init__(self, specs: list[ModelSpec] | None = None) -> None:
        self._specs = {s.model_id: s.validate() for s in (specs or [])}
    def register(self, spec: ModelSpec) -> None:
        self._specs[spec.model_id] = spec.validate()
    def get(self, model_id: str) -> ModelSpec | None:
        return self._specs.get(model_id)
    def candidates(self, task: str, modality: str, *, local_only: bool = True) -> tuple[ModelSpec, ...]:
        return tuple(s for s in self._specs.values() if task in s.tasks and modality in s.modalities and (s.local or not local_only))
    def snapshot(self) -> dict[str, dict[str, object]]:
        return {k: {"family": v.family, "tasks": sorted(v.tasks), "modalities": sorted(v.modalities), "local": v.local, "quality": v.quality, "speed": v.speed, "vram_gb": v.vram_gb} for k, v in self._specs.items()}
