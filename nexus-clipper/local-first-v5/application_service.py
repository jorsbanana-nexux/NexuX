from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, HTTPException

from analysis_world_service import build_and_persist_world, load_world, world_path
from canonical_v6_pipeline import run_generation
from contracts import CompatJob, GenerateRequest
from publishing_analytics import record_analytics_event
from runtime_adapter import CanonicalRuntime, default_runtime
from ui_contract import canonicalize_fronted_values
from ui_contract_validation import validate_generate_request


class CanonicalApplicationService:
    """Owns canonical request validation and job lifecycle."""

    def __init__(self, runtime: CanonicalRuntime | None = None) -> None:
        self.runtime = runtime or default_runtime()
        self.analytics_root = self.runtime.data_dir / "analytics"

    def read_job(self, job_id: str) -> dict[str, Any]:
        job = self.runtime.read_job(job_id)
        if job.get("status") == "completed" and isinstance(job.get("analysis_world"), dict):
            return job
        if job.get("status") == "completed":
            try:
                world, path = self.sync_analysis_world(job)
                job["analysis_world"] = {"schema_version": world.schema_version, "path": str(path), "modalities": sorted(world.modalities)}
                self.runtime.set_job(job, analysis_world=job["analysis_world"])
            except (OSError, ValueError, TypeError):
                # World synchronization must not corrupt an otherwise valid completed job.
                pass
        return job

    def sync_analysis_world(self, job: dict[str, Any]) -> tuple[Any, Path]:
        candidates = job.get("candidates") or []
        audio_profiles = {
            str(candidate.get("id")): candidate.get("audio_profile")
            for candidate in candidates
            if isinstance(candidate, dict) and isinstance(candidate.get("audio_profile"), dict)
        }
        render_meta = job.get("render_meta") or []
        audio_profiles.update({
            str(item.get("candidate_id")): item.get("audio_profile")
            for item in render_meta
            if isinstance(item, dict) and isinstance(item.get("audio_profile"), dict)
        })
        vision = job.get("vision") if isinstance(job.get("vision"), dict) else {}
        media = job.get("meta") if isinstance(job.get("meta"), dict) else {}
        provenance = {
            "world": "analysis_world:v2",
            "media": "job.meta",
            "transcript": "job.transcript",
            "audio": "candidate.audio_profile/render_meta.audio_profile",
            "vision": "job.vision",
            "candidates": "job.candidates",
            "editorial": "job.editorial_decision",
        }
        return build_and_persist_world(
            self.runtime.jobs_dir,
            job_id=str(job["job_id"]),
            media=media,
            transcript=job.get("transcript") or {},
            audio_profiles=audio_profiles,
            scenes=vision.get("scenes") or [],
            subjects=vision.get("subject_samples") or [],
            candidates=candidates,
            editorial=job.get("editorial_decision") or {},
            provenance=provenance,
            confidence={"world": 1.0},
        )

    def get_analysis_world(self, job_id: str) -> dict[str, Any]:
        job = self.read_job(job_id)
        path = world_path(self.runtime.jobs_dir, job_id)
        if not path.exists():
            raise HTTPException(404, "AnalysisWorld not available")
        return load_world(self.runtime.jobs_dir, job_id)

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
            "analysis_world": None,
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
            if path.name.endswith(".analysis-world.json"):
                continue
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
        return Path(job.get("output_path", ""))
