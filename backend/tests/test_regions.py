"""
Tests for Monitored Regions Endpoints
"""


def test_get_regions_list(client):
    response = client.get("/api/regions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 12
    ids = [r["region_id"] for r in data]
    assert "western_indian_ocean" in ids
    assert "central_asia" in ids
    assert "siberia" in ids
    assert "bay_of_bengal" in ids


def test_get_region_detail_success(client):
    response = client.get("/api/regions/western_indian_ocean")
    assert response.status_code == 200
    data = response.json()
    assert data["region_id"] == "western_indian_ocean"
    assert "bounds" in data
    assert len(data["bounds"]) == 4


def test_get_region_detail_not_found(client):
    response = client.get("/api/regions/nonexistent_antarctica_zone")
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()
