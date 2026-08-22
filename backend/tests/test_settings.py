"""
Tests for V9.7 settings store + settings API.
Verifies the bug fix: model selection must follow the settings store,
not a stale env var.
"""
import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUX_SETTINGS_PATH", str(tmp_path / "settings.json"))
    monkeypatch.setenv("NEXUX_DB_PATH", str(tmp_path / "jobs.db"))
    import main
    from utils import settings_store
    settings_store.reset_loaded()
    settings_store._path = settings_store.Path(str(tmp_path / "settings.json"))
    with TestClient(main.app) as c:
        yield c
    settings_store.reset_loaded()


class TestSettingsAPI:
    def test_get_defaults(self, client):
        r = client.get("/api/settings")
        assert r.status_code == 200
        body = r.json()
        assert body["settings"]["transcription_model"] == "small"
        assert set(body["variants"].keys()) == {"small", "base", "large-v3"}
        assert "HF_TOKEN_set" in body["env"]

    def test_patch_persists(self, client):
        r = client.patch("/api/settings", json={"transcription_model": "base"})
        assert r.status_code == 200
        assert r.json()["settings"]["transcription_model"] == "base"
        # survives a fresh read
        r2 = client.get("/api/settings")
        assert r2.json()["settings"]["transcription_model"] == "base"

    def test_patch_rejects_unknown_key(self, client):
        r = client.patch("/api/settings", json={"not_a_setting": 1})
        assert r.status_code == 400

    def test_patch_rejects_bad_model(self, client):
        r = client.patch("/api/settings", json={"transcription_model": "turbo-max"})
        assert r.status_code == 400

    def test_patch_empty_is_400(self, client):
        r = client.patch("/api/settings", json={})
        assert r.status_code == 400

    def test_reset(self, client):
        client.patch("/api/settings", json={"transcription_model": "large-v3"})
        r = client.delete("/api/settings/reset")
        assert r.status_code == 200
        assert r.json()["settings"]["transcription_model"] == "small"


class TestModelEndpoints:
    def test_list_models(self, client):
        r = client.get("/api/settings/models")
        assert r.status_code == 200
        body = r.json()
        assert len(body["models"]) == 3
        assert all(m["downloaded"] is False for m in body["models"])

    def test_preload_rejects_unknown_variant(self, client):
        r = client.post("/api/settings/models/preload", json={"variant": "nope"})
        assert r.status_code == 400

    def test_preload_unknown_job_404(self, client):
        r = client.get("/api/settings/models/preload/preload_nothing")
        assert r.status_code == 404
