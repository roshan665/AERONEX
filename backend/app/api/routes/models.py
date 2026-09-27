"""
FastAPI Routes for AI/ML Model Management & Registry
"""

from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Path, Body

from app.ml.schemas import (
    ModelListResponse,
    ModelMetadata,
    ModelSelectionRequest,
)
from app.ml.registry import model_registry
from app.core.config import settings

router = APIRouter(tags=["AI/ML Models"])


@router.get(
    "/models",
    response_model=ModelListResponse,
    summary="List Registered Anomaly Models",
    description="Returns metadata, operational status, versioning, and feature schemas for all registered models."
)
def list_models() -> ModelListResponse:
    return model_registry.list_models()


@router.get(
    "/models/status",
    summary="Active AI Model Operational Status",
    description="Returns active inference model, runtime data provenance, and subsystem health."
)
def get_model_status() -> Dict[str, Any]:
    active_model = model_registry.get_active_model()
    meta = active_model.metadata()
    return {
        "status": "online",
        "active_model_id": meta.model_id,
        "active_model_name": meta.model_name,
        "active_model_version": meta.version,
        "model_type": meta.model_type,
        "operational_status": meta.status,
        "feature_schema_version": meta.feature_schema_version,
        "training_dataset_id": meta.training_dataset_id,
        "data_mode": settings.DATA_PROVENANCE,
        "is_simulated": settings.IS_SIMULATED,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get(
    "/models/{model_id}",
    response_model=ModelMetadata,
    summary="Get Model Architecture & Metadata",
    description="Retrieves granular metadata, hyperparameters, and scientific limitations for a specific model."
)
def get_model_detail(
    model_id: str = Path(..., description="Unique model identifier, e.g. 'deterministic_baseline' or 'isolation_forest_v1'")
) -> ModelMetadata:
    model = model_registry.get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model ID '{model_id}' is not registered in the system."
        )
    return model.metadata()


@router.post(
    "/models/select",
    response_model=ModelMetadata,
    summary="Select Active Inference Model",
    description="Switches the active anomaly model between deterministic baseline and experimental ML."
)
def select_model(request: ModelSelectionRequest = Body(...)) -> ModelMetadata:
    try:
        updated_meta = model_registry.set_active_model(request.model_id)
        return updated_meta
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
