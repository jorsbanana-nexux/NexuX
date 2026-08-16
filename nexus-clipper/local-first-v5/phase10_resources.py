from __future__ import annotations

from typing import Any


def resource_guard(*, memory_gb: float, vram_gb: float = 0.0, requested_workers: int, requested_batch: int) -> dict[str, Any]:
    workers = max(1, int(requested_workers))
    batch = max(1, int(requested_batch))
    if memory_gb and memory_gb < 4:
        workers = 1
        batch = 1
    elif memory_gb and memory_gb < 8:
        workers = min(workers, 2)
        batch = min(batch, 2)
    if vram_gb and vram_gb < 4:
        batch = min(batch, 2)
    return {
        "workers": workers,
        "batch_size": batch,
        "degraded": workers < requested_workers or batch < requested_batch,
    }
