"""
System Provenance & Dataset Metadata Route
"""

from typing import Dict, Any
from fastapi import APIRouter
from app.data.demo_data import SYSTEM_METADATA

router = APIRouter(tags=["Metadata"])


@router.get(
    "/metadata",
    response_model=Dict[str, Any],
    summary="Dataset Provenance & System Specifications",
    description="Returns scientific model parameters, grid resolution, temporal horizon, and algorithmic provenance information.",
)
def get_metadata():
    return {
        **SYSTEM_METADATA,
        "grid_specifications": {
            "coordinate_reference_system": "EPSG:4326 (WGS84)",
            "spacing_degrees": SYSTEM_METADATA["grid_spacing_degrees"],
            "longitude_domain": "[-180.0, 180.0]",
            "latitude_domain": "[-90.0, 90.0]",
        },
        "methodology": {
            "climatology_reference": "Empirical Domain Baseline / Physical Thresholds (ERA5 1991-2020 Planned)",
            "spatial_clustering": "SciPy Morphological 8-Connectivity (scipy.ndimage)",
            "area_metric": "Cosine Latitude Spherical Integration",
        },
    }
