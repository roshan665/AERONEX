"""
Data Schemas for Weather Grid Inputs, Normalized Representations, and Detection Outputs
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from pydantic import BaseModel, Field


class WeatherGridDataset(BaseModel):
    """
    Input schema for raw Numerical Weather Prediction (NWP) or synthetic gridded datasets.
    """
    model_config = {"arbitrary_types_allowed": True}

    forecast_init_time: str = Field(..., description="ISO 8601 UTC model run initialization")
    valid_time: str = Field(..., description="ISO 8601 UTC target forecast valid time")
    lead_time_hours: int = Field(..., ge=0, description="Lead time from initialization in hours")
    
    # 1D Coordinate Arrays
    lats: np.ndarray = Field(..., description="1D NumPy array of latitudes in [-90.0, 90.0]")
    lons: np.ndarray = Field(..., description="1D NumPy array of longitudes in [-180.0, 180.0]")
    
    # 2D Gridded Variables (shape: len(lats) x len(lons))
    variables: Dict[str, np.ndarray] = Field(
        ..., 
        description="Dictionary mapping variable key ('temperature', 'mslp', etc.) to 2D numpy array"
    )
    units: Dict[str, str] = Field(
        ..., 
        description="Declared units for each variable, e.g. {'temperature': 'K', 'mslp': 'Pa'}"
    )
    
    # Optional Climatological Baselines for Z-score calculation
    climatology_mean: Optional[Dict[str, np.ndarray]] = None
    climatology_std: Optional[Dict[str, np.ndarray]] = None
    
    is_simulated: bool = Field(default=True, description="Always true for demonstration datasets")
    data_source: str = Field(default="SYNTHETIC_NWP_GRID", description="Provenance identifier")


class NormalizedWeatherGrid(BaseModel):
    """
    Preprocessed canonical representation with standardized units:
    - Temperature: °C
    - Wind Speed: m/s
    - Pressure: hPa
    - Precipitation: mm
    """
    model_config = {"arbitrary_types_allowed": True}

    forecast_init_time: str
    valid_time: str
    lead_time_hours: int
    lead_day: int
    lats: np.ndarray
    lons: np.ndarray
    shape: Tuple[int, int]
    
    # Canonical 2D Arrays
    temperature_celsius: Optional[np.ndarray] = None
    wind_speed_ms: Optional[np.ndarray] = None
    mslp_hpa: Optional[np.ndarray] = None
    precipitation_mm: Optional[np.ndarray] = None
    precipitation_accumulation_hours: Optional[int] = 24
    
    # Optional Climatological Baselines (in canonical units)
    temp_clim_mean: Optional[np.ndarray] = None
    temp_clim_std: Optional[np.ndarray] = None
    wind_clim_mean: Optional[np.ndarray] = None
    wind_clim_std: Optional[np.ndarray] = None
    mslp_clim_mean: Optional[np.ndarray] = None
    mslp_clim_std: Optional[np.ndarray] = None
    
    preprocessing_warnings: List[str] = Field(default_factory=list)
    is_simulated: bool = True
    data_source: str = "SYNTHETIC_NWP_GRID"


class DetectionResult(BaseModel):
    """
    Intermediate output from an individual meteorological variable detector.
    """
    model_config = {"arbitrary_types_allowed": True}

    variable: str
    category: str
    method: str
    mask: np.ndarray = Field(..., description="2D boolean mask of anomalous cells")
    score_grid: np.ndarray = Field(..., description="2D float grid of continuous anomaly scores (Z-score or deficit)")
    threshold_value: float
    canonical_unit: str
    detected_cell_count: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FootprintEntity(BaseModel):
    """
    Spatial cluster extracted from an anomaly mask with vector geometry.
    """
    cluster_id: int
    event_id: str
    name: str
    category: str
    hazard_type: str
    severity: str
    severity_level: int
    primary_variable: str
    canonical_unit: str
    
    # Geographic properties
    centroid_lat: float
    centroid_lon: float
    coordinates_display: str
    bounds: List[float] = Field(..., description="[min_lon, min_lat, max_lon, max_lat]")
    estimated_area_km2: float
    cell_count: int
    
    # Anomaly metrics
    max_anomaly_score: float
    mean_anomaly_score: float
    peak_metric_value: float
    
    # GeoJSON coordinates format: [[[lon, lat], ...]]
    polygon_coordinates: List[List[List[float]]]
    supporting_metrics: Dict[str, Any] = Field(default_factory=dict)
    detection_method: str
    is_simulated: bool = True
