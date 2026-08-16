"""Single entrypoint contract for the autonomous production pipeline.

The entrypoint intentionally requires concrete stage implementations. It never reports
success when a production capability is missing. Legacy executors can be supplied by
an adapter during migration, but the orchestration lifecycle stays canonical.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from autonomous_pipeline import AutonomousPipeline, AutonomousRun, PipelineStage, StageFn


@dataclass(frozen=True)
class ProductionPipelineConfig:
    required_stages: tuple[PipelineStage, ...] = (
        PipelineStage.INGEST,
        PipelineStage.TRANSCRIBE,
        PipelineStage.ANALYZE,
        PipelineStage.REASON,
        PipelineStage.PLAN,
        PipelineStage.DIRECT,
        PipelineStage.RENDER,
        PipelineStage.CRITIC,
        PipelineStage.REVISE,
        PipelineStage.PUBLISH,
        PipelineStage.FEEDBACK,
    )

    def validate(self, stages: Mapping[PipelineStage, StageFn]) -> None:
        missing = [stage.value for stage in self.required_stages if stage not in stages]
        if missing:
            raise RuntimeError(f"production pipeline is incomplete; missing stages: {', '.join(missing)}")


def execute_production_run(
    *,
    run_id: str,
    job_id: str,
    stages: Mapping[PipelineStage, StageFn],
    context: Mapping[str, Any] | None = None,
    cancel: Callable[[], bool] | None = None,
    config: ProductionPipelineConfig | None = None,
) -> AutonomousRun:
    cfg = config or ProductionPipelineConfig()
    cfg.validate(stages)
    return AutonomousPipeline(stages).run(
        run_id=run_id,
        job_id=job_id,
        context=context,
        cancel=cancel,
    )
