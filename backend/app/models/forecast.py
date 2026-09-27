"""
Pydantic Models for Numerical Weather Forecast Time-Series
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ForecastTimelineItem(BaseModel):
    day: str = Field(..., description="Day label, e.g. Day 1")
    lead_day: int = Field(..., ge=1, le=10, description="Lead day number 1-10")
    lead_time_hours: int = Field(..., description="Lead time in hours (lead_day * 24)")
    valid_time: str = Field(..., description="ISO 8601 UTC valid forecast timestamp")
    global_avg: float = Field(..., description="Deterministic spatial average")
    max: float = Field(..., description="Maximum regional extreme peak")
    min: float = Field(..., description="Minimum regional baseline")
    uncertainty_upper: float = Field(..., description="90th percentile simulated ensemble spread")
    uncertainty_lower: float = Field(..., description="10th percentile simulated ensemble spread")
    confidence_rating: str = Field(..., description="Confidence level: HIGH, MODERATE, TREND_ONLY")


class ForecastResponse(BaseModel):
    forecast_id: str
    variable: str
    variable_name: str
    unit: str
    model_initialization: str
    region_id: Optional[str] = None
    horizon_days: int = 10
    timeline: List[ForecastTimelineItem]
    data_provenance: str = "DEMO_SYNTHETIC_DATASET"
    is_simulated: bool = True
    disclaimer: str


class ForecastRunMetadata(BaseModel):
    forecast_id: str
    model_name: str
    initialization_time: str
    spatial_resolution_deg: float
    spatial_resolution: Optional[str] = None
    grid_dimensions: Dict[str, int]
    available_lead_times_hours: List[int]
    available_variables: List[str]
    format: str
    data_provenance: str = "DEMO_SYNTHETIC_DATASET"
    is_simulated: bool = True

