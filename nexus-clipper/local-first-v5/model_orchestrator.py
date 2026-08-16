from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable
from .model_registry import ModelSpec, ModelRegistry
from .model_router import ModelRouter, RoutingRequest

@dataclass(frozen=True)
class ModelResult:
    task: str
    model_id: str
    success: bool
    confidence: float
    output: Any = None
    error: str | None = None

class LocalModelOrchestrator:
    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry
        self.router = ModelRouter(registry)
        self._handlers: dict[str, Callable[[Any], Any]] = {}

    def register_handler(self, model_id: str, handler: Callable[[Any], Any]) -> None:
        if self.registry.get(model_id) is None:
            raise KeyError(model_id)
        self._handlers[model_id] = handler

    def run(self, request: RoutingRequest, payload: Any) -> ModelResult:
        spec = self.router.route(request)
        if spec is None:
            return ModelResult(request.task, "", False, 0.0, error="no compatible local model")
        handler = self._handlers.get(spec.model_id)
        if handler is None:
            return ModelResult(request.task, spec.model_id, False, 0.0, error="model handler unavailable")
        try:
            output = handler(payload)
            confidence = max(0.0, min(1.0, float(spec.quality)))
            return ModelResult(request.task, spec.model_id, True, confidence, output=output)
        except Exception as exc:
            return ModelResult(request.task, spec.model_id, False, 0.0, error=str(exc))
