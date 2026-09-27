"""
Tests for Metadata and System Specification Endpoint
"""


def test_metadata_endpoint(client):
    response = client.get("/api/metadata")
    assert response.status_code == 200
    data = response.json()
    assert "AeroNex" in data["system_name"]
    assert data["data_provenance"] == "DEMO_SYNTHETIC_DATASET"
    assert data["is_simulated"] is True
    assert "grid_specifications" in data
    assert data["grid_specifications"]["spacing_degrees"] == 0.25
    assert "methodology" in data
    assert "ERA5" in data["methodology"]["climatology_reference"]
