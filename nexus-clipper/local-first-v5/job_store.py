from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

_LOCKS: dict[Path, threading.RLock] = {}
_LOCKS_GUARD = threading.Lock()


def _lock(path: Path) -> threading.RLock:
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(path.resolve(), threading.RLock())


def path_for(root: Path, job_id: str) -> Path:
    return root / f"{job_id}.json"


def read(root: Path, job_id: str) -> dict[str, Any]:
    path = path_for(root, job_id)
    with _lock(path):
        return json.loads(path.read_text(encoding="utf-8"))


def write(root: Path, job: dict[str, Any]) -> dict[str, Any]:
    job_id = str(job["job_id"])
    path = path_for(root, job_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(job)
    payload["updated_at"] = time.time()
    payload["revision"] = int(payload.get("revision", 0)) + 1
    with _lock(path):
        fd, tmp_name = tempfile.mkstemp(prefix=f".{job_id}.", suffix=".tmp", dir=str(path.parent))
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, path)
        finally:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass
    return payload


def update(root: Path, job: dict[str, Any], **changes: Any) -> dict[str, Any]:
    job_id = str(job["job_id"])
    path = path_for(root, job_id)
    with _lock(path):
        try:
            current = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            current = dict(job)
        merged = dict(current)
        merged.update(changes)
        if not changes:
            # A caller passing a stale snapshot must not overwrite newer state.
            merged = dict(current)
        if current.get("status") in {"cancelled", "completed", "failed", "interrupted"} and changes.get("status") not in {None, current.get("status")}:
            merged["status"] = current["status"]
            merged["stage"] = current.get("stage", merged.get("stage"))
            if current.get("error"):
                merged["error"] = current["error"]
        return write(root, merged)


def recover_interrupted(root: Path) -> int:
    recovered = 0
    for path in root.glob("*.json"):
        try:
            job = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if job.get("status") not in {"processing", "queued"}:
            continue
        job["status"] = "interrupted"
        job["stage"] = "recovery_required"
        job["error"] = "Worker process stopped before the job reached a terminal state"
        write(root, job)
        recovered += 1
    return recovered
