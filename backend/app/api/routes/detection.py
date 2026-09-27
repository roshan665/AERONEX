"""
Processing Route for Running the Anomaly Detection Pipeline
"""

from typing import Optional, Literal
from fastapi import APIRouter, Query, Body, HTTPException
from pydantic import BaseModel, Field

from app.engine.config import EngineConfig, DetectorThresholds, FootprintConfig
from app.engine.pipeline import AnomalyDetectionPipeline, PipelineExecutionResult
from app.engine.synthetic_generator import SyntheticWeatherGenerator
from app.services.anomaly_service import AnomalyService
from app.core.logging import logger

router = APIRouter(tags=["Detection Engine"])


class DetectionRunRequest(BaseModel):
    lead_time_hours: int = Field(default=24, ge=0, le=240, description="Forecast lead time in hours (0 to 240)")
    min_area_km2: Optional[float] = Field(default=2500.0, ge=0.0, description="Minimum footprint surface area in km²")
    connectivity: Literal[4, 8] = Field(default=8, description="Morphological connectivity (4 or 8)")
    seed: int = Field(default=42, description="Random seed for reproducible synthetic dataset")
    scenario: Optional[str] = Field(default=None, description="Optional scenario focus: 'cyclone', 'heatwave', 'coldwave', or None")


@router.get(
    "/detection/scenarios",
    summary="List Reproducible Synthetic Demo Scenarios",
    description="Returns metadata, expected signatures, and parameters for presentation demo scenarios."
)
def list_demo_scenarios():
    return [
        {
            "scenario_id": "cyclone",
            "name": "Tropical Cyclone Vortex",
            "type": "Cyclone",
            "category_key": "cyclone",
            "lead_time_hours": 24,
            "seed": 42,
            "region": "Western Indian Ocean",
            "description": "Intense cyclonic depression with eyewall wind gusts exceeding 140 km/h and central pressure drop to 948 hPa.",
            "expected_phenomenon": "Co-located extreme MSLP deficit and gale-force wind speed footprint.",
            "data_provenance": "DEMO_SYNTHETIC_DATASET",
            "is_simulated": True,
        },
        {
            "scenario_id": "heatwave",
            "name": "Severe Heat Dome",
            "type": "Heat Wave",
            "category_key": "heat_wave",
            "lead_time_hours": 48,
            "seed": 101,
            "region": "Northwest Subtropics / Central Asia",
            "description": "Upper-tropospheric high-pressure thermal ridge trapping surface heat with temperatures reaching +44°C (+3.8σ).",
            "expected_phenomenon": "Extensive contiguous high-temperature footprint exceeding 3-sigma climatological normal.",
            "data_provenance": "DEMO_SYNTHETIC_DATASET",
            "is_simulated": True,
        },
        {
            "scenario_id": "coldwave",
            "name": "Arctic Cold Wave Outbreak",
            "type": "Cold Wave",
            "category_key": "cold_wave",
            "lead_time_hours": 72,
            "seed": 202,
            "region": "Siberian High-Latitude Sector",
            "description": "Deep polar vortex plunge pushing Arctic sub-zero thermal airmass down to -28°C below normal (-3.6σ).",
            "expected_phenomenon": "Broad negative temperature anomaly footprint exceeding extreme cold threshold.",
            "data_provenance": "DEMO_SYNTHETIC_DATASET",
            "is_simulated": True,
        },
        {
            "scenario_id": "all",
            "name": "Full Multi-Hazard Benchmark",
            "type": "Multi-Hazard",
            "category_key": "all",
            "lead_time_hours": 24,
            "seed": 42,
            "region": "Global / South Asia",
            "description": "Comprehensive synoptic grid containing all 5 injected extreme weather phenomena simultaneously.",
            "expected_phenomenon": "Multiple concurrent anomaly clusters extracted across thermal, pressure, and wind fields.",
            "data_provenance": "DEMO_SYNTHETIC_DATASET",
            "is_simulated": True,
        },
    ]


@router.post(
    "/detection/run",
    response_model=PipelineExecutionResult,
    summary="Run Weather Anomaly Detection Pipeline",
    description=(
        "Executes the end-to-end scientific detection pipeline on gridded numerical weather fields. "
        "Performs coordinate validation, canonical unit conversion, multi-variable anomaly scoring, "
        "SciPy morphological connected-component clustering, and Shapely GeoJSON footprint extraction."
    ),
)
def run_detection(request: DetectionRunRequest = Body(...)):
    logger.info(f"Initiating anomaly detection run for lead_time_hours={request.lead_time_hours}, scenario={request.scenario}")

    try:
        # 1. Generate or load the dataset
        dataset, _ = SyntheticWeatherGenerator.generate_dataset(
            lead_time_hours=request.lead_time_hours,
            seed=request.seed,
            scenario=request.scenario,
        )

        # 2. Configure pipeline
        config = EngineConfig()
        if request.min_area_km2 is not None:
            config.footprint.min_area_km2 = request.min_area_km2
        config.footprint.connectivity = request.connectivity

        # 3. Execute pipeline
        pipeline = AnomalyDetectionPipeline(config=config)
        result = pipeline.run(dataset=dataset)

        # Cache detected events so /api/anomalies/{id} and /api/anomalies/{id}/score work seamlessly
        AnomalyService.register_dynamic_events(result.events)

        logger.info(
            f"Detection completed in {result.execution_time_ms} ms. "
            f"Found {result.total_anomalies_detected} anomalies, "
            f"{result.total_footprints_extracted} footprints."
        )

        return result

    except Exception as e:
        logger.error(f"Error during anomaly detection run: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Detection pipeline execution failure: {str(e)}"
        )
