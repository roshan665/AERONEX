"""
FastAPI Routes for Event Tracking, Trajectory History, and Forecast Uncertainty
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Path

from app.tracking.models import (
    EventTrackSummary,
    EventTrackDetail,
    TrackPoint,
    UncertaintySummaryResponse,
    EventUncertaintyDetail
)
from app.tracking.service import TrackingService
from app.tracking.uncertainty import UncertaintyService
from app.core.logging import logger

router = APIRouter(tags=["Tracking & Uncertainty"])
tracking_service = TrackingService()


@router.get(
    "/events/tracks",
    response_model=List[EventTrackSummary],
    summary="List all tracked anomaly series",
    description="Returns high-level summaries for all active and historical multi-horizon anomaly tracks."
)
def list_event_tracks(
    category: Optional[str] = Query(None, description="Filter by category (e.g. 'cyclone', 'heat_wave')"),
    min_detections: Optional[int] = Query(None, ge=1, description="Minimum number of detected frames"),
    status: Optional[str] = Query(None, description="Filter by status ('ACTIVE', 'DISSIPATED', 'INTERMITTENT')"),
) -> List[EventTrackSummary]:
    return tracking_service.list_tracks(
        category=category,
        min_detections=min_detections,
        status=status
    )


@router.get(
    "/events/tracks/{track_id}",
    response_model=EventTrackDetail,
    summary="Get detailed track profile",
    description="Retrieves comprehensive trajectory coordinates, metric history, and scientific caveats for a track."
)
def get_track_detail(
    track_id: str = Path(..., description="Unique track identifier (e.g. 'TRK-CYC-001')")
) -> EventTrackDetail:
    track = tracking_service.get_track(track_id)
    if not track:
        raise HTTPException(
            status_code=404,
            detail=f"Track ID '{track_id}' not found in active tracking repository."
        )
    return track


@router.get(
    "/events/tracks/{track_id}/history",
    response_model=List[TrackPoint],
    summary="Get chronological detection frames for a track",
    description="Returns the sequential list of TrackPoints across all forecast lead steps for a given track."
)
def get_track_history(
    track_id: str = Path(..., description="Unique track identifier")
) -> List[TrackPoint]:
    history = tracking_service.get_track_history(track_id)
    if history is None:
        raise HTTPException(
            status_code=404,
            detail=f"Track ID '{track_id}' not found."
        )
    return history


@router.get(
    "/uncertainty",
    response_model=UncertaintySummaryResponse,
    summary="Get system uncertainty status and capabilities",
    description="Reports whether ensemble spread is available or deterministic confidence decay applies."
)
def get_uncertainty_summary(
    dataset_id: Optional[str] = Query(None, description="Active dataset identifier"),
    mode: Optional[str] = Query(None, description="Force mode ('ensemble' or 'deterministic')"),
) -> UncertaintySummaryResponse:
    return UncertaintyService.get_summary(dataset_id=dataset_id, force_mode=mode)


@router.get(
    "/uncertainty/{event_id}",
    response_model=EventUncertaintyDetail,
    summary="Get event-specific uncertainty metrics",
    description="Returns daily ensemble spread metrics if available, or deterministic confidence decay guide."
)
def get_event_uncertainty(
    event_id: str = Path(..., description="Event or track identifier (e.g. 'evt-001' or 'TRK-CYC-001')")
) -> EventUncertaintyDetail:
    return UncertaintyService.get_event_uncertainty(event_id)
