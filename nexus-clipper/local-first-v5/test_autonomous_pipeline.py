from __future__ import annotations

from autonomous_pipeline import AutonomousPipeline, PipelineStage


def test_pipeline_runs_registered_stages_in_order() -> None:
    seen: list[str] = []

    def make(stage: PipelineStage):
        def _run(state):
            seen.append(stage.value)
            return {"value": stage.value, "provenance": (stage.value,), "confidence": 0.9}
        return _run

    stages = {stage: make(stage) for stage in (PipelineStage.INGEST, PipelineStage.REASON, PipelineStage.PLAN, PipelineStage.RENDER, PipelineStage.CRITIC)}
    run = AutonomousPipeline(stages).run(run_id="r1", job_id="j1")

    assert run.status == "completed"
    assert seen == ["ingest", "reason", "plan", "render", "critic"]
    assert all(result.status == "completed" for result in run.stages)
    assert all(result.confidence == 0.9 for result in run.stages)


def test_pipeline_stops_cleanly_on_cancellation() -> None:
    seen: list[str] = []

    def stage(state):
        seen.append("ingest")
        return {"ok": True}

    run = AutonomousPipeline({PipelineStage.INGEST: stage}).run(
        run_id="r2", job_id="j2", cancel=lambda: True
    )

    assert run.status == "cancelled"
    assert not seen


def test_pipeline_converts_stage_exception_to_failed_run() -> None:
    def broken(state):
        raise RuntimeError("render failed")

    run = AutonomousPipeline({PipelineStage.RENDER: broken}).run(run_id="r3", job_id="j3")

    assert run.status == "failed"
    assert run.stages[-1].stage is PipelineStage.RENDER
    assert run.stages[-1].error == "render failed"
    assert run.stages[-1].confidence == 0.0
