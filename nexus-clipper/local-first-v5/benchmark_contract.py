from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

SCHEMA_VERSION = "1.0"
VALID_SYSTEMS = frozenset({"nexux", "baseline", "human", "external"})
VALID_METRICS = frozenset({"top1_iou", "recall_at_k", "mean_best_iou", "duration_compliance", "diversity", "human_preference", "editorial_failure_rate", "technical_failure_rate", "caption_accuracy", "av_sync_failure_rate"})

def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))

@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    source_id: str
    system: str
    clips: tuple[Mapping[str, Any], ...] = ()
    reference_clips: tuple[Mapping[str, Any], ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    def validate(self) -> "BenchmarkCase":
        if not self.case_id or not self.source_id: raise ValueError("case_id and source_id are required")
        if self.system not in VALID_SYSTEMS: raise ValueError(f"unsupported benchmark system: {self.system}")
        return self

@dataclass(frozen=True)
class BenchmarkReport:
    schema_version: str
    run_id: str
    metric_values: Mapping[str, float]
    case_count: int
    metadata: Mapping[str, Any] = field(default_factory=dict)
    def validate(self) -> "BenchmarkReport":
        if self.schema_version != SCHEMA_VERSION: raise ValueError(f"unsupported benchmark schema: {self.schema_version}")
        if not self.run_id or self.case_count < 0: raise ValueError("invalid benchmark report identity/count")
        for name, value in self.metric_values.items():
            if name not in VALID_METRICS: raise ValueError(f"unsupported benchmark metric: {name}")
            _clamp(value)
        return self
    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {"schema_version": self.schema_version, "run_id": self.run_id, "metric_values": {k: round(_clamp(v), 6) for k, v in self.metric_values.items()}, "case_count": self.case_count, "metadata": dict(self.metadata)}

def build_benchmark_report(run_id: str, metrics: Mapping[str, float], *, case_count: int, metadata: Mapping[str, Any] | None = None) -> BenchmarkReport:
    return BenchmarkReport(SCHEMA_VERSION, run_id, dict(metrics), int(case_count), dict(metadata or {})).validate()
