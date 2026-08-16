from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Iterable


def run_parallel(items: Iterable[Any], fn: Callable[[Any], Any], *, workers: int = 4) -> list[Any]:
    values = list(items)
    if not values:
        return []
    if workers <= 1 or len(values) == 1:
        return [fn(item) for item in values]
    results: list[Any] = [None] * len(values)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(fn, item): index for index, item in enumerate(values)}
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    return results
