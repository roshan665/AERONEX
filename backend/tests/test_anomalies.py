"""
Tests for Anomaly Catalog & Detail Endpoints
"""


def test_get_all_anomalies(client):
    response = client.get("/api/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 5
    assert data["count"] >= 5
    assert len(data["events"]) >= 5
    assert data["is_simulated"] is True


def test_filter_anomalies_by_category(client):
    response = client.get("/api/anomalies?category_key=cyclone")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert all(e["category_key"] == "cyclone" for e in data["events"])


def test_filter_anomalies_by_severity(client):
    response = client.get("/api/anomalies?severity=High")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 2
    assert all(e["severity"] == "High" for e in data["events"])


def test_filter_anomalies_by_forecast_day(client):
    response = client.get("/api/anomalies?forecast_day=3")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert all(3 in e["forecast_days"] for e in data["events"])


def test_filter_anomalies_by_min_area(client):
    response = client.get("/api/anomalies?min_area_km2=400000")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert all(e["estimated_area_km2"] >= 400000 for e in data["events"])


def test_get_anomaly_detail_success(client):
    response = client.get("/api/anomalies/evt-001")
    assert response.status_code == 200
    data = response.json()
    assert data["event"]["id"] == "evt-001"
    assert data["event"]["name"] == "Tropical Cyclone"
    assert len(data["footprint_polygon"]) >= 4
    assert len(data["forecast_track"]) >= 3
    assert len(data["trajectory_steps"]) >= 3
    assert "max_wind_speed_ms" in data["meteorological_metrics"]


def test_get_anomaly_detail_not_found(client):
    response = client.get("/api/anomalies/evt-nonexistent-999")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()
