"""
NWP Data Ingestion & Dataset Catalog API Endpoints
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Body, Path
from pydantic import BaseModel, Field

from app.ingestion.models import (
    DatasetSummary,
    NWPValidationReport,
    IngestionRunRequest,
    IngestionRunResponse,
    IngestionStatusResponse,
)
from app.ingestion.service import IngestionService
from app.core.logging import logger

router = APIRouter(tags=["NWP Data Ingestion"])


class ValidateRequest(BaseModel):
    dataset_id: str = Field(..., description="Target dataset identifier to validate")


@router.get(
    "/datasets",
    response_model=List[DatasetSummary],
    summary="List Available Real NWP Datasets",
    description="Returns metadata summaries for all locally available and cached real NWP forecast files.",
)
def list_datasets():
    service = IngestionService.get_instance()
    return service.list_available_datasets()


@router.get(
    "/datasets/{dataset_id}",
    response_model=DatasetSummary,
    summary="Get NWP Dataset Details",
    description="Retrieves detailed catalog metadata for a specific NWP forecast dataset.",
)
def get_dataset(
    dataset_id: str = Path(..., description="Unique dataset identifier")
):
    service = IngestionService.get_instance()
    dataset = service.get_dataset_by_id(dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset with ID '{dataset_id}' not found in active storage or cache."
        )
    return dataset


@router.post(
    "/ingestion/validate",
    response_model=NWPValidationReport,
    summary="Validate NWP Dataset Quality & Physical Bounds",
    description=(
        "Executes comprehensive data quality validation: coordinate regularity, "
        "spatial grid shapes, physical realism bounds, missing-data fractions, and temporal continuity."
    ),
)
def validate_dataset(request: ValidateRequest = Body(...)):
    service = IngestionService.get_instance()
    try:
        return service.validate_dataset(request.dataset_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error during dataset validation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=422, detail=f"Validation failed: {str(e)}")


@router.post(
    "/ingestion/run",
    response_model=IngestionRunResponse,
    summary="Trigger NWP Data Ingestion & Anomaly Detection",
    description=(
        "Initiates the complete real NWP ingestion lifecycle: loads NetCDF4/GRIB2 files, "
        "validates arrays, normalizes coordinates and units, and executes anomaly detection pipelines."
    ),
)
def run_ingestion(request: IngestionRunRequest = Body(...)):
    service = IngestionService.get_instance()
    try:
        return service.run_ingestion(request)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error during ingestion execution: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion execution failed: {str(e)}")


@router.get(
    "/ingestion/status",
    response_model=IngestionStatusResponse,
    summary="Get Current Ingestion Engine Status",
    description="Returns the operational status, active data mode, and last ingestion run metadata.",
)
def get_ingestion_status():
    service = IngestionService.get_instance()
    return service.get_status()
