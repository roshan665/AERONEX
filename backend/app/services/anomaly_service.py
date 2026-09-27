"""
Anomaly Service for Managing Extreme Weather Detection Records
"""

from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from app.data.demo_data import ANOMALIES_CATALOG, SYSTEM_METADATA
from app.models.anomaly import (
    AnomalyEvent, 
    AnomalyListResponse, 
    AnomalyDetailResponse,
    TrajectoryStep
)


class AnomalyService:
    _dynamic_cache: Dict[str, dict] = {}

    @classmethod
    def register_dynamic_events(cls, events: List[AnomalyEvent]) -> None:
        """Stores dynamically detected anomaly events for detail and score queries."""
        for evt in events:
            evt_dict = evt.model_dump() if hasattr(evt, "model_dump") else dict(evt)
            # Ensure footprint_polygon exists in [lat, lon] Leaflet format
            if "geometry" in evt_dict and evt_dict["geometry"] and "coordinates" in evt_dict["geometry"]:
                coords = evt_dict["geometry"]["coordinates"]
                if coords and len(coords) > 0:
                    # GeoJSON is [lon, lat], detail polygon format expects [lat, lon]
                    evt_dict["footprint_polygon"] = [[pt[1], pt[0]] for pt in coords[0]]
            if "footprint_polygon" not in evt_dict or not evt_dict["footprint_polygon"]:
                lat, lon = evt_dict.get("lat", 20.0), evt_dict.get("lon", 80.0)
                evt_dict["footprint_polygon"] = [
                    [lat - 1.0, lon - 1.0],
                    [lat + 1.0, lon - 1.0],
                    [lat + 1.0, lon + 1.0],
                    [lat - 1.0, lon + 1.0],
                    [lat - 1.0, lon - 1.0],
                ]
            if "forecast_track" not in evt_dict:
                evt_dict["forecast_track"] = [
                    [evt_dict.get("lat", 20.0), evt_dict.get("lon", 80.0)]
                ]
            cls._dynamic_cache[evt_dict["id"].lower()] = evt_dict

    @classmethod
    def get_dynamic_event(cls, anomaly_id: str) -> Optional[dict]:
        return cls._dynamic_cache.get(anomaly_id.lower())

    @classmethod
    def get_anomalies(
        cls,
        category_key: Optional[str] = None,
        severity: Optional[str] = None,
        region: Optional[str] = None,
        forecast_day: Optional[int] = None,
        min_area_km2: Optional[float] = None,
    ) -> AnomalyListResponse:
        filtered = ANOMALIES_CATALOG

        if category_key and category_key.upper() != "ALL":
            filtered = [a for a in filtered if a["category_key"].lower() == category_key.lower()]

        if severity and severity.upper() != "ALL":
            filtered = [a for a in filtered if a["severity"].lower() == severity.lower()]

        if region and region.upper() != "ALL":
            filtered = [a for a in filtered if region.lower() in a["region"].lower()]

        if forecast_day is not None:
            filtered = [a for a in filtered if forecast_day in a.get("forecast_days", [])]

        if min_area_km2 is not None:
            filtered = [a for a in filtered if a.get("estimated_area_km2", 0.0) >= min_area_km2]

        events = [
            AnomalyEvent(
                id=a["id"],
                name=a["name"],
                type=a["type"],
                category_key=a["category_key"],
                region=a["region"],
                lat=a["lat"],
                lon=a["lon"],
                coordinates_display=a["coordinates_display"],
                forecast_window=a["forecast_window"],
                forecast_days=a["forecast_days"],
                severity=a["severity"],
                severity_level=a["severity_level"],
                estimated_area=a["estimated_area"],
                estimated_area_km2=a["estimated_area_km2"],
                max_wind=a["max_wind"],
                central_pressure=a["central_pressure"],
                anomaly_score=a["anomaly_score"],
                color=a["color"],
                description=a["description"],
                updated_ago=a["updated_ago"],
                detection_timestamp=a["detection_timestamp"],
                is_simulated=True,
            )
            for a in filtered
        ]

        return AnomalyListResponse(
            total=len(ANOMALIES_CATALOG),
            count=len(events),
            events=events,
            data_provenance=SYSTEM_METADATA["data_provenance"],
            is_simulated=True,
            disclaimer=SYSTEM_METADATA["disclaimer"],
        )

    @classmethod
    def get_anomaly_by_id(cls, anomaly_id: str) -> AnomalyDetailResponse:
        item = next((a for a in ANOMALIES_CATALOG if a["id"].lower() == anomaly_id.lower()), None)
        if not item:
            item = cls._dynamic_cache.get(anomaly_id.lower())
        if not item:
            raise HTTPException(
                status_code=404,
                detail=f"Anomaly event with ID '{anomaly_id}' not found in active catalog."
            )

        event = AnomalyEvent(
            id=item["id"],
            name=item["name"],
            type=item["type"],
            category_key=item["category_key"],
            region=item["region"],
            lat=item["lat"],
            lon=item["lon"],
            coordinates_display=item["coordinates_display"],
            forecast_window=item["forecast_window"],
            forecast_days=item["forecast_days"],
            severity=item["severity"],
            severity_level=item["severity_level"],
            estimated_area=item["estimated_area"],
            estimated_area_km2=item["estimated_area_km2"],
            max_wind=item["max_wind"],
            central_pressure=item["central_pressure"],
            anomaly_score=item["anomaly_score"],
            color=item["color"],
            description=item["description"],
            updated_ago=item["updated_ago"],
            detection_timestamp=item["detection_timestamp"],
            is_simulated=True,
        )

        trajectory_steps = [
            TrajectoryStep(
                day=s["day"],
                lat=s["lat"],
                lon=s["lon"],
                intensity_note=s["intensity_note"]
            )
            for s in item.get("trajectory_steps", [])
        ]

        return AnomalyDetailResponse(
            event=event,
            footprint_polygon=item["footprint_polygon"],
            forecast_track=item["forecast_track"],
            trajectory_steps=trajectory_steps,
            meteorological_metrics=item.get("meteorological_metrics", {}),
            data_provenance=SYSTEM_METADATA["data_provenance"],
            is_simulated=True,
            disclaimer=SYSTEM_METADATA["disclaimer"],
        )
