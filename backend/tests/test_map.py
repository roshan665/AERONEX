"""
Tests for Map Layers and RFC 7946 GeoJSON Features
"""


def test_map_layers_structure(client):
    response = client.get("/api/map/layers")
    assert response.status_code == 200
    data = response.json()

    # Layers
    assert len(data["available_layers"]) == 4
    layer_ids = [l["layer_id"] for l in data["available_layers"]]
    assert "temperature" in layer_ids
    assert "wind" in layer_ids
    assert "pressure" in layer_ids
    assert "precipitation" in layer_ids

    # GeoJSON FeatureCollection: Anomalies
    fc = data["anomalies_geojson"]
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) >= 5
    first_feat = fc["features"][0]
    assert first_feat["type"] == "Feature"
    assert first_feat["geometry"]["type"] == "Polygon"
    
    # Check RFC 7946 coordinate ordering: [longitude, latitude]
    poly_coords = first_feat["geometry"]["coordinates"][0]
    # In evt-001 (Western Indian Ocean), Longitude is ~75 to 83, Latitude is ~ -9 to -16
    assert poly_coords[0][0] > 70.0  # Longitude
    assert poly_coords[0][1] < 0.0   # Latitude (Southern Hemisphere)

    # GeoJSON FeatureCollection: Tracks
    tracks_fc = data["tracks_geojson"]
    assert tracks_fc["type"] == "FeatureCollection"
    assert len(tracks_fc["features"]) >= 5
    first_track = tracks_fc["features"][0]
    assert first_track["geometry"]["type"] == "LineString"
