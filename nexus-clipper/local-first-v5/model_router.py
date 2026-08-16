from __future__ import annotations
from dataclasses import dataclass
from .model_registry import ModelRegistry, ModelSpec

@dataclass(frozen=True)
class RoutingRequest:
    task: str
    modality: str
    quality_weight: float = 0.6
    speed_weight: float = 0.4
    max_vram_gb: float | None = None
    local_only: bool = True

class ModelRouter:
    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry

    def route(self, request: RoutingRequest) -> ModelSpec | None:
        candidates = self.registry.candidates(request.task, request.modality, local_only=request.local_only)
        if request.max_vram_gb is not None:
            candidates = tuple(c for c in candidates if c.vram_gb <= request.max_vram_gb)
        if not candidates:
            return None
        return max(candidates, key=lambda c: request.quality_weight * c.quality + request.speed_weight * c.speed)
