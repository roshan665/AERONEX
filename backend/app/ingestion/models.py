"""
Pydantic Schemas for NWP Data Ingestion, Dataset Metadata, and Quality Reports
"""

from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


class NWPVariableInfo(BaseModel):
    """Metadata and statistics for a single ingested meteorological variable."""
    provider_var_name: str
    standard_var_name: str
    original_units: str
    target_units: str
    shape: Tuple[int, ...]
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    mean_val: Optional[float] = None
    missing_count: int = 0
    missing_fraction: float = 0.0


class NWPValidationReport(BaseModel):
    """Comprehensive validation report for a real NWP file/dataset."""
    dataset_id: str
    file_path: Optional[str] = None
    file_format: str
    is_valid: bool
    file_readable: bool
    passed_checks: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    detected_variables: List[NWPVariableInfo] = Field(default_factory=list)
    missing_expected_variables: List[str] = Field(default_factory=list)
    unsupported_fields: List[str] = Field(default_factory=list)
    grid_shape: Tuple[int, int] = (0, 0)
    lat_bounds: Tuple[float, float] = (0.0, 0.0)
    lon_bounds: Tuple[float, float] = (0.0, 0.0)
    resolution_deg: float = 0.25
    forecast_init_time: Optional[str] = None
    valid_time: Optional[str] = None
    lead_time_hours: Optional[int] = None
    processing_duration_ms: float = 0.0


class DatasetSummary(BaseModel):
    """High-level summary of an available or cached NWP forecast dataset."""
    dataset_id: str
    name: str
    provider: str
    file_format: str
    cycle_date: str
    cycle_hour: str
    lead_time_hours: int
    spatial_resolution_deg: float
    region_name: str
    geographic_bounds: List[float] = Field(..., description="[min_lat, max_lat, min_lon, max_lon]")
    variables: List[str]
    file_size_bytes: int
    is_cached: bool = True
    is_real_data: bool = True
    data_provenance: str = "REAL_NOAA_GFS"


class IngestionRunRequest(BaseModel):
    """Request payload to initiate ingestion of a real NWP dataset."""
    dataset_id: Optional[str] = Field(default="local_gfs_south_asia", description="Dataset identifier")
    source_mode: str = Field(default="local", description="'local' file or 'remote_nomads' retrieval")
    cycle_date: Optional[str] = Field(default=None, description="Cycle date string YYYYMMDD, e.g. '20260926'")
    cycle_hour: str = Field(default="00", description="Forecast cycle: '00', '06', '12', '18'")
    lead_time_hours: int = Field(default=24, ge=0, le=240, description="Forecast lead time in hours")
    region_id: str = Field(default="south_asia", description="Geographic region key, e.g. 'south_asia', 'global', or 'custom'")
    custom_bounds: Optional[List[float]] = Field(default=None, description="Custom bounds [min_lat, max_lat, min_lon, max_lon]")
    variables: List[str] = Field(default_factory=lambda: ["temperature", "wind", "mslp"], description="Variables to ingest")
    run_anomaly_detection: bool = Field(default=True, description="Automatically run anomaly detector on ingested fields")
    min_area_km2: Optional[float] = Field(default=2500.0, description="Minimum footprint surface area in km²")


class IngestionRunResponse(BaseModel):
    """Response returned upon completion of real NWP ingestion and anomaly processing."""
    success: bool
    message: str
    dataset_id: str
    data_source: str
    is_real_data: bool
    data_provenance: str
    validation_report: NWPValidationReport
    anomalies_detected_count: int = 0
    footprints_extracted_count: int = 0
    anomalies: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float = 0.0


class IngestionStatusResponse(BaseModel):
    """Current status of the ingestion pipeline and active backend data mode."""
    status: str
    active_data_source: str
    active_data_mode: str
    last_ingested_dataset: Optional[str] = None
    last_ingestion_time: Optional[str] = None
    cached_datasets_count: int = 0
    available_providers: List[str] = Field(default_factory=list)
