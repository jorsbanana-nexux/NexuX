from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, HTTPException

from canonical_v6_pipeline import run_generation
from contracts import CompatJob, GenerateRequest
from publishing_analytics import record_analytics_event
from runtime_adapter import CanonicalRuntime, default_runtime
from ui_contract import canonicalize_fronted_values
from ui_contract_validation import validate_generate_request


class CanonicalApplicationService:
    """Owns canonical request validation and job lifecycle.

    HTTP handlers should delegate here rather than coordinating engine internals.
    """

    def __init__(self, runtime: CanonicalRuntime | None = None) -> None:
        self.runtime = runtime or default_runtime()
        self.analytics_root = self.runtime.data_dir / "analytics"

    def read_job(self, job_id: str) -> dict[str, Any]:
        return self.runtime.read_job(job_id)

    def create_job(self, request: GenerateRequest) -> CompatJob:
        request.subtitle_style, request.animation = canonicalize_fronted_values(
            request.subtitle_style, request.animation
        )
        validate_generate_request(request)
        job_id = uuid.uuid4().hex
        job = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0.0,
            "stage": "queued",
            "output_path": None,
            "error": None,
            "clips": [],
            "broll": False,
            "render_meta": [],
            "analysis_bundle": None,
            "revision": 0,
            "critic": None,
            "publish_plan": None,
            "editorial_decision": None,
        }
        self.runtime.write_job(job)
        self.runtime.cancel_flags[job_id] = False
        record_analytics_event(
            self.analytics_root,
            job_id,
            {
                "event": "generation_queued",
                "clip_count": request.clip_count,
                "aspect_ratio": request.aspect_ratio,
                "genre": request.genre,
                "prompt": bool(request.clip_prompt),
                "voice_over": request.voice_over,
            },
        )
        return CompatJob(**job)

    def enqueue(self, request: GenerateRequest, background: BackgroundTasks) -> CompatJob:
        job = self.create_job(request)
        background.add_task(run_generation, job.job_id, request, self.runtime)
        return job

    def cancel(self, job_id: str) -> dict[str, str]:
        job = self.runtime.read_job(job_id)
        if job.get("status") in {"completed", "failed", "cancelled"}:
            raise HTTPException(400, f"Job already {job['status']}")
        self.runtime.cancel_flags[job_id] = True
        self.runtime.set_job(job, status="cancelled", stage="cancelled", error="Cancelled by user")
        record_analytics_event(self.analytics_root, job_id, {"event": "generation_cancelled"})
        return {"job_id": job_id, "status": "cancelled"}

    def list_jobs(self, status: str | None = None) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        for path in self.runtime.jobs_dir.glob("*.json"):
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if status and item.get("status") != status:
                continue
            items.append(CompatJob(**item).model_dump())
        items.sort(key=lambda item: item.get("job_id", ""), reverse=True)
        return {"total": len(items), "jobs": items}

    @staticmethod
    def output_path(job: dict[str, Any]) -> Path:
        path = Path(job.get("output_path", ""))
        return path
