"""
Forecast Exploration & Horizon Time-Series Route
"""

from typing import Optional
from fastapi import APIRouter, Query, Path
from app.models.forecast import ForecastResponse, ForecastRunMetadata
from app.services.forecast_service import ForecastService

router = APIRouter(tags=["Forecast Explorer"])


@router.get(
    "/forecasts",
    response_model=ForecastResponse,
    summary="Multi-Variable 10-Day Forecast Slices",
    description="Returns 10-day time-series predictions and uncertainty envelopes across temperature, wind, pressure, or precipitation.",
)
def get_forecasts(
    variable: str = Query(
        "temperature", 
        description="Meteorological variable: 'temperature', 'wind', 'pressure', 'precipitation'"
    ),
    region_id: Optional[str] = Query(
        None, 
        description="Filter to a specific region sector"
    ),
    lead_day: Optional[int] = Query(
        None, 
        ge=1, 
        le=10, 
        description="Filter to a specific lead day (1 to 10)"
    ),
):
    return ForecastService.get_forecasts(
        variable=variable,
        region_id=region_id,
        lead_day=lead_day,
    )


@router.get(
    "/forecasts/{forecast_id}",
    response_model=ForecastRunMetadata,
    summary="NWP Forecast Run Metadata",
    description="Retrieves initialization, resolution, and dimension descriptors for a specific model run.",
)
def get_forecast_run(
    forecast_id: str = Path(
        ..., 
        description="Unique model cycle ID, e.g. GFS-20250426-00Z"
    )
):
    return ForecastService.get_forecast_by_id(forecast_id=forecast_id)
