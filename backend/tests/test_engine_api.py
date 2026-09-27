"""
API Integration Tests for Anomaly Detection Pipeline Endpoint
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_api_detection_run_default():
    response = client.post("/api/detection/run", json={})
    assert response.status_code == 200
    data = response.json()

    assert "execution_time_ms" in data
    assert data["execution_time_ms"] > 0
    assert data["lead_time_hours"] == 24
    assert data["total_anomalies_detected"] > 0
    assert data["total_footprints_extracted"] > 0
    assert len(data["events"]) > 0
    assert len(data["footprints"]) > 0
    assert data["is_simulated"] == True
    assert "SYNTHETIC" in data["data_provenance"]

    # Check first event properties
    first_event = data["events"][0]
    assert "id" in first_event
    assert "name" in first_event
    assert "type" in first_event
    assert "severity" in first_event
    assert "geometry" in first_event
    assert first_event["geometry"]["type"] == "Polygon"
    assert "primary_variable" in first_event


def test_api_detection_run_custom_params():
    payload = {
        "lead_time_hours": 48,
        "min_area_km2": 5000.0,
        "connectivity": 4,
        "seed": 99,
    }
    response = client.post("/api/detection/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["lead_time_hours"] == 48
    # Footprints must all respect minimum area
    for fp in data["footprints"]:
        assert fp["estimated_area_km2"] >= 5000.0


def test_api_detection_run_validation_invalid_lead_time():
    # lead_time_hours > 240
    response = client.post("/api/detection/run", json={"lead_time_hours": 500})
    assert response.status_code == 422


def test_api_detection_run_validation_invalid_connectivity():
    # connectivity must be 4 or 8
    response = client.post("/api/detection/run", json={"connectivity": 6})
    assert response.status_code == 422


def test_api_detection_run_validation_negative_area():
    response = client.post("/api/detection/run", json={"min_area_km2": -50.0})
    assert response.status_code == 422
