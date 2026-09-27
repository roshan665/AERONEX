"""
Comprehensive Automated Tests for Phase 5: Real NWP Data Ingestion & Preprocessing
"""

import os
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ingestion.service import IngestionService
from app.ingestion.parser import NWPFileParser
from app.ingestion.validator import NWPDataValidator
from app.ingestion.models import IngestionRunRequest
from app.engine.pipeline import AnomalyDetectionPipeline

client = TestClient(app)

SAMPLE_NETCDF_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "nwp", "gfs_sample_0p25_south_asia.nc")
)


class TestNWPFileParser:
    def test_sample_file_exists(self):
        assert os.path.exists(SAMPLE_NETCDF_PATH), f"Sample NetCDF fixture missing at {SAMPLE_NETCDF_PATH}"

    def test_parse_netcdf_dataset(self):
        dataset = NWPFileParser.parse_file(SAMPLE_NETCDF_PATH, lead_time_hours_override=24)
        
        assert dataset is not None
        assert dataset.lead_time_hours == 24
        assert len(dataset.lats) == 121
        assert len(dataset.lons) == 121
        assert dataset.lats[0] == pytest.approx(8.0, abs=0.1)
        assert dataset.lats[-1] == pytest.approx(38.0, abs=0.1)
        assert dataset.lons[0] == pytest.approx(65.0, abs=0.1)
        assert dataset.lons[-1] == pytest.approx(95.0, abs=0.1)

        # Check core atmospheric variables
        assert "temperature" in dataset.variables
        assert "u10" in dataset.variables
        assert "v10" in dataset.variables
        assert "mslp" in dataset.variables
        assert "precipitation" in dataset.variables

        # Verify shapes
        assert dataset.variables["temperature"].shape == (121, 121)
        assert dataset.variables["mslp"].shape == (121, 121)

        # Check raw units
        assert dataset.units["temperature"] == "K"
        assert dataset.units["mslp"] == "Pa"

    def test_missing_file_raises_error(self):
        with pytest.raises(FileNotFoundError):
            NWPFileParser.parse_file("non_existent_file_path_12345.nc")


class TestNWPDataValidator:
    def test_validate_valid_netcdf(self):
        dataset = NWPFileParser.parse_file(SAMPLE_NETCDF_PATH)
        report = NWPDataValidator.validate_grid(
            dataset_id="test_gfs_sample",
            file_path=SAMPLE_NETCDF_PATH,
            file_format="NetCDF4",
            lats=dataset.lats,
            lons=dataset.lons,
            variables=dataset.variables,
            units=dataset.units,
            forecast_init_time=dataset.forecast_init_time,
            valid_time=dataset.valid_time,
            lead_time_hours=dataset.lead_time_hours,
        )

        assert report.is_valid is True
        assert report.file_readable is True
        assert len(report.errors) == 0
        assert len(report.detected_variables) >= 4
        assert report.resolution_deg == pytest.approx(0.25, abs=0.01)

    def test_validate_out_of_bounds_latitude(self):
        dataset = NWPFileParser.parse_file(SAMPLE_NETCDF_PATH)
        corrupted_lats = dataset.lats.copy()
        corrupted_lats[0] = 95.0  # Invalid latitude

        report = NWPDataValidator.validate_grid(
            dataset_id="corrupt_lat",
            file_path=SAMPLE_NETCDF_PATH,
            file_format="NetCDF4",
            lats=corrupted_lats,
            lons=dataset.lons,
            variables=dataset.variables,
            units=dataset.units,
        )

        assert report.is_valid is False
        assert any("Latitude" in err for err in report.errors)


class TestPipelineIntegration:
    def test_real_dataset_feeds_anomaly_pipeline(self):
        dataset = NWPFileParser.parse_file(SAMPLE_NETCDF_PATH)
        pipeline = AnomalyDetectionPipeline()
        result = pipeline.run(dataset=dataset)

        assert result is not None
        assert result.total_anomalies_detected > 0
        assert result.total_footprints_extracted > 0
        assert len(result.events) > 0

        # Verify event properties
        event_types = [e.type for e in result.events]
        assert any(t in ["Heat Wave", "Cyclone", "Wind Anomaly"] for t in event_types)


class TestIngestionAPIRoutes:
    def test_list_datasets(self):
        response = client.get("/api/datasets")
        assert response.status_code == 200
        datasets = response.json()
        assert isinstance(datasets, list)
        assert len(datasets) > 0
        assert any("gfs" in d["dataset_id"].lower() for d in datasets)

    def test_get_dataset_detail(self):
        response = client.get("/api/datasets")
        first_id = response.json()[0]["dataset_id"]

        detail_resp = client.get(f"/api/datasets/{first_id}")
        assert detail_resp.status_code == 200
        data = detail_resp.json()
        assert data["dataset_id"] == first_id
        assert data["spatial_resolution_deg"] == 0.25

    def test_get_nonexistent_dataset_returns_404(self):
        response = client.get("/api/datasets/unknown_nonexistent_dataset_999")
        assert response.status_code == 404

    def test_validate_dataset_endpoint(self):
        response = client.post(
            "/api/ingestion/validate",
            json={"dataset_id": "gfs_sample_0p25_south_asia"}
        )
        assert response.status_code == 200
        report = response.json()
        assert report["is_valid"] is True
        assert report["file_readable"] is True
        assert len(report["detected_variables"]) >= 4

    def test_run_ingestion_endpoint_local(self):
        request_payload = {
            "dataset_id": "gfs_sample_0p25_south_asia",
            "source_mode": "local",
            "lead_time_hours": 24,
            "region_id": "south_asia",
            "run_anomaly_detection": True,
            "min_area_km2": 2500.0,
        }
        response = client.post("/api/ingestion/run", json=request_payload)
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["is_real_data"] is True
        assert result["anomalies_detected_count"] > 0
        assert len(result["anomalies"]) > 0

    def test_get_ingestion_status(self):
        response = client.get("/api/ingestion/status")
        assert response.status_code == 200
        status = response.json()
        assert "status" in status
        assert "active_data_source" in status
        assert "available_providers" in status
        assert len(status["available_providers"]) >= 2
