"""
Tests for Dashboard Overview Endpoint
"""


def test_overview_endpoint_success(client):
    response = client.get("/api/overview")
    assert response.status_code == 200
    data = response.json()

    # Summary verification
    summary = data["summary"]
    assert summary["active_anomaly_count"] >= 5
    assert summary["regions_monitored_count"] == 12
    assert summary["forecast_horizon_days"] == 10
    assert summary["is_simulated"] is True
    assert "DEMO_SYNTHETIC" in summary["data_provenance"]

    # Dashboard cards verification
    cards = data["dashboard_cards"]
    assert len(cards) == 4
    card_ids = [c["id"] for c in cards]
    assert "active-anomalies" in card_ids
    assert "regions-monitored" in card_ids
    assert "forecast-horizon" in card_ids
    assert "latest-data" in card_ids

    # Severity distribution
    severity = data["severity_distribution"]
    assert len(severity) == 3
    sev_names = [s["name"] for s in severity]
    assert "High" in sev_names
    assert "Medium" in sev_names
    assert "Low" in sev_names

    # Hazard breakdown
    hazard = data["hazard_breakdown"]
    assert hazard["cyclones"] >= 1
    assert hazard["heat_domes"] >= 1
    assert hazard["cold_waves"] >= 1

    # Critical alerts
    alerts = data["critical_alerts"]
    assert len(alerts) >= 1
    assert alerts[0]["severity"] in ["High", "Medium", "Low"]


def test_overview_with_region_filter(client):
    response = client.get("/api/overview?region_id=western_indian_ocean")
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["active_anomaly_count"] >= 1
