"""
Pydantic Models for Weather Anomaly Events and Footprints
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AnomalyEvent(BaseModel):
    id: str = Field(..., description="Unique anomaly event identifier")
    name: str = Field(..., description="Display name of event")
    type: str = Field(..., description="Hazard taxonomy: Cyclone, Heat Wave, Cold Wave, etc.")
    category_key: str = Field(..., description="Machine-readable key: cyclone, heat_wave, etc.")
    region: str = Field(..., description="Geographic region sector")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Centroid latitude")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Centroid longitude")
    coordinates_display: str = Field(..., description="Human readable coordinate format")
    forecast_window: str = Field(..., description="Lead time window, e.g. Day 2 – Day 5")
    forecast_days: List[int] = Field(..., description="Active lead days array")
    severity: str = Field(..., description="Severity tier: High, Medium, Low")
    severity_level: int = Field(..., ge=1, le=4, description="Numeric severity (1 to 4)")
    estimated_area: str = Field(..., description="Display area string")
    estimated_area_km2: float = Field(..., description="Numeric area in square kilometers")
    max_wind: str = Field(..., description="Maximum estimated sustained wind")
    central_pressure: str = Field(..., description="Minimum central sea level pressure")
    anomaly_score: str = Field(..., description="Z-score deviation or deficit score")
    color: str = Field(..., description="Visual display hex code")
    description: str = Field(..., description="Scientific meteorological synopsis")
    updated_ago: str = Field(..., description="Relative detection time label")
    detection_timestamp: str = Field(..., description="UTC ISO 8601 detection time")
    is_simulated: bool = Field(default=True, description="Always true for demonstration datasets")
    
    # Extended Scientific Metadata (Phase 4 Anomaly Engine)
    primary_variable: Optional[str] = Field(default=None, description="Primary meteorological variable driving detection")
    detection_method: Optional[str] = Field(default=None, description="Detection methodology (Threshold, Z-score, or Hybrid)")
    forecast_init_time: Optional[str] = Field(default=None, description="ISO 8601 initialization timestamp")
    valid_time: Optional[str] = Field(default=None, description="ISO 8601 forecast valid timestamp")
    forecast_lead_day: Optional[int] = Field(default=None, description="Forecast lead day index")
    geographic_bounds: Optional[List[float]] = Field(default=None, description="[min_lon, min_lat, max_lon, max_lat]")
    grid_cell_count: Optional[int] = Field(default=None, description="Contiguous grid cell count in footprint")
    max_anomaly_magnitude: Optional[float] = Field(default=None, description="Peak anomaly magnitude score")
    mean_anomaly_magnitude: Optional[float] = Field(default=None, description="Average anomaly magnitude score across footprint")
    relevant_units: Optional[str] = Field(default=None, description="Canonical physical units of measurement")
    supporting_measurements: Optional[Dict[str, Any]] = Field(default=None, description="Detailed physical diagnostic metrics")
    geometry: Optional[Dict[str, Any]] = Field(default=None, description="GeoJSON Polygon geometry dictionary")
    data_source: Optional[str] = Field(default="DEMO_SYNTHETIC_DATASET", description="Data source provenance identifier")
    data_quality_warnings: Optional[List[str]] = Field(default_factory=list, description="Preprocessing warnings and data quality notes")


class TrajectoryStep(BaseModel):
    day: int
    lat: float
    lon: float
    intensity_note: str


class AnomalyDetailResponse(BaseModel):
    event: AnomalyEvent
    footprint_polygon: List[List[float]] = Field(..., description="Contour vertices [[lat, lon], ...]")
    forecast_track: List[List[float]] = Field(..., description="Trajectory vector points [[lat, lon], ...]")
    trajectory_steps: List[TrajectoryStep] = Field(default_factory=list)
    meteorological_metrics: Dict[str, Any] = Field(default_factory=dict)
    data_provenance: str = "DEMO_SYNTHETIC_DATASET"
    is_simulated: bool = True
    disclaimer: str


class AnomalyListResponse(BaseModel):
    total: int
    count: int
    events: List[AnomalyEvent]
    data_provenance: str = "DEMO_SYNTHETIC_DATASET"
    is_simulated: bool = True
    disclaimer: str
