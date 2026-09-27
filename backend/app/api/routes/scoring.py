"""
FastAPI Routes for Anomaly Scoring and Explainability
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Path, Body
from pydantic import BaseModel, Field

from app.ml.schemas import (
    CompositeAnomalyScore,
    ScoringWeightsConfig,
)
from app.ml.scoring import AnomalyScoringService
from app.data.demo_data import ANOMALIES_CATALOG
from app.services.anomaly_service import AnomalyService

router = APIRouter(tags=["Anomaly Scoring"])


class ScoringComputeRequest(BaseModel):
    event_id: Optional[str] = Field(default="custom_query", description="Identifier for scoring context")
    observed_temperature: Optional[float] = Field(default=None, description="Observed temperature in °C")
    baseline_temperature: Optional[float] = Field(default=28.0, description="Baseline normal temperature in °C")
    clim_temp_std: Optional[float] = Field(default=2.5, description="Climatological temperature standard deviation")
    max_wind_kmh: Optional[float] = Field(default=None, description="Maximum sustained wind speed in km/h")
    min_mslp_hpa: Optional[float] = Field(default=None, description="Minimum central sea level pressure in hPa")
    area_km2: Optional[float] = Field(default=None, description="Surface area in square kilometers")
    forecast_days: Optional[List[int]] = Field(default=None, description="Active forecast horizon lead days")
    missing_cell_fraction: float = Field(default=0.0, ge=0.0, le=1.0, description="Fraction of missing grid cells")
    weights: Optional[ScoringWeightsConfig] = None


@router.get(
    "/anomalies/{anomaly_id}/score",
    response_model=CompositeAnomalyScore,
    summary="Multi-Component Normalized Anomaly Score",
    description="Deconstructs an anomaly event into normalized dimensionless components with weightings and interpretation."
)
def get_anomaly_score(
    anomaly_id: str = Path(..., description="Unique anomaly ID, e.g. evt-001")
) -> CompositeAnomalyScore:
    event = next((a for a in ANOMALIES_CATALOG if a["id"].lower() == anomaly_id.lower()), None)
    if not event:
        event = AnomalyService.get_dynamic_event(anomaly_id)
    if not event:
        raise HTTPException(
            status_code=404,
            detail=f"Anomaly event '{anomaly_id}' not found in active catalog."
        )

    # Extract physical diagnostic measurements
    metrics = event.get("meteorological_metrics", {})
    obs_temp = None
    if "peak_temperature_c" in metrics:
        obs_temp = metrics["peak_temperature_c"]
    elif "temperature" in event.get("primary_variable", "").lower():
        obs_temp = 42.5

    max_wind = metrics.get("max_sustained_wind_kmh")
    if max_wind is None and event.get("max_wind"):
        try:
            max_wind = float(event["max_wind"].split()[0])
        except (ValueError, IndexError):
            pass

    min_mslp = metrics.get("central_mslp_hpa")
    if min_mslp is None and event.get("central_pressure"):
        try:
            min_mslp = float(event["central_pressure"].split()[0])
        except (ValueError, IndexError):
            pass

    area_km2 = event.get("estimated_area_km2", 25000.0)
    forecast_days = event.get("forecast_days", [1, 2, 3])

    return AnomalyScoringService.compute_composite_score(
        event_id=anomaly_id,
        observed_temperature=obs_temp,
        baseline_temperature=28.0,
        clim_temp_std=2.5,
        max_wind_kmh=max_wind,
        min_mslp_hpa=min_mslp,
        area_km2=area_km2,
        forecast_days=forecast_days,
        missing_cell_fraction=0.0
    )


@router.post(
    "/scoring/compute",
    response_model=CompositeAnomalyScore,
    summary="Compute Custom Anomaly Score",
    description="Calculates normalized composite anomaly score from arbitrary physical values and custom component weights."
)
def compute_custom_score(request: ScoringComputeRequest = Body(...)) -> CompositeAnomalyScore:
    return AnomalyScoringService.compute_composite_score(
        event_id=request.event_id or "custom_calculation",
        observed_temperature=request.observed_temperature,
        baseline_temperature=request.baseline_temperature,
        clim_temp_std=request.clim_temp_std,
        max_wind_kmh=request.max_wind_kmh,
        min_mslp_hpa=request.min_mslp_hpa,
        area_km2=request.area_km2,
        forecast_days=request.forecast_days,
        missing_cell_fraction=request.missing_cell_fraction,
        weights=request.weights
    )
