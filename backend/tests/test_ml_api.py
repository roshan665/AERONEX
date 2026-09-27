"""
Integration Tests for Phase 6 AI/ML, Scoring, Evaluation, and Uncertainty Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_models_endpoint():
    res = client.get("/api/models")
    assert res.status_code == 200
    data = res.json()
    assert "models" in data
    assert len(data["models"]) >= 3
    assert data["active_model_id"] == "deterministic_baseline"


def test_model_status_endpoint():
    res = client.get("/api/models/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "active_model_id" in data
    assert "feature_schema_version" in data


def test_model_detail_endpoint():
    res = client.get("/api/models/deterministic_baseline")
    assert res.status_code == 200
    data = res.json()
    assert data["model_id"] == "deterministic_baseline"
    assert data["is_operational"] is True

    res_ml = client.get("/api/models/isolation_forest_v1")
    assert res_ml.status_code == 200
    data_ml = res_ml.json()
    assert data_ml["model_id"] == "isolation_forest_v1"
    assert data_ml["is_operational"] is False  # Experimental

    res_404 = client.get("/api/models/nonexistent_model_id")
    assert res_404.status_code == 404


def test_model_selection_endpoint():
    # Select isolation forest
    res = client.post("/api/models/select", json={"model_id": "isolation_forest_v1"})
    assert res.status_code == 200
    data = res.json()
    assert data["model_id"] == "isolation_forest_v1"

    # Verify status reflects change
    status_res = client.get("/api/models/status")
    assert status_res.json()["active_model_id"] == "isolation_forest_v1"

    # Select research stub should return 400
    res_stub = client.post("/api/models/select", json={"model_id": "spatiotemporal_research_stub"})
    assert res_stub.status_code == 400

    # Revert back to deterministic baseline
    revert_res = client.post("/api/models/select", json={"model_id": "deterministic_baseline"})
    assert revert_res.status_code == 200


def test_anomaly_score_endpoint():
    res = client.get("/api/anomalies/evt-001/score")
    assert res.status_code == 200
    data = res.json()
    assert data["event_id"] == "evt-001"
    assert 0.0 <= data["composite_score"] <= 1.0
    assert 0.0 <= data["overall_score_100"] <= 100.0
    assert data["is_probability"] is False
    assert "thermal_deviation" in data["components"]
    assert len(data["primary_contributing_variables"]) >= 1

    # 404 for nonexistent event
    res_404 = client.get("/api/anomalies/nonexistent_evt_999/score")
    assert res_404.status_code == 404


def test_custom_scoring_compute_endpoint():
    payload = {
        "event_id": "custom_calculation",
        "observed_temperature": 45.0,
        "baseline_temperature": 28.0,
        "max_wind_kmh": 125.0,
        "min_mslp_hpa": 960.0,
        "area_km2": 150000.0,
        "forecast_days": [1, 2, 3],
        "weights": {
            "w_temp": 0.25,
            "w_wind": 0.25,
            "w_pressure": 0.20,
            "w_spatial": 0.10,
            "w_persistence": 0.10,
            "w_quality": 0.10
        }
    }
    res = client.post("/api/scoring/compute", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["event_id"] == "custom_calculation"
    assert data["overall_score_100"] > 50.0


def test_evaluation_benchmark_endpoint():
    res = client.get("/api/evaluation")
    assert res.status_code == 200
    data = res.json()
    assert data["is_synthetic_evaluation"] is True
    assert "models" in data
    assert "deterministic_baseline" in data["models"]
    assert "isolation_forest_v1" in data["models"]
    assert len(data["summary_table"]) >= 2


def test_uncertainty_series_endpoint():
    res_ens = client.get("/api/uncertainty/series?variable=temperature&mode=ensemble")
    assert res_ens.status_code == 200
    data_ens = res_ens.json()
    assert data_ens["is_available"] is True
    assert data_ens["uncertainty_mode"] == "ENSEMBLE_MEMBERS"
    assert len(data_ens["timeline"]) == 10

    res_det = client.get("/api/uncertainty/series?variable=temperature&mode=deterministic")
    assert res_det.status_code == 200
    data_det = res_det.json()
    assert data_det["is_available"] is False
    assert data_det["uncertainty_mode"] == "DETERMINISTIC_ONLY"
    assert data_det["empty_state_explanation"] is not None
