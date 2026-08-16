from __future__ import annotations

from phase10_cache import JsonCache, cache_key
from phase10_execution import run_multimodal_stages
from phase10_hardware import HardwareProfile, choose_execution_policy
from phase10_resources import resource_guard


def test_cache_round_trip(tmp_path):
    cache = JsonCache(tmp_path)
    key = cache_key("video", "scene", 3)
    cache.put(key, {"value": 7}, {"kind": "scene"})
    record = cache.get(key)
    assert record is not None
    assert record.artifact["value"] == 7
    assert record.metadata["kind"] == "scene"


def test_resource_guard_degrades_low_memory():
    result = resource_guard(memory_gb=3.0, requested_workers=4, requested_batch=8)
    assert result["workers"] == 1
    assert result["batch_size"] == 1
    assert result["degraded"] is True


def test_parallel_stage_execution_preserves_order():
    profile = HardwareProfile(cpu_count=4, memory_gb=16)
    stages = [lambda: "audio", lambda: "vision", lambda: "ocr"]
    assert run_multimodal_stages(stages, profile=profile) == ["audio", "vision", "ocr"]


def test_execution_policy_is_bounded():
    profile = HardwareProfile(cpu_count=64, memory_gb=128, gpu_available=True)
    policy = choose_execution_policy(profile)
    assert 1 <= policy["workers"] <= 8
    assert 1 <= policy["max_parallel_vision"] <= 4
