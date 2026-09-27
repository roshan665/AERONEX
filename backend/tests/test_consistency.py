"""
Cross-Endpoint Data Consistency Verification Tests
"""


def test_overview_counts_match_anomalies(client):
    overview_res = client.get("/api/overview")
    anomalies_res = client.get("/api/anomalies")

    assert overview_res.status_code == 200
    assert anomalies_res.status_code == 200

    overview_data = overview_res.json()
    anomalies_data = anomalies_res.json()

    # Active anomaly counts must match exactly
    assert overview_data["summary"]["active_anomaly_count"] == anomalies_data["total"]

    # Critical alerts count in overview must match High severity count in anomalies
    high_severity_count = sum(1 for a in anomalies_data["events"] if a["severity"] == "High")
    assert overview_data["summary"]["critical_alerts_count"] == high_severity_count


def test_map_feature_ids_match_anomaly_ids(client):
    map_res = client.get("/api/map/layers")
    anomalies_res = client.get("/api/anomalies")

    assert map_res.status_code == 200
    assert anomalies_res.status_code == 200

    map_data = map_res.json()
    anomalies_data = anomalies_res.json()

    map_anomaly_ids = {f["id"] for f in map_data["anomalies_geojson"]["features"]}
    catalog_anomaly_ids = {a["id"] for a in anomalies_data["events"]}

    # Every anomaly in catalog must be represented in GeoJSON map layer
    assert catalog_anomaly_ids.issubset(map_anomaly_ids)


def test_forecast_variables_consistency(client):
    variables = ["temperature", "wind", "pressure", "precipitation"]
    for var in variables:
        res = client.get(f"/api/forecasts?variable={var}")
        assert res.status_code == 200
        data = res.json()
        assert data["variable"] == var
        assert len(data["timeline"]) == 10
        assert data["is_simulated"] is True
        # Verify valid timestamps and physical envelope bounds
        for item in data["timeline"]:
            assert item["valid_time"].endswith("Z")
            assert item["uncertainty_lower"] <= item["uncertainty_upper"]
            assert item["min"] <= item["global_avg"] <= item["max"]


def test_all_endpoints_contain_demo_indicator(client):
    endpoints = [
        "/api/health",
        "/api/overview",
        "/api/forecasts",
        "/api/anomalies",
        "/api/map/layers",
        "/api/metadata",
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200
        data = res.json()
        # Verify either is_simulated or data_provenance or data_mode indicates demo/simulated data
        is_sim = (
            data.get("is_simulated") is True
            or "DEMO" in str(data.get("data_provenance", ""))
            or "DEMO" in str(data.get("data_mode", ""))
            or (isinstance(data.get("summary"), dict) and data["summary"].get("is_simulated") is True)
        )
        assert is_sim, f"Endpoint {ep} must indicate simulated/demo data"
