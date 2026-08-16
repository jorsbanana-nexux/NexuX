from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

from parallel_executor import run_parallel
from phase10_hardware import HardwareProfile, choose_execution_policy
from phase10_resources import resource_guard


def run_multimodal_stages(
    stages: Sequence[Callable[[], Any]],
    *,
    profile: HardwareProfile,
    workload: str = "multimodal",
) -> list[Any]:
    policy = choose_execution_policy(profile, workload=workload)
    safe = resource_guard(
        memory_gb=profile.memory_gb,
        vram_gb=profile.vram_gb,
        requested_workers=policy["max_parallel_vision"],
        requested_batch=policy["batch_size"],
    )
    # The stage list itself remains the source of truth; this layer only schedules independent work.
    return run_parallel(stages, lambda stage: stage(), workers=safe["workers"])
