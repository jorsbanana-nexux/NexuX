from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException

from job_store import read as atomic_read, recover_interrupted, update as atomic_update
from process_supervisor import terminate as terminate_process


class CancellationRegistry(dict[str, bool]):
    """Sticky cancellation flags with process-level interruption hooks."""

    def __setitem__(self, job_id: str, value: bool) -> None:
        super().__setitem__(job_id, value)
        if value:
            for stage in ("download", "transcribe", "render"):
                terminate_process(f"{stage}:{job_id}")


class JobStateService:
    """Canonical adapter over the existing durable job store."""

    def __init__(self, jobs_dir: Path) -> None:
        self.jobs_dir = jobs_dir
        self.cancel_flags = CancellationRegistry()

    @staticmethod
    def validate_job_id(job_id: str) -> None:
        if not job_id or len(job_id) != 32 or any(c not in "0123456789abcdef" for c in job_id):
            raise HTTPException(422, "Invalid job_id")

    def read(self, job_id: str) -> dict[str, Any]:
        self.validate_job_id(job_id)
        path = self.jobs_dir / f"{job_id}.json"
        if not path.exists():
            raise HTTPException(404, "Job not found")
        return atomic_read(self.jobs_dir, job_id)

    def write(self, job: dict[str, Any]) -> dict[str, Any]:
        return atomic_update(self.jobs_dir, job)

    def set(self, job: dict[str, Any], **updates: Any) -> dict[str, Any]:
        current = atomic_update(self.jobs_dir, job, **updates)
        job.clear()
        job.update(current)
        return job

    def recover(self) -> None:
        recover_interrupted(self.jobs_dir)

    def list(self, status: str | None = None) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for path in self.jobs_dir.glob("*.json"):
            try:
                item = atomic_read(self.jobs_dir, path.stem)
            except (OSError, ValueError, HTTPException):
                continue
            if status and item.get("status") != status:
                continue
            items.append(item)
        items.sort(key=lambda item: item.get("job_id", ""), reverse=True)
        return items
