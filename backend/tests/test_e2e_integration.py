"""
AeroNex Phase 7: End-to-End System Integration & Workflow Test Suite

Validates full user journey, schema compliance, cross-module consistency,
NWP ingestion, tracking, uncertainty, and error resilience.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestFullUserWorkflowE2E:
    """
    Tests the complete 6-step user journey from initial load to ingestion.
    """

    def test_step1_open_aeronex_and_inspect_overview(self):
        """
        Step 1: Dashboard loads, health probe succeeds, and summary cards are populated.
        """
        # Health & Liveness
        health_res = client.get("/health")
        assert health_res.status_code == 200
        health_data = health_res.json()
        assert health_data["status"] == "healthy"
        assert "AeroNex" in health_data["app"]

        # Executive Overview
        overview_res = client.get("/overview")
        assert overview_res.status_code == 200
        overview_data = overview_res.json()
        
        # Verify Summary KPIs
        summary = overview_data["summary"]
        assert summary["active_anomaly_count"] >= 5
        assert summary["regions_monitored_count"] >= 5
        assert summary["forecast_horizon_days"] == 10
        assert summary["data_provenance"] == "DEMO_SYNTHETIC_DATASET"
        assert summary["is_simulated"] is True

        # Verify Dashboard Cards format
        cards = overview_data["dashboard_cards"]
        assert len(cards) >= 4
        card_ids = [c["id"] for c in cards]
        assert "active-anomalies" in card_ids
        assert "regions-monitored" in card_ids
        assert "forecast-horizon" in card_ids
        assert "latest-data" in card_ids

    def test_step2_forecast_selection_and_metadata(self):
        """
        Step 2: Forecast queries load time-series and metadata across lead days.
        """
        # Temperature forecast
        res_temp = client.get("/forecasts?variable=temperature")
        assert res_temp.status_code == 200
        temp_data = res_temp.json()
        assert temp_data["variable"] == "temperature"
        assert temp_data["unit"] == "°C"
        assert len(temp_data["timeline"]) == 10

        # Wind forecast with lead day filter
        res_wind = client.get("/forecasts?variable=wind&lead_day=3")
        assert res_wind.status_code == 200
        wind_data = res_wind.json()
        assert wind_data["variable"] == "wind"
        assert wind_data["unit"] == "km/h"
        assert len(wind_data["timeline"]) == 1
        assert wind_data["timeline"][0]["day"] in (3, "Day 3") or wind_data["timeline"][0].get("lead_day") == 3

        # Model run metadata
        res_run = client.get("/forecasts/GFS-20250426-00Z")
        assert res_run.status_code == 200
        run_data = res_run.json()
        assert run_data["forecast_id"] == "GFS-20250426-00Z"
        assert run_data["spatial_resolution"] == "0.25°"
        assert run_data["is_simulated"] is True

    def test_step3_explore_map_and_footprints(self):
        """
        Step 3: Interactive map layers with RFC 7946 GeoJSON polygons and waypoints.
        """
        res = client.get("/map/layers")
        assert res.status_code == 200
        data = res.json()

        # Check GeoJSON FeatureCollection
        geojson = data["geojson"]
        assert geojson["type"] == "FeatureCollection"
        features = geojson["features"]
        assert len(features) >= 5

        for feat in features:
            assert feat["type"] == "Feature"
            assert "geometry" in feat
            assert feat["geometry"]["type"] in ("Polygon", "Point")
            assert "properties" in feat
            props = feat["properties"]
            assert "name" in props
            assert "severity" in props
            assert "color" in props

    def test_step4_inspect_anomaly_telemetry_and_filtering(self):
        """
        Step 4: Anomaly catalog queries, filtering, and detailed diagnostic inspection.
        """
        # Query list
        res = client.get("/anomalies?severity=High")
        assert res.status_code == 200
        data = res.json()
        assert data["count"] > 0
        for event in data["events"]:
            assert event["severity"] == "High"
            assert event["severity_level"] >= 3

        # Inspect specific anomaly
        first_id = data["events"][0]["id"]
        detail_res = client.get(f"/anomalies/{first_id}")
        assert detail_res.status_code == 200
        detail = detail_res.json()

        assert detail["event"]["id"] == first_id
        assert "footprint_polygon" in detail
        assert len(detail["footprint_polygon"]) >= 3  # Valid closed polygon
        assert "forecast_track" in detail
        assert detail["is_simulated"] is True

    def test_step5_track_event_and_uncertainty(self):
        """
        Step 5: Event tracking across time frames, translation speed, bearing, and uncertainty.
        """
        # Query active tracks
        res = client.get("/events/tracks?status=ACTIVE")
        assert res.status_code == 200
        tracks = res.json()
        assert len(tracks) >= 3

        # Inspect cyclone track
        cyclone_track = next((t for t in tracks if t["category"] == "cyclone"), None)
        assert cyclone_track is not None
        assert cyclone_track["cumulative_distance_km"] > 0
        assert cyclone_track["mean_speed_kmh"] > 0
        assert len(cyclone_track["trajectory_line"]) >= 3

        # Chronological track history
        hist_res = client.get(f"/events/tracks/{cyclone_track['track_id']}/history")
        assert hist_res.status_code == 200
        hist_data = hist_res.json()
        if isinstance(hist_data, list):
            assert len(hist_data) >= 3
        else:
            assert hist_data["track_id"] == cyclone_track["track_id"]
            assert len(hist_data["history"]) >= 3

        # Uncertainty endpoint
        unc_res = client.get(f"/uncertainty/{cyclone_track['track_id']}")
        assert unc_res.status_code == 200
        unc_data = unc_res.json()
        assert unc_data.get("track_id") == cyclone_track["track_id"] or unc_data.get("event_id") in (cyclone_track["track_id"], "evt-001")
        assert "lead_time_decay" in unc_data
        assert len(unc_data["lead_time_decay"]) > 0


    def test_step6_nwp_ingestion_and_validation(self):
        """
        Step 6: Dataset catalog, physical validation, and real NetCDF4 ingestion run.
        """
        # List available datasets
        ds_res = client.get("/datasets")
        assert ds_res.status_code == 200
        datasets = ds_res.json()
        assert len(datasets) >= 1
        sample_ds = datasets[0]
        assert sample_ds["file_format"] == "NetCDF4"

        # Validate dataset quality & physical bounds
        val_res = client.post("/ingestion/validate", json={"dataset_id": sample_ds["dataset_id"]})
        assert val_res.status_code == 200
        val_data = val_res.json()
        assert val_data["is_valid"] is True
        assert val_data["file_readable"] is True
        assert len(val_data["passed_checks"]) >= 5

        # Execute ingestion pipeline with real local NetCDF4 grid
        run_res = client.post("/ingestion/run", json={
            "dataset_id": sample_ds["dataset_id"],
            "source_mode": "local",
            "lead_time_hours": 24,
            "region_id": "south_asia",
            "run_anomaly_detection": True,
            "min_area_km2": 2500.0,
        })
        assert run_res.status_code == 200
        run_data = run_res.json()
        assert run_data["success"] is True
        assert run_data["data_source"] == "LOCAL_NWP_NETCDF"
        assert run_data["is_real_data"] is True
        assert run_data["anomalies_detected_count"] >= 1
        assert len(run_data["anomalies"]) >= 1

        # Check ingestion status endpoint
        status_res = client.get("/ingestion/status")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert "available_providers" in status_data


class TestDataConsistencyAndUnits:
    """
    Validates cross-endpoint consistency, unit adherence, and coordinate conventions.
    """

    def test_units_and_naming_conventions(self):
        """
        Ensures temperature is °C, wind is km/h or m/s, pressure is hPa, area is km².
        """
        anomalies_res = client.get("/anomalies")
        assert anomalies_res.status_code == 200
        events = anomalies_res.json()["events"]

        for evt in events:
            # Area in km2
            assert evt["estimated_area_km2"] > 0
            assert "km²" in evt["estimated_area"]

            # Coordinates geographic bounds
            assert -90.0 <= evt["lat"] <= 90.0
            assert -180.0 <= evt["lon"] <= 180.0

            # Severity tier mapping
            assert evt["severity"] in ("High", "Medium", "Low")
            if evt["severity"] == "High":
                assert evt["severity_level"] >= 3
            elif evt["severity"] == "Medium":
                assert evt["severity_level"] == 2
            else:
                assert evt["severity_level"] == 1

    def test_regions_and_overview_alignment(self):
        """
        Ensures region counts in /regions and /overview align.
        """
        regions_res = client.get("/regions")
        assert regions_res.status_code == 200
        res_json = regions_res.json()
        regions = res_json["regions"] if isinstance(res_json, dict) and "regions" in res_json else res_json

        overview_res = client.get("/overview")
        assert overview_res.status_code == 200
        summary = overview_res.json()["summary"]

        assert summary["regions_monitored_count"] == len(regions)


class TestErrorResilienceAndEdgeCases:
    """
    Validates graceful error handling, status codes, and non-disclosure of stack traces.
    """

    def test_nonexistent_anomaly_id_returns_404(self):
        res = client.get("/anomalies/evt-nonexistent-999")
        assert res.status_code == 404
        assert "detail" in res.json()

    def test_nonexistent_forecast_id_returns_404(self):
        res = client.get("/forecasts/MODEL-FAKE-RUN")
        assert res.status_code == 404
        assert "detail" in res.json()

    def test_nonexistent_track_id_returns_404(self):
        res = client.get("/events/tracks/TRK-FAKE-999")
        assert res.status_code == 404
        assert "detail" in res.json()

    def test_nonexistent_dataset_id_returns_404(self):
        res = client.get("/datasets/fake_dataset_id_999")
        assert res.status_code == 404
        assert "detail" in res.json()

    def test_invalid_forecast_day_query_returns_422(self):
        # Forecast day must be between 1 and 10
        res = client.get("/anomalies?forecast_day=15")
        assert res.status_code == 422

    def test_negative_min_area_query_returns_422(self):
        res = client.get("/anomalies?min_area_km2=-100")
        assert res.status_code == 422

    def test_ingestion_invalid_dataset_id_handled_gracefully(self):
        res = client.post("/ingestion/validate", json={"dataset_id": "nonexistent_file_id"})
        assert res.status_code in (200, 400, 404)
        data = res.json()
        if res.status_code == 200:
            assert data["is_valid"] is False
            assert data["file_readable"] is False
            assert len(data["errors"]) > 0
