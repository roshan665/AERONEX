"""
Anomaly Detection & Footprint Catalog Route
"""

from typing import Optional
from fastapi import APIRouter, Query, Path
from app.models.anomaly import AnomalyListResponse, AnomalyDetailResponse
from app.services.anomaly_service import AnomalyService

router = APIRouter(tags=["Anomaly Detection"])


@router.get(
    "/anomalies",
    response_model=AnomalyListResponse,
    summary="List Tracked Weather Anomalies",
    description="Queries detected cyclones, heat domes, cold waves, and pressure anomalies with multi-attribute filtering.",
)
def get_anomalies(
    category_key: Optional[str] = Query(
        None, 
        description="Filter by category key: 'cyclone', 'heat_wave', 'cold_wave', 'wind_anomaly', 'pressure_anomaly', or 'ALL'"
    ),
    severity: Optional[str] = Query(
        None, 
        description="Filter by severity tier: 'High', 'Medium', 'Low', or 'ALL'"
    ),
    region: Optional[str] = Query(
        None, 
        description="Search/filter by region name"
    ),
    forecast_day: Optional[int] = Query(
        None, 
        ge=1, 
        le=10, 
        description="Filter events active during a specific forecast day (1 to 10)"
    ),
    min_area_km2: Optional[float] = Query(
        None, 
        ge=0.0, 
        description="Filter out anomalies below a minimum surface area threshold"
    ),
):
    return AnomalyService.get_anomalies(
        category_key=category_key,
        severity=severity,
        region=region,
        forecast_day=forecast_day,
        min_area_km2=min_area_km2,
    )


@router.get(
    "/anomalies/{anomaly_id}",
    response_model=AnomalyDetailResponse,
    summary="Anomaly Diagnostic Telemetry",
    description="Retrieves granular diagnostic metrics, closed polygon boundary contours, and forecast trajectory vectors for a single event.",
)
def get_anomaly_detail(
    anomaly_id: str = Path(
        ..., 
        description="Unique anomaly ID, e.g. evt-001"
    )
):
    return AnomalyService.get_anomaly_by_id(anomaly_id=anomaly_id)
