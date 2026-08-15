from fastapi.testclient import TestClient

from canonical_api import app


client = TestClient(app)


def test_root_declares_canonical_runtime_and_no_broll():
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["canonical_runtime"] is True
    assert body["broll"] is False


def test_health_exposes_local_first_contract():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["canonical_runtime"] is True
    assert body["broll"] is False


def test_styles_never_advertise_broll():
    response = client.get("/api/styles")
    assert response.status_code == 200
    body = response.json()
    assert body["broll"] is False
    assert "2:3" in body["aspect_ratios"]
    assert "21:9" in body["aspect_ratios"]


def test_invalid_job_id_is_rejected():
    response = client.get("/api/job/not-a-real-job-id")
    assert response.status_code in {404, 422}
