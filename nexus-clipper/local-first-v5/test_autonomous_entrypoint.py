from __future__ import annotations

import pytest

from autonomous_entrypoint import ProductionPipelineConfig, execute_production_run
from autonomous_pipeline import PipelineStage


def _ok(stage: PipelineStage):
    def run(state):
        return {"stage_output": stage.value, "provenance": (stage.value,), "confidence": 1.0}
    return run


def test_entrypoint_rejects_incomplete_production_wiring() -> None:
    with pytest.raises(RuntimeError, match="missing stages"):
        execute_production_run(run_id="r1", job_id="j1", stages={})


def test_entrypoint_runs_all_declared_production_stages() -> None:
    stages = {stage: _ok(stage) for stage in ProductionPipelineConfig().required_stages}
    run = execute_production_run(run_id="r2", job_id="j2", stages=stages)
    assert run.status == "completed"
    assert [item.stage for item in run.stages] == list(ProductionPipelineConfig().required_stages)
