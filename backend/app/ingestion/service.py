"""
Ingestion Service: Orchestrator for Real NWP Dataset Ingestion, Quality Audits, and Anomaly Detection
"""

import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.ingestion.models import (
    DatasetSummary,
    NWPValidationReport,
    IngestionRunRequest,
    IngestionRunResponse,
    IngestionStatusResponse,
)
from app.ingestion.providers.local_file import LocalFileProvider
from app.ingestion.providers.noaa_gfs import NOAAGFSProvider
from app.ingestion.parser import NWPFileParser
from app.ingestion.validator import NWPDataValidator
from app.engine.pipeline import AnomalyDetectionPipeline
from app.engine.config import EngineConfig
from app.core.logging import logger


class IngestionService:
    """
    Central orchestration service managing NWP data discovery, retrieval,
    local/remote parsing, data validation, and anomaly detector execution.
    """

    _instance: Optional["IngestionService"] = None

    def __init__(self, data_root: Optional[str] = None):
        if data_root is None:
            # Default backend/data directory
            data_root = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "data")
            )

        self.data_dir = os.path.join(data_root, "nwp")
        self.cache_dir = os.path.join(data_root, "cache")
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

        self.local_provider = LocalFileProvider(self.data_dir)
        self.gfs_provider = NOAAGFSProvider(self.cache_dir)

        # Ingestion state tracking
        self.status = "IDLE"
        self.active_data_source = "DEMO_SYNTHETIC_DATASET"
        self.active_data_mode = "DEMO_SYNTHETIC"
        self.last_ingested_dataset: Optional[str] = None
        self.last_ingestion_time: Optional[str] = None
        self.last_run_result: Optional[IngestionRunResponse] = None

    @classmethod
    def get_instance(cls) -> "IngestionService":
        if cls._instance is None:
            cls._instance = IngestionService()
        return cls._instance

    def list_available_datasets(self) -> List[DatasetSummary]:
        """Scans local storage and cache for available real NWP forecast files."""
        summaries: List[DatasetSummary] = []
        seen_ids = set()

        # Check local offline files
        if os.path.exists(self.data_dir):
            for fname in os.listdir(self.data_dir):
                if fname.endswith((".nc", ".nc4", ".grib2", ".grb2")):
                    fpath = os.path.join(self.data_dir, fname)
                    fsize = os.path.getsize(fpath)
                    dataset_id = os.path.splitext(fname)[0]
                    seen_ids.add(dataset_id)

                    summaries.append(
                        DatasetSummary(
                            dataset_id=dataset_id,
                            name=f"Offline NWP Grid ({fname})",
                            provider="Local Offline Storage (NCEP GFS / NetCDF4)",
                            file_format="NetCDF4" if fname.endswith((".nc", ".nc4")) else "GRIB2",
                            cycle_date="20260926",
                            cycle_hour="00",
                            lead_time_hours=24,
                            spatial_resolution_deg=0.25,
                            region_name="South Asia (Regional Domain)",
                            geographic_bounds=[8.0, 38.0, 65.0, 95.0],
                            variables=["t2m", "u10", "v10", "mslp", "tp"],
                            file_size_bytes=fsize,
                            is_cached=True,
                            is_real_data=True,
                            data_provenance="LOCAL_NWP_NETCDF",
                        )
                    )

        # Check remote cache files
        if os.path.exists(self.cache_dir):
            for fname in os.listdir(self.cache_dir):
                if fname.endswith((".nc", ".nc4", ".grib2", ".grb2")):
                    fpath = os.path.join(self.cache_dir, fname)
                    dataset_id = os.path.splitext(fname)[0]
                    if dataset_id not in seen_ids:
                        summaries.append(
                            DatasetSummary(
                                dataset_id=dataset_id,
                                name=f"Cached GFS Subset ({fname})",
                                provider="NOAA NCEP GFS 0.25° (NOMADS)",
                                file_format="GRIB2",
                                cycle_date="20260926",
                                cycle_hour="00",
                                lead_time_hours=24,
                                spatial_resolution_deg=0.25,
                                region_name="South Asia (Subset)",
                                geographic_bounds=[8.0, 38.0, 65.0, 95.0],
                                variables=["temperature", "wind", "mslp"],
                                file_size_bytes=os.path.getsize(fpath),
                                is_cached=True,
                                is_real_data=True,
                                data_provenance="REAL_NOAA_GFS",
                            )
                        )

        return summaries

    def get_dataset_by_id(self, dataset_id: str) -> Optional[DatasetSummary]:
        for ds in self.list_available_datasets():
            if ds.dataset_id.lower() == dataset_id.lower():
                return ds
        return None

    def validate_dataset(self, dataset_id: str) -> NWPValidationReport:
        """Validates a dataset's format, coordinates, variables, and physics bounds."""
        target_path = self._locate_dataset_file(dataset_id)
        if not target_path:
            raise FileNotFoundError(f"Dataset with ID '{dataset_id}' could not be found.")

        # Parse with NWPFileParser
        grid_dataset = NWPFileParser.parse_file(target_path, dataset_id=dataset_id)
        fmt = "NetCDF4" if target_path.endswith((".nc", ".nc4")) else "GRIB2"

        return NWPDataValidator.validate_grid(
            dataset_id=dataset_id,
            file_path=target_path,
            file_format=fmt,
            lats=grid_dataset.lats,
            lons=grid_dataset.lons,
            variables=grid_dataset.variables,
            units=grid_dataset.units,
            forecast_init_time=grid_dataset.forecast_init_time,
            valid_time=grid_dataset.valid_time,
            lead_time_hours=grid_dataset.lead_time_hours,
        )

    def run_ingestion(self, request: IngestionRunRequest) -> IngestionRunResponse:
        """
        Executes end-to-end ingestion workflow:
        1. Retrieval / local file selection
        2. Parsing
        3. Validation
        4. Normalization
        5. Anomaly detection & footprint extraction
        """
        start_time = time.perf_counter()
        self.status = "INGESTING"

        try:
            # 1. Retrieve or locate file
            file_path = None
            data_provenance = "LOCAL_NWP_NETCDF"

            if request.source_mode == "remote_nomads":
                today_str = request.cycle_date or datetime.now(timezone.utc).strftime("%Y%m%d")
                bounds = request.custom_bounds or [8.0, 38.0, 65.0, 95.0]
                file_path = self.gfs_provider.fetch_dataset(
                    cycle_date=today_str,
                    cycle_hour=request.cycle_hour,
                    lead_time_hours=request.lead_time_hours,
                    geographic_bounds=bounds,
                    variables=request.variables,
                )
                data_provenance = "REAL_NOAA_GFS"
            else:
                # Local offline mode
                if request.dataset_id:
                    file_path = self._locate_dataset_file(request.dataset_id)
                    if not file_path:
                        raise FileNotFoundError(f"Target dataset '{request.dataset_id}' not found in active storage.")
                else:
                    # Default to bundled sample
                    file_path = os.path.join(self.data_dir, "gfs_sample_0p25_south_asia.nc")

            if not file_path or not os.path.exists(file_path):
                raise FileNotFoundError(f"Unable to locate or retrieve target dataset: {file_path}")

            # 2. Parse into WeatherGridDataset
            grid_dataset = NWPFileParser.parse_file(
                file_path,
                lead_time_hours_override=request.lead_time_hours,
                dataset_id=request.dataset_id
            )

            # Set real data provenance
            grid_dataset.data_source = data_provenance
            grid_dataset.is_simulated = False

            # 3. Validate
            fmt = "NetCDF4" if file_path.endswith((".nc", ".nc4")) else "GRIB2"
            validation_report = NWPDataValidator.validate_grid(
                dataset_id=request.dataset_id or "real_dataset",
                file_path=file_path,
                file_format=fmt,
                lats=grid_dataset.lats,
                lons=grid_dataset.lons,
                variables=grid_dataset.variables,
                units=grid_dataset.units,
                forecast_init_time=grid_dataset.forecast_init_time,
                valid_time=grid_dataset.valid_time,
                lead_time_hours=grid_dataset.lead_time_hours,
            )

            if not validation_report.is_valid:
                raise ValueError(f"Dataset validation failed: {'; '.join(validation_report.errors)}")

            # 4. Anomaly Detection
            anomalies = []
            footprints_count = 0
            if request.run_anomaly_detection:
                engine_config = EngineConfig()
                if request.min_area_km2:
                    engine_config.footprint.min_area_km2 = request.min_area_km2

                pipeline = AnomalyDetectionPipeline(config=engine_config)
                detection_result = pipeline.run(dataset=grid_dataset)

                # Format anomalies as dictionary outputs
                for evt in detection_result.events:
                    evt_dict = evt.model_dump()
                    evt_dict["is_simulated"] = False
                    evt_dict["data_source"] = data_provenance
                    anomalies.append(evt_dict)

                footprints_count = detection_result.total_footprints_extracted

            # 5. Update Ingestion State
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            self.status = "READY"
            self.active_data_source = data_provenance
            self.active_data_mode = "REAL_NWP_DATA"
            self.last_ingested_dataset = request.dataset_id
            self.last_ingestion_time = datetime.now(timezone.utc).isoformat()

            response = IngestionRunResponse(
                success=True,
                message=f"Successfully ingested {validation_report.file_format} dataset and detected {len(anomalies)} anomalies.",
                dataset_id=request.dataset_id or "real_nwp_dataset",
                data_source=data_provenance,
                is_real_data=True,
                data_provenance=data_provenance,
                validation_report=validation_report,
                anomalies_detected_count=len(anomalies),
                footprints_extracted_count=footprints_count,
                anomalies=anomalies,
                execution_time_ms=elapsed_ms,
            )
            self.last_run_result = response
            return response

        except Exception as e:
            self.status = "ERROR"
            logger.error(f"Ingestion run failure: {str(e)}", exc_info=True)
            raise

    def get_status(self) -> IngestionStatusResponse:
        cached_count = len(self.list_available_datasets())
        return IngestionStatusResponse(
            status=self.status,
            active_data_source=self.active_data_source,
            active_data_mode=self.active_data_mode,
            last_ingested_dataset=self.last_ingested_dataset,
            last_ingestion_time=self.last_ingestion_time,
            cached_datasets_count=cached_count,
            available_providers=[
                "NOAA NCEP GFS 0.25° (NOMADS)",
                "Local Offline NetCDF4/GRIB2 Storage"
            ],
        )

    def _locate_dataset_file(self, dataset_id: str) -> Optional[str]:
        # Check in local data dir
        for base_dir in [self.data_dir, self.cache_dir]:
            if os.path.exists(base_dir):
                for fname in os.listdir(base_dir):
                    if dataset_id.lower() in fname.lower():
                        return os.path.join(base_dir, fname)
        return None
