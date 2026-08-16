from .model_registry import ModelRegistry, ModelSpec
from .model_router import ModelRouter, RoutingRequest
from .model_orchestrator import LocalModelOrchestrator
from .confidence_calibration import calibrate

def test_local_model_routing_and_fallback():
    registry = ModelRegistry([ModelSpec("small", "family-a", frozenset({"text"}), frozenset({"text"}), quality=.8, speed=.9, vram_gb=2)])
    router = ModelRouter(registry)
    assert router.route(RoutingRequest("text", "text", max_vram_gb=2)).model_id == "small"
    assert router.route(RoutingRequest("vision", "image")) is None
    orch = LocalModelOrchestrator(registry)
    result = orch.run(RoutingRequest("text", "text"), "x")
    assert result.success is False

def test_confidence_is_bounded():
    assert 0 <= calibrate(2, reliability=.5, disagreement=.2) <= 1
