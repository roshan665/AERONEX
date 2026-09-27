"""
Tests for Health & Root Endpoints
"""


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "AeroNex" in data["service"]
    assert data["documentation"] == "/docs"
    assert "DEMO" in data["data_mode"]


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert data["is_simulated"] is True
    assert data["subsystems"]["api_gateway"] == "ONLINE"
    assert data["subsystems"]["anomaly_engine"] == "ONLINE"
