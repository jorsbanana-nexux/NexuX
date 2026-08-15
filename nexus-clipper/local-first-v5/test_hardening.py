from __future__ import annotations

import json
from pathlib import Path

from job_store import read, recover_interrupted, write
from transcription import _transcribe_file


def test_job_store_writes_revision_atomically(tmp_path: Path):
    root = tmp_path / "jobs"
    root.mkdir()
    job = {"job_id": "a" * 32, "status": "queued"}
    write(root, job)
    first = read(root, job["job_id"])
    assert first["revision"] == 1
    write(root, {**first, "status": "processing"})
    second = read(root, job["job_id"])
    assert second["revision"] == 2
    assert second["status"] == "processing"
    assert not list(root.glob(".*.tmp"))


def test_job_store_recovers_nonterminal_jobs(tmp_path: Path):
    root = tmp_path / "jobs"
    root.mkdir()
    path = root / f"{'b' * 32}.json"
    path.write_text(json.dumps({"job_id": "b" * 32, "status": "processing"}), encoding="utf-8")
    assert recover_interrupted(root) == 1
    state = read(root, "b" * 32)
    assert state["status"] == "interrupted"
    assert state["stage"] == "recovery_required"


def test_transcript_chunk_offsets_are_absolute(monkeypatch, tmp_path: Path):
    class Segment:
        def __init__(self, start: float, end: float):
            self.start, self.end, self.text = start, end, "hello"
            self.words = []

    class Info:
        language = "en"

    class Model:
        def transcribe(self, *_args, **_kwargs):
            return iter([Segment(0.0, 1.0)]), Info()

    segments, language = _transcribe_file(Model(), tmp_path / "dummy.wav", "en", 900.0, 4)
    assert language == "en"
    assert segments[0]["id"] == 4
    assert segments[0]["start"] == 900.0
    assert segments[0]["end"] == 901.0
