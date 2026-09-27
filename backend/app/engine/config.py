"""
AeroNex Anomaly Detection Engine — Configuration Parameters
"""

from typing import Dict, Any, Literal
from pydantic import BaseModel, Field


class DetectorThresholds(BaseModel):
    # Temperature Thresholds (°C)
    extreme_heat_celsius: float = Field(default=40.0, description="Absolute threshold for extreme heat anomaly")
    severe_heat_celsius: float = Field(default=43.0, description="Threshold for severe/extreme heat dome")
    extreme_cold_celsius: float = Field(default=4.0, description="Absolute threshold for cold wave condition")
    severe_cold_celsius: float = Field(default=-10.0, description="Threshold for severe freezing cold wave")
    temp_zscore_threshold: float = Field(default=2.5, description="Z-score deviation threshold for temperature")

    # Wind Thresholds (m/s) [1 m/s = 3.6 km/h]
    gale_wind_ms: float = Field(default=17.5, description="Gale-force threshold (~63 km/h)")
    storm_wind_ms: float = Field(default=24.5, description="Storm-force wind threshold (~88 km/h)")
    hurricane_wind_ms: float = Field(default=32.7, description="Hurricane-force wind threshold (~118 km/h)")
    wind_zscore_threshold: float = Field(default=2.5, description="Z-score deviation threshold for wind speed")

    # Barometric Pressure Thresholds (hPa)
    low_pressure_hpa: float = Field(default=998.0, description="Low pressure depression threshold")
    deep_depression_hpa: float = Field(default=988.0, description="Deep depression threshold")
    cyclonic_core_hpa: float = Field(default=978.0, description="Severe cyclonic central pressure threshold")
    pressure_zscore_threshold: float = Field(default=-2.5, description="Negative Z-score threshold for barometric deficit")

    # Precipitation Thresholds (mm / 24h accumulation)
    heavy_rain_mm: float = Field(default=64.5, description="Heavy rainfall threshold (IMD/WMO standard)")
    very_heavy_rain_mm: float = Field(default=115.5, description="Very heavy rainfall threshold")
    extreme_rain_mm: float = Field(default=204.5, description="Extremely heavy rainfall threshold")
    precip_zscore_threshold: float = Field(default=3.0, description="Z-score deviation for rainfall")


class FootprintConfig(BaseModel):
    connectivity: Literal[4, 8] = Field(default=8, description="Morphological connectivity (4- or 8-neighbor)")
    min_cells: int = Field(default=5, ge=1, description="Minimum grid cells to qualify as a weather system")
    min_area_km2: float = Field(default=2500.0, ge=0.0, description="Minimum physical surface area filter in km²")
    simplify_tolerance_deg: float = Field(default=0.05, description="Douglas-Peucker simplification tolerance in degrees")


class TemporalTrackingConfig(BaseModel):
    iou_threshold: float = Field(default=0.15, ge=0.0, le=1.0, description="Minimum IoU overlap to link consecutive timesteps")
    max_centroid_displacement_km: float = Field(default=850.0, description="Maximum plausible physical movement per 24h")


class EngineConfig(BaseModel):
    baseline_strategy: Literal["threshold", "climatology_zscore", "hybrid"] = "hybrid"
    thresholds: DetectorThresholds = Field(default_factory=DetectorThresholds)
    footprint: FootprintConfig = Field(default_factory=FootprintConfig)
    tracking: TemporalTrackingConfig = Field(default_factory=TemporalTrackingConfig)
    standardization_epsilon: float = 1e-6


engine_config = EngineConfig()
