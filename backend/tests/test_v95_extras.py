"""
NexuX V9.5 — Extras API + Unified Job Registration Tests
=========================================================
Covers the restored V8.5/V9.0 endpoint surface (api_v95_extras.py)
and the /api/v2/generate → job-store integration fix.
Run: python -m pytest tests/test_v95_extras.py -v
"""
import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Fresh env per test; isolated DB, no auth, no real pipeline workers."""
    monkeypatch.setenv("NEXUX_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("NEXUX_API_KEY", "")
    from utils.rate_limiter import rate_limiter as rl
    rl._buckets.clear()

    import main

    # main is module-cached across tests → reset its global job state.
    main.jobs.clear()
    main.cancel_flags.clear()
    main.active_count = 0

    # Stub both workers so background tasks never hit the network/FFmpeg.
    async def fake_process_job(job_id, url, kwargs):
        try:
            main.jobs[job_id]["status"] = "completed"
            main.jobs[job_id]["progress"] = 100
            main._save_job(main.jobs[job_id])
        finally:
            main.active_count = max(0, main.active_count - 1)

    async def fake_mode2_job(job_id, params):
        try:
            main.jobs[job_id]["status"] = "completed"
            main.jobs[job_id]["progress"] = 100
            main._save_job(main.jobs[job_id])
        finally:
            main.active_count = max(0, main.active_count - 1)

    monkeypatch.setattr(main, "_process_job", fake_process_job)
    monkeypatch.setattr(main, "_process_mode2_job", fake_mode2_job)

    from fastapi.testclient import TestClient
    with TestClient(main.app) as c:
        yield c


class TestExtrasEndpoints:
    def test_platforms_lists_tiktok(self, client):
        res = client.get("/api/platforms")
        assert res.status_code == 200
        names = [p["name"] for p in res.json()["platforms"]]
        assert "tiktok" in names

    def test_repair_diagnose_returns_issues(self, client):
        res = client.get("/api/repair/diagnose")
        assert res.status_code == 200
        body = res.json()
        assert "issues" in body
        assert all({"id", "label", "status", "detail"} <= set(i) for i in body["issues"])

    def test_repair_fix_all_shape(self, client):
        res = client.post("/api/repair/fix-all")
        assert res.status_code == 200
        body = res.json()
        assert "fixed" in body and "results" in body

    def test_virality_unknown_job_404(self, client):
        assert client.get("/api/virality/nope").status_code == 404

    def test_hooks_unknown_job_404(self, client):
        assert client.get("/api/hooks/nope").status_code == 404

    def test_caption_quality_unknown_job_404(self, client):
        assert client.get("/api/caption-quality/nope").status_code == 404

    def test_rerender_unknown_job_404(self, client):
        res = client.post("/api/rerender/nope/0", json={"settings": {}})
        assert res.status_code == 404

    def test_overlay_rerender_unknown_job_404(self, client):
        res = client.post("/api/rerender/nope/0/overlays", json={"settings": {}, "overlays": []})
        assert res.status_code == 404


class TestV2JobRegistration:
    def test_v2_podcast_job_is_pollable(self, client):
        res = client.post("/api/v2/generate", json={
            "mode": "podcast",
            "youtube_url": "https://www.youtube.com/watch?v=test123",
            "target_duration": 30,
            "clip_count": 2,
        })
        assert res.status_code == 200
        job_id = res.json()["job_id"]

        job = client.get(f"/api/job/{job_id}")
        assert job.status_code == 200
        assert job.json()["job_id"] == job_id
        assert job.json()["status"] in ("queued", "processing", "completed")

    def test_v2_creative_job_is_pollable(self, client):
        res = client.post("/api/v2/generate", json={
            "mode": "creative",
            "keyword": "motivasi belajar",
            "voice_enabled": False,
            "target_duration": 60,
        })
        assert res.status_code == 200
        job_id = res.json()["job_id"]

        job = client.get(f"/api/job/{job_id}")
        assert job.status_code == 200
        assert job.json()["job_id"] == job_id

    def test_v2_generate_requires_input(self, client):
        res = client.post("/api/v2/generate", json={"mode": "podcast"})
        assert res.status_code == 400

    def test_v2_job_appears_in_jobs_list(self, client):
        res = client.post("/api/v2/generate", json={
            "mode": "podcast",
            "youtube_url": "https://www.youtube.com/watch?v=list123",
        })
        job_id = res.json()["job_id"]

        jobs = client.get("/api/jobs").json()["jobs"]
        assert any(j["job_id"] == job_id for j in jobs)

    def test_v2_job_cancellable(self, client, monkeypatch):
        import main

        async def idle_worker(job_id, params):
            pass  # leave the job in "queued" so it can be cancelled

        monkeypatch.setattr(main, "_process_mode2_job", idle_worker)

        res = client.post("/api/v2/generate", json={
            "mode": "creative",
            "keyword": "cancel me",
        })
        job_id = res.json()["job_id"]

        cancel = client.delete(f"/api/job/{job_id}")
        assert cancel.status_code == 200
        assert cancel.json()["status"] == "cancelled"

    def test_cancel_completed_job_rejected(self, client):
        res = client.post("/api/v2/generate", json={
            "mode": "creative",
            "keyword": "already done",
        })
        job_id = res.json()["job_id"]

        # Fixture worker completes the job synchronously → cancel must 400.
        cancel = client.delete(f"/api/job/{job_id}")
        assert cancel.status_code == 400
