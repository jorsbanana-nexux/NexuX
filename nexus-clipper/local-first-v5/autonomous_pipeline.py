"""Production orchestration boundary for NexuX autonomous editing.

The orchestrator composes existing capabilities without owning their media implementations.
Each stage is explicit, observable, cancellable, and provenance-aware. Callers inject concrete
stage functions so the control plane remains testable and does not fabricate success.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Mapping

SCHEMA_VERSION = "1.0"


class PipelineStage(str, Enum):
    INGEST = "ingest"
    TRANSCRIBE = "transcribe"
    ANALYZE = "analyze"
    REASON = "reason"
    PLAN = "plan"
    DIRECT = "direct"
    RENDER = "render"
    CRITIC = "critic"
    REVISE = "revise"
    PUBLISH = "publish"
    FEEDBACK = "feedback"


@dataclass(frozen=True)
class StageResult:
    stage: PipelineStage
    status: str
    output: Mapping[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    provenance: tuple[str, ...] = ()
    error: str | None = None

    def validate(self) -> "StageResult":
        if self.status not in {"completed", "skipped", "failed"}:
            raise ValueError("invalid stage status")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be in [0,1]")
        return self


@dataclass(frozen=True)
class AutonomousRun:
    run_id: str
    job_id: str
    schema_version: str = SCHEMA_VERSION
    status: str = "created"
    current_stage: PipelineStage | None = None
    stages: tuple[StageResult, ...] = ()
    started_at: str = ""
    finished_at: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def with_stage(self, result: StageResult, *, status: str | None = None) -> "AutonomousRun":
        result.validate()
        new_status = status or ("failed" if result.status == "failed" else "running")
        return AutonomousRun(
            run_id=self.run_id,
            job_id=self.job_id,
            schema_version=self.schema_version,
            status=new_status,
            current_stage=result.stage,
            stages=self.stages + (result,),
            started_at=self.started_at,
            finished_at=self.finished_at,
            metadata=dict(self.metadata),
        )

    def finish(self, status: str) -> "AutonomousRun":
        if status not in {"completed", "failed", "cancelled", "review"}:
            raise ValueError("invalid terminal status")
        return AutonomousRun(
            run_id=self.run_id,
            job_id=self.job_id,
            schema_version=self.schema_version,
            status=status,
            current_stage=self.current_stage,
            stages=self.stages,
            started_at=self.started_at,
            finished_at=datetime.now(timezone.utc).isoformat(),
            metadata=dict(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "job_id": self.job_id,
            "status": self.status,
            "current_stage": self.current_stage.value if self.current_stage else None,
            "stages": [
                {
                    "stage": item.stage.value,
                    "status": item.status,
                    "output": dict(item.output),
                    "confidence": item.confidence,
                    "provenance": list(item.provenance),
                    "error": item.error,
                }
                for item in self.stages
            ],
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "metadata": dict(self.metadata),
        }


StageFn = Callable[[Mapping[str, Any]], Mapping[str, Any]]


class AutonomousPipeline:
    """Sequential production control plane with explicit failure and cancellation semantics."""

    def __init__(self, stages: Mapping[PipelineStage, StageFn]) -> None:
        self._stages = dict(stages)

    def run(
        self,
        *,
        run_id: str,
        job_id: str,
        context: Mapping[str, Any] | None = None,
        cancel: Callable[[], bool] | None = None,
    ) -> AutonomousRun:
        now = datetime.now(timezone.utc).isoformat()
        run = AutonomousRun(run_id=run_id, job_id=job_id, started_at=now, status="running")
        state: dict[str, Any] = dict(context or {})

        ordered = tuple(PipelineStage)
        for stage in ordered:
            if cancel and cancel():
                return run.finish("cancelled")
            fn = self._stages.get(stage)
            if fn is None:
                continue
            try:
                result = dict(fn(state) or {})
                confidence = float(result.pop("confidence", 1.0))
                provenance = tuple(str(x) for x in result.pop("provenance", (stage.value,)))
                stage_result = StageResult(stage, "completed", result, confidence, provenance)
                run = run.with_stage(stage_result)
                state.update(result)
            except Exception as exc:  # noqa: BLE001 - boundary must convert failures into run state
                stage_result = StageResult(stage, "failed", {}, 0.0, (stage.value,), str(exc))
                run = run.with_stage(stage_result, status="failed")
                return run.finish("failed")

        return run.finish("completed")
