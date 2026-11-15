import json

from fastapi.testclient import TestClient

from api.main import app
from tests.test_api import BODY

client = TestClient(app)


def test_compare_is_logged_without_coordinates(tmp_path, monkeypatch):
    log = tmp_path / "usage.jsonl"
    monkeypatch.setenv("USAGE_LOG", str(log))
    client.post("/compare", json={**BODY, "location": None, "lat": 20.36, "lon": 77.12})
    row = json.loads(log.read_text().splitlines()[0])
    assert row["location"] == "gps" and row["priorities"] == ["water_saving"]
    assert "lat" not in row and "lon" not in row and row["latency_ms"] >= 0


def test_stats_needs_token_and_summarises(tmp_path, monkeypatch):
    monkeypatch.setenv("USAGE_LOG", str(tmp_path / "usage.jsonl"))
    monkeypatch.setenv("ADMIN_TOKEN", "s3cret")
    client.post("/compare", json=BODY)
    client.post("/compare", json=BODY)
    assert client.get("/admin/stats").status_code == 401
    r = client.get("/admin/stats", headers={"x-admin-token": "s3cret"})
    s = r.json()
    assert s["requests"] == 2 and s["by_location"] == {"akola": 2}
    assert s["by_priority"] == {"water_saving": 2} and s["p50_latency_ms"] >= 0


def test_stats_disabled_when_no_token_configured(monkeypatch):
    monkeypatch.delenv("ADMIN_TOKEN", raising=False)
    assert client.get("/admin/stats").status_code == 404
