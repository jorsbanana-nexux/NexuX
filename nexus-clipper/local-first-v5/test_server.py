from __future__ import annotations

from fastapi.testclient import TestClient

from compositor import spec_for_aspect_ratio
from server import app


def test_aspect_specs():
    assert (spec_for_aspect_ratio("9:16").width, spec_for_aspect_ratio("9:16").height) == (1080, 1920)
    assert (spec_for_aspect_ratio("16:9").width, spec_for_aspect_ratio("16:9").height) == (1920, 1080)
    assert (spec_for_aspect_ratio("1:1").width, spec_for_aspect_ratio("1:1").height) == (1080, 1080)


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
    assert {x["id"] for x in data["subtitle_styles"]} == {"karaoke", "pop_line", "deep_diver"}
