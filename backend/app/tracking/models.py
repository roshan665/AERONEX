"""
Pydantic Models for Event Tracking, Trajectory Evolution, and Forecast Uncertainty
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TrackPoint(BaseModel):
    """Detection state of a tracked anomaly at a specific forecast timestep."""
    frame_index: int = Field(..., description="0-indexed sequence of forecast frames")
    step_hours: int = Field(..., description="Forecast lead time in hours (e.g. 24, 48, 72)")
    forecast_day: int = Field(..., description="Forecast horizon day (1 to 10)")
    valid_time: str = Field(..., description="ISO 8601 UTC timestamp when forecast is valid")
    detection_status: str = Field(
        ..., 
        description="'DETECTED' if present, 'MISSING' if unassociated at this frame, 'DISSIPATED' if decayed"
    )
    event_id: Optional[str] = Field(default=None, description="Detection event snapshot ID at this frame")
    centroid_lat: Optional[float] = Field(default=None, description="Footprint centroid latitude")
    centroid_lon: Optional[float] = Field(default=None, description="Footprint centroid longitude")
    coordinates_display: Optional[str] = Field(default=None, description="Formatted coordinate string")
    estimated_area_km2: Optional[float] = Field(default=None, description="Estimated ground surface area in km²")
    max_magnitude: Optional[float] = Field(default=None, description="Peak metric value or anomaly score")
    magnitude_unit: Optional[str] = Field(default=None, description="Unit of peak metric (e.g. 'km/h', '°C', 'hPa')")
    severity: Optional[str] = Field(default=None, description="'Low', 'Medium', 'High', 'Critical'")
    polygon_coordinates: Optional[List[List[float]]] = Field(
        default=None, 
        description="GeoJSON exterior ring [[lon, lat], ...]"
    )
    displacement_km: Optional[float] = Field(
        default=None, 
        description="Great-Circle distance in km from previous detected centroid"
    )
    bearing_deg: Optional[float] = Field(
        default=None, 
        description="Forward azimuth in degrees [0, 360) from previous centroid"
    )
    bearing_cardinal: Optional[str] = Field(
        default=None, 
        description="Cardinal direction (e.g. 'NW', 'E', 'SSE')"
    )
    speed_kmh: Optional[float] = Field(
        default=None, 
        description="Footprint translation speed in km/h between detected frames"
    )
    area_change_km2: Optional[float] = Field(default=None, description="Change in footprint area from previous frame")
    area_change_pct: Optional[float] = Field(default=None, description="Percentage change in footprint area")
    magnitude_change: Optional[float] = Field(default=None, description="Change in peak magnitude from previous frame")


class EventTrackSummary(BaseModel):
    """High-level summary of a tracked anomaly series across forecast horizons."""
    track_id: str = Field(..., description="Stable unique identifier for the tracked series (e.g. 'TRK-CYC-001')")
    name: str = Field(..., description="Human-readable event name")
    category: str = Field(..., description="Internal category key: cyclone, heat_wave, cold_wave, etc.")
    hazard_type: str = Field(..., description="Display label for hazard type")
    first_detection_lead_hours: int = Field(..., description="Lead time (hours) of initial detection")
    latest_detection_lead_hours: int = Field(..., description="Lead time (hours) of latest active detection")
    total_detections: int = Field(..., description="Number of frames where event was detected")
    total_frames: int = Field(..., description="Total forecast frames in evaluation window")
    initial_centroid: Optional[List[float]] = Field(default=None, description="Initial [lat, lon]")
    latest_centroid: Optional[List[float]] = Field(default=None, description="Latest [lat, lon]")
    cumulative_distance_km: float = Field(default=0.0, description="Total path length traveled by centroid (km)")
    net_displacement_km: float = Field(default=0.0, description="Straight-line distance from initial to latest centroid")
    mean_speed_kmh: float = Field(default=0.0, description="Average translation speed across active steps")
    peak_magnitude: Optional[float] = Field(default=None, description="Highest magnitude across all frames")
    magnitude_unit: Optional[str] = Field(default=None, description="Unit of magnitude metric")
    peak_severity: str = Field(default="Low", description="Highest severity reached across frames")
    max_area_km2: float = Field(default=0.0, description="Maximum surface area reached across frames")
    status: str = Field(default="ACTIVE", description="'ACTIVE', 'DISSIPATED', 'INTERMITTENT'")
    trajectory_line: List[List[float]] = Field(
        default_factory=list, 
        description="Path coordinates [[lat, lon], ...] for map polylines"
    )
    color: str = Field(default="#FF4568", description="Hex color token")
    data_provenance: str = Field(default="DEMO_SYNTHETIC_DATASET", description="Data provenance label")
    is_simulated: bool = Field(default=True, description="True if simulated demo data")


class EventTrackDetail(EventTrackSummary):
    """Detailed profile of a tracked series including all chronological frames and notes."""
    points: List[TrackPoint] = Field(default_factory=list, description="Chronological detection frames")
    movement_notes: str = Field(
        default=(
            "Derived movement represents displacement of detected forecast footprint centroids "
            "across successive forecast frames; it does not constitute a verified physical storm track."
        ),
        description="Scientific caveat regarding derived tracking"
    )
    uncertainty_summary: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Associated forecast uncertainty metrics"
    )


class UncertaintyLeadTimeBand(BaseModel):
    """Forecast lead time confidence decay guide."""
    day: int
    step_hours: int
    confidence_pct: float
    confidence_level: str = Field(..., description="'HIGH', 'MODERATE', 'LOW_TREND_ONLY'")
    description: str


class UncertaintySummaryResponse(BaseModel):
    """System-level uncertainty capability and status report."""
    uncertainty_mode: str = Field(
        ..., 
        description="'DETERMINISTIC_ONLY' for single-run forecasts, 'ENSEMBLE_MEMBERS' if multi-member data available"
    )
    is_available: bool = Field(..., description="True if genuine multi-member ensemble spread is available")
    ensemble_members_count: int = Field(..., description="Number of ensemble members evaluated (1 if deterministic)")
    primary_provider: str = Field(..., description="Underlying NWP source provider")
    message: str = Field(..., description="Human-readable uncertainty description and caveats")
    lead_time_decay: List[UncertaintyLeadTimeBand] = Field(
        default_factory=list, 
        description="Forecast confidence decay profile by lead time"
    )
    known_limitations: List[str] = Field(
        default_factory=list, 
        description="Documented meteorological limitations of the active dataset"
    )


class MemberPrediction(BaseModel):
    """Individual ensemble member prediction point for an event."""
    member_id: str
    centroid_lat: float
    centroid_lon: float
    estimated_area_km2: float
    peak_magnitude: float
    is_detected: bool = True


class DailyEnsembleSpread(BaseModel):
    """Ensemble spread metrics for a single forecast day."""
    forecast_day: int
    step_hours: int
    members_count: int
    member_agreement_pct: float
    mean_centroid: List[float] = Field(..., description="[lat, lon]")
    centroid_spatial_dispersion_km: float = Field(
        ..., 
        description="Average distance of member centroids from ensemble mean centroid"
    )
    area_mean_km2: float
    area_std_km2: float
    area_iqr_km2: float
    magnitude_mean: float
    magnitude_std: float
    magnitude_unit: str
    member_centroids: List[List[float]] = Field(default_factory=list, description="[[lat, lon], ...] for all members")


class EventUncertaintyDetail(BaseModel):
    """Comprehensive uncertainty profile for an event or track."""
    event_id: str
    track_id: Optional[str] = None
    uncertainty_mode: str
    is_available: bool
    ensemble_members_count: int
    daily_spread: List[DailyEnsembleSpread] = Field(
        default_factory=list, 
        description="Per-day ensemble spread metrics if available"
    )
    lead_time_decay: List[UncertaintyLeadTimeBand] = Field(
        default_factory=list, 
        description="Standard lead-time confidence decay bands"
    )
    methodology_notes: str = Field(
        default="Deterministic forecasts convey lead-time decay; ensemble statistics are computed across aligned members."
    )
    known_limitations: List[str] = Field(default_factory=list)
