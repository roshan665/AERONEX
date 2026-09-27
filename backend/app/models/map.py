"""
Pydantic Models for Map Layers & GeoJSON (RFC 7946) Structures
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class MapLegendStop(BaseModel):
    value: float
    color: str


class MapLayerRange(BaseModel):
    min: float
    max: float


class MapLayerDescriptor(BaseModel):
    layer_id: str
    display_name: str
    unit: str
    default_active: bool
    category: str
    color_scale: str
    range: MapLayerRange
    legend_stops: List[MapLegendStop]


class GeoJsonGeometry(BaseModel):
    type: str = Field(..., description="Polygon, LineString, Point, etc.")
    coordinates: Any = Field(..., description="GeoJSON coordinates: [longitude, latitude]")


class GeoJsonFeature(BaseModel):
    type: str = "Feature"
    id: Optional[str] = None
    geometry: GeoJsonGeometry
    properties: Dict[str, Any]


class GeoJsonFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    metadata: Dict[str, Any]
    features: List[GeoJsonFeature]


class MapLayersResponse(BaseModel):
    available_layers: List[MapLayerDescriptor]
    anomalies_geojson: GeoJsonFeatureCollection
    tracks_geojson: GeoJsonFeatureCollection
    geojson: Optional[GeoJsonFeatureCollection] = None
    data_provenance: str = "DEMO_SYNTHETIC_DATASET"
    is_simulated: bool = True

