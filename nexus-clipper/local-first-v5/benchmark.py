from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    video: str
    reference_clips: list[dict[str, float]]


@dataclass
class Metrics:
    candidates: int = 0
    top1_overlap: float = 0.0
    mean_best_overlap: float = 0.0
    average_duration: float = 0.0
    in_duration_rate: float = 0.0
    non_overlap_rate: float = 0.0
    mean_score: float = 0.0


def interval_iou(a: dict[str, Any], b: dict[str, Any]) -> float:
    start = max(float(a["start"]), float(b["start"]))
    end = min(float(a["end"]), float(b["end"]))
    inter = max(0.0, end - start)
    union = max(float(a["end"]), float(b["end"])) - min(float(a["start"]), float(b["start"]))
    return inter / union if union > 0 else 0.0


def evaluate_candidates(
    candidates: list[dict[str, Any]],
    reference_clips: list[dict[str, float]],
    min_duration: float = 20.0,
    max_duration: float = 60.0,
) -> Metrics:
    if not candidates:
        return Metrics()
    ranked = sorted(candidates, key=lambda item: float(item.get("viral_score", 0.0)), reverse=True)
    best_overlaps = [max((interval_iou(candidate, ref) for ref in reference_clips), default=0.0) for candidate in ranked]
    durations = [max(0.0, float(c.get("end", 0.0)) - float(c.get("start", 0.0))) for c in ranked]
    pair_count = 0
    overlap_count = 0
    for i, left in enumerate(ranked):
        for right in ranked[i + 1 :]:
            pair_count += 1
            if interval_iou(left, right) > 0.20:
                overlap_count += 1
    return Metrics(
        candidates=len(ranked),
        top1_overlap=best_overlaps[0] if best_overlaps else 0.0,
        mean_best_overlap=sum(best_overlaps) / len(best_overlaps) if best_overlaps else 0.0,
        average_duration=sum(durations) / len(durations) if durations else 0.0,
        in_duration_rate=(sum(min_duration <= d <= max_duration for d in durations) / len(durations)) if durations else 0.0,
        non_overlap_rate=1.0 - (overlap_count / pair_count if pair_count else 0.0),
        mean_score=sum(float(c.get("viral_score", 0.0)) for c in ranked) / len(ranked),
    )


def load_cases(path: Path) -> list[BenchmarkCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [BenchmarkCase(**item) for item in payload]


def save_report(path: Path, reports: dict[str, Metrics]) -> None:
    path.write_text(json.dumps({key: asdict(value) for key, value in reports.items()}, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="NexuX V5 deterministic candidate benchmark")
    parser.add_argument("json_file", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.json_file.read_text(encoding="utf-8"))
    candidates = payload.get("candidates", payload if isinstance(payload, list) else [])
    refs = payload.get("reference_clips", []) if isinstance(payload, dict) else []
    print(json.dumps(asdict(evaluate_candidates(candidates, refs)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
