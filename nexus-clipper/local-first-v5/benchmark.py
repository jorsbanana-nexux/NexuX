from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    video: str
    reference_clips: list[dict]


@dataclass
class Metrics:
    candidates: int = 0
    top1_overlap: float = 0.0
    mean_best_overlap: float = 0.0
    average_duration: float = 0.0


def interval_iou(a: dict, b: dict) -> float:
    start = max(float(a["start"]), float(b["start"]))
    end = min(float(a["end"]), float(b["end"]))
    inter = max(0.0, end - start)
    union = max(float(a["end"]), float(b["end"])) - min(float(a["start"]), float(b["start"]))
    return inter / union if union > 0 else 0.0


def evaluate_candidates(candidates: list[dict], reference_clips: list[dict]) -> Metrics:
    if not candidates:
        return Metrics()
    best = []
    for candidate in candidates:
        best.append(max((interval_iou(candidate, ref) for ref in reference_clips), default=0.0))
    return Metrics(
        candidates=len(candidates),
        top1_overlap=best[0] if best else 0.0,
        mean_best_overlap=sum(best) / len(best),
        average_duration=sum(float(c["duration"]) for c in candidates) / len(candidates),
    )


def load_cases(path: Path) -> list[BenchmarkCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [BenchmarkCase(**item) for item in payload]


def save_report(path: Path, reports: dict[str, Metrics]) -> None:
    path.write_text(json.dumps({k: asdict(v) for k, v in reports.items()}, indent=2), encoding="utf-8")
