from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
BODY = {"location": "akola", "current_rotation": "soybean_fallow", "priorities": ["water_saving"],
        "constraints": {"water_availability": "low", "equipment": "basic", "market": "mandi"}}


def test_health_endpoint_is_ok():
    r = client.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_compare_returns_four_strategies_for_a_preset_location():
    r = client.post("/compare", json=BODY)
    assert r.status_code == 200
    body = r.json()
    assert body["served"] is True
    assert [s["id"] for s in body["strategies"]] == ["S0", "S1", "S2", "S3"]
    assert "does not replace" in body["disclaimer"]


def test_compare_accepts_gps_coordinates_near_a_preset():
    r = client.post("/compare", json={**BODY, "location": None, "lat": 20.36, "lon": 77.12})
    assert r.status_code == 200
    assert r.json()["location"]["nearest"] == "washim"


def test_a_gps_point_we_cannot_serve_gets_a_clear_message_not_an_error():
    r = client.post("/compare", json={**BODY, "location": None, "lat": 21.7, "lon": 76.1})
    assert r.status_code == 200
    assert r.json()["served"] is False and r.json()["reason"]


def test_missing_location_is_rejected():
    r = client.post("/compare", json={"priorities": []})
    assert r.status_code == 422


def test_unknown_priority_is_rejected_with_a_message():
    r = client.post("/compare", json={**BODY, "priorities": ["shiny"]})
    assert r.status_code == 422
    assert "shiny" in r.text


def test_unknown_location_name_is_rejected():
    r = client.post("/compare", json={**BODY, "location": "atlantis"})
    assert r.status_code == 422


def test_unknown_rotation_is_rejected():
    r = client.post("/compare", json={**BODY, "current_rotation": "banana"})
    assert r.status_code == 422
