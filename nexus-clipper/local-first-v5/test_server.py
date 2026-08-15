from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from captions import PRESETS
from compositor import spec_for_aspect_ratio
from server import CANCEL_FLAGS, GenerateRequest, _run_generation, app


def test_aspect_specs():
    assert (spec_for_aspect_ratio("9:16").width, spec_for_aspect_ratio("9:16").height) == (1080, 1920)
    assert (spec_for_aspect_ratio("16:9").width, spec_for_aspect_ratio("16:9").height) == (1920, 1080)
    assert (spec_for_aspect_ratio("1:1").width, spec_for_aspect_ratio("1:1").height) == (1080, 1080)
    assert (spec_for_aspect_ratio("4:5").width, spec_for_aspect_ratio("4:5").height) == (1080, 1350)


def test_health_contract():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["canonical_engine"] == "local-first-v5"
    assert data["broll"] is False


def test_styles_contract():
    client = TestClient(app)
    response = client.get("/api/styles")
    assert response.status_code == 200
    data = response.json()
    assert "9:16" in data["aspect_ratios"]
    assert "16:9" in data["aspect_ratios"]
    assert data["broll"] is False
    advertised = {x["id"] for x in data["subtitle_styles"]}
    assert advertised.issubset(PRESETS.keys())
    assert {"hormozi", "mrbeast", "aliabdaal", "minimalist", "gaming", "cinematic", "neon", "typewriter", "tiktok_viral", "documentary", "comedy", "horror", "motivational", "educational", "custom"}.issubset(advertised)


def test_generate_request_rejects_unrenderable_durations():
    assert GenerateRequest(youtube_url="https://youtu.be/example", target_duration=20).target_duration == 20
    for invalid in (15, 65, 180):
        try:
            GenerateRequest(youtube_url="https://youtu.be/example", target_duration=invalid)
        except Exception:
            pass
        else:
            raise AssertionError(f"duration {invalid} should be rejected")


def test_cancelled_queued_job_cannot_be_resurrected(tmp_path, monkeypatch):
    job_id = uuid.uuid4().hex
    job_dir = tmp_path / "jobs"
    job_dir.mkdir()
    job_path = job_dir / f"{job_id}.json"
    job_path.write_text(json.dumps({"job_id": job_id, "status": "cancelled"}), encoding="utf-8")

    import server
    monkeypatch.setattr(server, "JOBS", job_dir)
    req = GenerateRequest(youtube_url="https://youtu.be/example", target_duration=45)

    asyncio.run(_run_generation(job_id, req))
    assert json.loads(job_path.read_text(encoding="utf-8"))["status"] == "cancelled"
    assert job_id not in CANCEL_FLAGS
