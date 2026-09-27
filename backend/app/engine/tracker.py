"""
Temporal Tracking Service for Associating Anomaly Footprints Across Consecutive Lead Times
"""

from typing import List, Dict, Any, Optional
import numpy as np
from shapely.geometry import Polygon

from app.engine.schemas import FootprintEntity
from app.engine.config import TemporalTrackingConfig


class TemporalEventTracker:
    """
    Associates spatial footprints across successive forecast timesteps (T0 -> T1 -> T2)
    using Intersection over Union (IoU) and centroid displacement.
    """

    @classmethod
    def track_footprints(
        cls,
        current_footprints: List[FootprintEntity],
        previous_footprints: List[FootprintEntity],
        config: TemporalTrackingConfig,
    ) -> List[Dict[str, Any]]:
        """
        Calculates IoU and centroid displacement to link footprints across timesteps.
        Returns a list of linked trajectory associations.
        """
        if not current_footprints or not previous_footprints:
            return []

        associations = []

        for curr in current_footprints:
            curr_poly = Polygon(curr.polygon_coordinates[0])
            best_match = None
            best_iou = 0.0
            min_dist_km = float("inf")

            for prev in previous_footprints:
                if curr.category != prev.category:
                    continue

                prev_poly = Polygon(prev.polygon_coordinates[0])
                
                # 1. Compute IoU
                intersection_area = curr_poly.intersection(prev_poly).area
                union_area = curr_poly.union(prev_poly).area
                iou = (intersection_area / union_area) if union_area > 0 else 0.0

                # 2. Compute approximate Great-Circle centroid displacement (km)
                dist_km = cls._haversine_distance_km(
                    curr.centroid_lat, curr.centroid_lon,
                    prev.centroid_lat, prev.centroid_lon
                )

                # Matching condition: either significant spatial overlap OR proximity within displacement threshold
                if iou >= config.iou_threshold or (dist_km <= config.max_centroid_displacement_km and iou > 0.02):
                    if iou > best_iou or (best_iou == 0.0 and dist_km < min_dist_km):
                        best_match = prev
                        best_iou = iou
                        min_dist_km = dist_km

            if best_match:
                area_change_pct = round(((curr.estimated_area_km2 - best_match.estimated_area_km2) / best_match.estimated_area_km2) * 100, 1)
                magnitude_change = round(curr.max_anomaly_score - best_match.max_anomaly_score, 2)

                associations.append({
                    "current_event_id": curr.event_id,
                    "previous_event_id": best_match.event_id,
                    "category": curr.category,
                    "iou_overlap": round(best_iou, 3),
                    "displacement_km": round(min_dist_km, 1),
                    "area_change_pct": area_change_pct,
                    "magnitude_change": magnitude_change,
                    "trajectory_vector": {
                        "from": [best_match.centroid_lat, best_match.centroid_lon],
                        "to": [curr.centroid_lat, curr.centroid_lon],
                    },
                    "status": "ASSOCIATED_TIMESTEP",
                    "note": "Geometric association based on spatial overlap and centroid proximity.",
                })

        return associations

    @staticmethod
    def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371.0
        phi1 = np.radians(lat1)
        phi2 = np.radians(lat2)
        delta_phi = np.radians(lat2 - lat1)
        delta_lambda = np.radians(lon2 - lon1)

        a = np.sin(delta_phi / 2.0)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0)**2
        c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
        return float(r * c)
