from __future__ import annotations

from dataclasses import asdict, dataclass
import os
from typing import Any


@dataclass(frozen=True)
class HardwareProfile:
    cpu_count: int
    memory_gb: float
    gpu_available: bool = False
    vram_gb: float = 0.0
    platform: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_hardware() -> HardwareProfile:
    memory_gb = 0.0
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        memory_gb = (pages * page_size) / (1024**3)
    except (ValueError, OSError, AttributeError):
        pass
    return HardwareProfile(
        cpu_count=max(1, os.cpu_count() or 1),
        memory_gb=round(memory_gb, 2),
        platform=os.name,
    )


def choose_execution_policy(profile: HardwareProfile, *, workload: str = "multimodal") -> dict[str, Any]:
    workers = max(1, min(8, profile.cpu_count // 2 if profile.cpu_count >= 4 else 1))
    return {
        "workers": workers,
        "batch_size": 1 if workload == "render" else (8 if profile.gpu_available else 4),
        "frame_stride": 1 if profile.gpu_available else 2,
        "prefer_gpu": bool(profile.gpu_available),
        "max_parallel_vision": max(1, min(4, workers)),
    }
