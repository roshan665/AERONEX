"""
API Router Aggregator for AeroNex Backend
"""

from fastapi import APIRouter
from app.api.routes import (
    health,
    overview,
    forecasts,
    anomalies,
    map as map_routes,
    regions,
    metadata,
    detection,
    ingestion,
    tracking,
    models,
    scoring,
    evaluation,
)

api_router = APIRouter(prefix="/api")
root_router = APIRouter()

routers = [
    health.router,
    overview.router,
    forecasts.router,
    anomalies.router,
    map_routes.router,
    regions.router,
    metadata.router,
    detection.router,
    ingestion.router,
    models.router,
    scoring.router,
    evaluation.router,
    tracking.router,
]

for r in routers:
    api_router.include_router(r)
    root_router.include_router(r)


