"""
Map Layers & GeoJSON Vector Features Route
"""

from fastapi import APIRouter
from app.models.map import MapLayersResponse
from app.services.map_service import MapService

router = APIRouter(tags=["Interactive Weather Map"])


@router.get(
    "/map/layers",
    response_model=MapLayersResponse,
    summary="Interactive Weather Map Layer Descriptors & GeoJSON",
    description="Supplies layer display settings, continuous color ramp stops, and RFC 7946 GeoJSON FeatureCollections for client rendering.",
)
def get_map_layers():
    return MapService.get_map_layers()
