"""
Tests for Forecast Time-Series Endpoints
"""


def test_forecasts_default_temperature(client):
    response = client.get("/api/forecasts")
    assert response.status_code == 200
    data = response.json()
    assert data["variable"] == "temperature"
    assert data["unit"] == "°C"
    assert len(data["timeline"]) == 10
    assert data["timeline"][0]["day"] == "Day 1"
    assert data["timeline"][9]["day"] == "Day 10"
    assert data["is_simulated"] is True


def test_forecasts_variable_wind(client):
    response = client.get("/api/forecasts?variable=wind")
    assert response.status_code == 200
    data = response.json()
    assert data["variable"] == "wind"
    assert data["unit"] == "km/h"
    assert len(data["timeline"]) == 10


def test_forecasts_lead_day_filter(client):
    response = client.get("/api/forecasts?variable=pressure&lead_day=3")
    assert response.status_code == 200
    data = response.json()
    assert data["variable"] == "pressure"
    assert len(data["timeline"]) == 1
    assert data["timeline"][0]["lead_day"] == 3
    assert data["timeline"][0]["day"] == "Day 3"


def test_forecasts_invalid_variable(client):
    response = client.get("/api/forecasts?variable=unknown_var")
    assert response.status_code == 422
    data = response.json()
    assert "Unsupported meteorological variable" in data["detail"]


def test_forecasts_invalid_lead_day(client):
    response = client.get("/api/forecasts?lead_day=15")
    assert response.status_code == 422
    data = response.json()
    assert "Request validation failed" in data["detail"] or "out of bounds" in data["detail"]


def test_forecast_run_metadata_success(client):
    response = client.get("/api/forecasts/GFS-20250426-00Z")
    assert response.status_code == 200
    data = response.json()
    assert data["forecast_id"] == "GFS-20250426-00Z"
    assert data["spatial_resolution_deg"] == 0.25
    assert len(data["available_lead_times_hours"]) == 10


def test_forecast_run_metadata_not_found(client):
    response = client.get("/api/forecasts/ECMWF-INVALID-00Z")
    assert response.status_code == 404
    data = response.json()
    assert "does not exist" in data["detail"]
