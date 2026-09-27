"""
Monitored Geographic Sectors Route
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Path
from app.services.region_service import RegionService

router = APIRouter(tags=["Regions"])


@router.get(
    "/regions",
    response_model=List[Dict[str, Any]],
    summary="List Monitored Geographic Sectors",
    description="Returns predefined demonstration bounding boxes, center coordinates, and monitoring statuses for spatial sectors.",
)
def get_regions():
    return RegionService.get_regions()


@router.get(
    "/regions/{region_id}",
    response_model=Dict[str, Any],
    summary="Geographic Sector Descriptor",
    description="Retrieves bounding box and center coordinates for a specific sector.",
)
def get_region_detail(
    region_id: str = Path(
        ..., 
        description="Region identifier (e.g. western_indian_ocean)"
    )
):
    return RegionService.get_region_by_id(region_id=region_id)
