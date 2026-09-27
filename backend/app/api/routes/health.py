import os
from fastapi import APIRouter
from app.core.config import settings
from app.data.demo_data import SYSTEM_METADATA
from app.ingestion.service import IngestionService

router = APIRouter(tags=["System Health"])


@router.get(
    "/health",
    summary="Service Health & Liveness Probe",
    description="Returns runtime service health status, active data provenance, and dataset initialization timestamp.",
)
def get_health():
    ingestion_service = IngestionService.get_instance()
    available_datasets = ingestion_service.list_available_datasets()
    local_nwp_count = len(available_datasets)

    return {
        "status": "healthy",
        "version": settings.VERSION,
        "service": settings.PROJECT_NAME,
        "app": settings.PROJECT_NAME,
        "data_mode": settings.DATA_PROVENANCE,
        "is_simulated": settings.IS_SIMULATED,
        "dataset_timestamp": SYSTEM_METADATA["latest_data_timestamp"],
        "subsystems": {
            "api_gateway": "ONLINE",
            "anomaly_engine": "ONLINE",
            "forecast_engine": "ONLINE",
            "geospatial_engine": "ONLINE",
        },
        "data_providers": {
            "synthetic_demo_generator": {
                "status": "ONLINE",
                "mode": "DEMO_SYNTHETIC",
                "available": True,
                "description": "Deterministic multi-hazard synthetic generator with injected anomaly ground-truth masks",
            },
            "local_nwp_storage": {
                "status": "ONLINE" if local_nwp_count > 0 else "EMPTY",
                "mode": "LOCAL_OFFLINE_ARCHIVE",
                "available": local_nwp_count > 0,
                "cached_datasets_count": local_nwp_count,
                "description": "Local NetCDF4 / GRIB2 offline archive for verified South Asia domains",
            },
            "noaa_nomads_gfs": {
                "status": "STANDBY_UNVERIFIED",
                "mode": "REMOTE_FETCH",
                "available": False,
                "description": "NOAA NOMADS GRIB Filter remote provider (requires external internet access)",
                "operational_advisory": "Real NWP mode requires explicit offline cache selection or verified network connection.",
            },
        },
    }

