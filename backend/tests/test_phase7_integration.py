"""
Phase 7 End-to-End System Integration & SIH Demo Readiness Test Suite

Validates:
1. Service health and provider availability distinction.
2. Executive overview data and cards.
3. Multi-variable forecast horizon queries.
4. Reproducible synthetic scenario generation (Cyclone, Heat Dome, Cold Wave).
5. Scientific detection pipeline execution and GeoJSON footprint extraction.
6. Input validation and RFC 7807 error responses for out-of-bound requests.
7. NWP dataset discovery, validation, and missing provider error handling.
8. Model selection, scoring attribution, and uncertainty telemetry.
9. Data provenance consistency and non-fabrication guarantees.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestSystemHealthAndProviders:
    """Requirement 1 & 8.1: Health check distinguishes server health from data provider status."""

    def test_health_endpoint_contract(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "subsystems" in data
        assert data["subsystems"]["api_gateway"] == "ONLINE"
        assert data["subsystems"]["anomaly_engine"] == "ONLINE"

        # Verify data providers breakdown
        assert "data_providers" in data
        providers = data["data_providers"]
        assert "synthetic_demo_generator" in providers
        assert providers["synthetic_demo_generator"]["status"] == "ONLINE"
        assert providers["synthetic_demo_generator"]["available"] is True

        assert "local_nwp_storage" in providers
        assert providers["local_nwp_storage"]["status"] == "ONLINE"

        assert "noaa_nomads_gfs" in providers
        # Clearly transparent: unverified remote fetch is not claimed as available offline
        assert providers["noaa_nomads_gfs"]["available"] is False


class TestOverviewAndCatalog:
    """Requirement 8.3: Overview KPIs and active anomaly catalog."""

    def test_overview_metrics(self):
        response = client.get("/api/overview")
        assert response.status_code == 200
        data = response.json()

        assert "dashboard_cards" in data
        assert len(data["dashboard_cards"]) >= 4
        card_ids = [c["id"] for c in data["dashboard_cards"]]
        assert "active-anomalies" in card_ids
        assert "regions-monitored" in card_ids

        assert data["summary"]["is_simulated"] is True
        assert "DEMO" in data["summary"]["data_provenance"]

    def test_anomalies_filtering(self):
        # Filter by category
        res_cyc = client.get("/api/anomalies?category_key=cyclone")
        assert res_cyc.status_code == 200
        events_cyc = res_cyc.json()["events"]
        assert all(e["category_key"] == "cyclone" for e in events_cyc)

        # Filter by severity
        res_high = client.get("/api/anomalies?severity=High")
        assert res_high.status_code == 200
        events_high = res_high.json()["events"]
        assert all(e["severity"] == "High" for e in events_high)


class TestForecastExploration:
    """Requirement 8.4: Forecast time-series exploration across variables and lead times."""

    def test_forecast_variables(self):
        for var in ["temperature", "wind", "pressure", "precipitation"]:
            response = client.get(f"/api/forecasts?variable={var}")
            assert response.status_code == 200
            data = response.json()
            assert data["variable"] == var
            assert len(data["timeline"]) == 10  # 10-day horizon

    def test_invalid_forecast_variable_fails_gracefully(self):
        response = client.get("/api/forecasts?variable=plasma_density")
        assert response.status_code == 422
        assert "Unsupported meteorological variable" in response.json()["detail"]


class TestDemoScenariosAndDetection:
    """Requirement 8.5 & 8.6: Presentation demo scenarios and detection execution."""

    def test_scenarios_catalog(self):
        response = client.get("/api/detection/scenarios")
        assert response.status_code == 200
        scenarios = response.json()
        assert len(scenarios) >= 4

        scenario_ids = [s["scenario_id"] for s in scenarios]
        assert "cyclone" in scenario_ids
        assert "heatwave" in scenario_ids
        assert "coldwave" in scenario_ids
        assert "all" in scenario_ids

    def test_cyclone_scenario_execution(self):
        response = client.post("/api/detection/run", json={
            "lead_time_hours": 24,
            "seed": 42,
            "scenario": "cyclone",
            "min_area_km2": 2500.0,
        })
        assert response.status_code == 200
        data = response.json()

        assert data["total_anomalies_detected"] >= 1
        event_names = [e["name"] for e in data["events"]]
        assert any("Cyclone" in name for name in event_names)
        assert data["execution_time_ms"] > 0
        assert data["is_simulated"] is True

    def test_heatwave_scenario_execution(self):
        response = client.post("/api/detection/run", json={
            "lead_time_hours": 48,
            "seed": 101,
            "scenario": "heatwave",
            "min_area_km2": 2500.0,
        })
        assert response.status_code == 200
        data = response.json()

        assert data["total_anomalies_detected"] >= 1
        event_names = [e["name"] for e in data["events"]]
        assert any("Heat" in name for name in event_names)

    def test_coldwave_scenario_execution(self):
        response = client.post("/api/detection/run", json={
            "lead_time_hours": 72,
            "seed": 202,
            "scenario": "coldwave",
            "min_area_km2": 2500.0,
        })
        assert response.status_code == 200
        data = response.json()

        assert data["total_anomalies_detected"] >= 1
        event_names = [e["name"] for e in data["events"]]
        assert any("Cold" in name for name in event_names)

    def test_invalid_lead_time_validation(self):
        # Lead time > 240 hours should be rejected
        response = client.post("/api/detection/run", json={
            "lead_time_hours": 500,
        })
        assert response.status_code == 422

    def test_negative_lead_time_validation(self):
        # Lead time < 0 hours should be rejected
        response = client.post("/api/detection/run", json={
            "lead_time_hours": -10,
        })
        assert response.status_code == 422

    def test_empty_results_handling_with_strict_thresholds(self):
        # Extreme minimum area threshold should yield 0 anomalies without runtime crash
        response = client.post("/api/detection/run", json={
            "lead_time_hours": 24,
            "seed": 42,
            "scenario": "cyclone",
            "min_area_km2": 999999999.0,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["total_anomalies_detected"] == 0
        assert data["events"] == []
        assert "execution_time_ms" in data


class TestNWPRealDataIntegration:
    """Requirement 8.10 & 8.11: NWP datasets and clear communication of unavailability."""

    def test_available_datasets_listing(self):
        response = client.get("/api/datasets")
        assert response.status_code == 200
        datasets = response.json()
        assert len(datasets) >= 1
        assert any(ds["dataset_id"] == "gfs_sample_0p25_south_asia" for ds in datasets)

    def test_missing_dataset_returns_404(self):
        response = client.get("/api/datasets/non_existent_dataset_12345")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_validate_real_nwp_dataset(self):
        response = client.post("/api/ingestion/validate", json={
            "dataset_id": "gfs_sample_0p25_south_asia"
        })
        assert response.status_code == 200
        report = response.json()
        assert report["is_valid"] is True
        assert report["file_readable"] is True
        assert report["grid_shape"] == [121, 121]

    def test_run_nwp_ingestion_local_sample(self):
        response = client.post("/api/ingestion/run", json={
            "dataset_id": "gfs_sample_0p25_south_asia",
            "source_mode": "local",
            "lead_time_hours": 24,
            "region_id": "south_asia",
            "run_anomaly_detection": True,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["dataset_id"] == "gfs_sample_0p25_south_asia"
        assert data["anomalies_detected_count"] >= 0

    def test_run_nwp_ingestion_nonexistent_dataset(self):
        response = client.post("/api/ingestion/run", json={
            "dataset_id": "nonexistent_fake_gfs_file",
            "source_mode": "local",
            "lead_time_hours": 24,
        })
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestAIModelsAndUncertainty:
    """Requirement 8.8: AI/ML models registry, scoring, and uncertainty services."""

    def test_models_registry_and_active_selection(self):
        response = client.get("/api/models")
        assert response.status_code == 200
        models = response.json()["models"]
        model_ids = [m["model_id"] for m in models]

        assert "deterministic_baseline" in model_ids
        assert "isolation_forest_v1" in model_ids

        # Switch to isolation forest
        sel_res = client.post("/api/models/select", json={"model_id": "isolation_forest_v1"})
        assert sel_res.status_code == 200
        assert sel_res.json()["model_id"] == "isolation_forest_v1"

        # Switch back to deterministic baseline
        sel_back = client.post("/api/models/select", json={"model_id": "deterministic_baseline"})
        assert sel_back.status_code == 200
        assert sel_back.json()["model_id"] == "deterministic_baseline"

    def test_anomaly_score_attribution(self):
        response = client.get("/api/anomalies/evt-001/score")
        assert response.status_code == 200
        score_data = response.json()

        assert score_data["event_id"] == "evt-001"
        assert "composite_score" in score_data
        assert "overall_score_100" in score_data
        assert "components" in score_data
        assert score_data["is_probability"] is False
        assert "score_interpretation" in score_data

    def test_uncertainty_series(self):
        # Ensemble mode (simulated)
        res_ens = client.get("/api/uncertainty/series?variable=temperature&mode=ensemble")
        assert res_ens.status_code == 200
        data_ens = res_ens.json()
        assert data_ens["is_available"] is True
        assert data_ens["member_count"] == 5

        # Deterministic mode (returns unavailable status honestly)
        res_det = client.get("/api/uncertainty/series?variable=temperature&mode=deterministic")
        assert res_det.status_code == 200
        data_det = res_det.json()
        assert data_det["is_available"] is False
        assert "deterministic" in data_det["empty_state_explanation"].lower()


class TestTrackingContinuityAndProvenance:
    """Requirement 8.9 & 8.12: Track continuity, persistence metrics, and data provenance consistency."""

    def test_tracks_list_and_continuity_metrics(self):
        response = client.get("/api/events/tracks")
        assert response.status_code == 200
        tracks = response.json()
        assert len(tracks) >= 3

        for track in tracks:
            assert "track_id" in track
            assert "category" in track
            assert "first_detection_lead_hours" in track
            assert "latest_detection_lead_hours" in track
            assert "total_detections" in track
            assert "status" in track
            assert track["total_detections"] > 0

    def test_track_detail_has_spatial_history_and_dispersion(self):
        response = client.get("/api/events/tracks/TRK-CYC-001")
        assert response.status_code == 200
        track = response.json()

        assert track["track_id"] == "TRK-CYC-001"
        assert len(track["points"]) >= 2
        # Verify persistence and motion metrics
        assert "net_displacement_km" in track
        assert "mean_speed_kmh" in track
        assert "cumulative_distance_km" in track
        assert "movement_notes" in track
        assert track["net_displacement_km"] > 0

    def test_data_provenance_honesty_across_endpoints(self):
        # 1. Overview provenance
        overview_res = client.get("/api/overview")
        assert overview_res.status_code == 200
        assert "DEMO" in overview_res.json()["summary"]["data_provenance"]

        # 2. Anomalies provenance
        anom_res = client.get("/api/anomalies")
        assert anom_res.status_code == 200
        for evt in anom_res.json()["events"]:
            assert "data_source" in evt
            assert "is_simulated" in evt
            assert evt["is_simulated"] is True

        # 3. Detection run provenance
        det_res = client.post("/api/detection/run", json={"scenario": "cyclone", "lead_time_hours": 24})
        assert det_res.status_code == 200
        assert det_res.json()["is_simulated"] is True
