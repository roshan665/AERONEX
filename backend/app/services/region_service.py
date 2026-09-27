"""
Region Service for Listing Geographic Sectors
"""

from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from app.data.demo_data import REGIONS_CATALOG, SYSTEM_METADATA


class RegionService:
    @staticmethod
    def get_regions() -> List[Dict[str, Any]]:
        return [
            {
                **r,
                "data_provenance": SYSTEM_METADATA["data_provenance"],
                "is_simulated": True,
            }
            for r in REGIONS_CATALOG
        ]

    @staticmethod
    def get_region_by_id(region_id: str) -> Dict[str, Any]:
        region = next((r for r in REGIONS_CATALOG if r["region_id"].lower() == region_id.lower()), None)
        if not region:
            raise HTTPException(
                status_code=404,
                detail=f"Geographic region '{region_id}' not found in demonstration sector registry."
            )
        return {
            **region,
            "data_provenance": SYSTEM_METADATA["data_provenance"],
            "is_simulated": True,
        }
