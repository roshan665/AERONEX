"""
Dashboard Overview & Executive KPIs Route
"""

from typing import Optional
from fastapi import APIRouter, Query
from app.models.overview import OverviewResponse
from app.services.overview_service import OverviewService

router = APIRouter(tags=["Overview"])


@router.get(
    "/overview",
    response_model=OverviewResponse,
    summary="Dashboard Executive Overview",
    description="Returns aggregated metrics, active anomaly counts, severity distributions, and critical alert tickers for dashboard cards.",
)
def get_overview(
    region_id: Optional[str] = Query(
        None, 
        description="Filter overview metrics to a specific region sector (e.g. western_indian_ocean)"
    )
):
    return OverviewService.get_overview(region_id=region_id)
