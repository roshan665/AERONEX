"""
Geospatial Footprint Extraction & Connected-Component Labeling Service
"""

from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from scipy import ndimage
from shapely.geometry import box, MultiPolygon, Polygon
from shapely.ops import unary_union

from app.engine.schemas import DetectionResult, FootprintEntity
from app.engine.config import FootprintConfig, DetectorThresholds


class FootprintExtractor:
    EARTH_RADIUS_KM = 6371.0

    @classmethod
    def extract_footprints(
        cls,
        detection: DetectionResult,
        lats: np.ndarray,
        lons: np.ndarray,
        config: FootprintConfig,
        thresholds: DetectorThresholds,
    ) -> List[FootprintEntity]:
        """
        Groups anomalous boolean cells into contiguous clusters, computes spherical area,
        derives bounding boxes and centroids, and builds GeoJSON-compatible polygons.
        """
        mask = detection.mask
        if not np.any(mask):
            return []

        # 1. Structure element for morphological connectivity
        if config.connectivity == 4:
            structure = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=int)
        else:
            structure = np.ones((3, 3), dtype=int)  # 8-neighbor connectivity

        labeled_array, num_features = ndimage.label(mask, structure=structure)
        if num_features == 0:
            return []

        # 2. Grid spacing in radians for cosine-weighted area calculation
        dlat_deg = float(np.abs(np.mean(np.diff(lats))))
        dlon_deg = float(np.abs(np.mean(np.diff(lons))))
        dlat_rad = np.radians(dlat_deg)
        dlon_rad = np.radians(dlon_deg)

        footprints: List[FootprintEntity] = []

        for cluster_id in range(1, num_features + 1):
            cell_indices = np.argwhere(labeled_array == cluster_id)
            cell_count = len(cell_indices)

            # Filter small noise by minimum cell count
            if cell_count < config.min_cells:
                continue

            lat_idxs = cell_indices[:, 0]
            lon_idxs = cell_indices[:, 1]

            cluster_lats = lats[lat_idxs]
            cluster_lons = lons[lon_idxs]

            # 3. Cosine-latitude area integration
            # Area_cell = R^2 * cos(lat_rad) * dlat_rad * dlon_rad
            lat_rads = np.radians(cluster_lats)
            cell_areas = (cls.EARTH_RADIUS_KM ** 2) * np.cos(lat_rads) * dlat_rad * dlon_rad
            total_area_km2 = float(np.sum(cell_areas))

            # Filter small noise by physical area
            if total_area_km2 < config.min_area_km2:
                continue

            # 4. Centroid & Geographic Bounds
            centroid_lat = float(np.mean(cluster_lats))
            centroid_lon = float(np.mean(cluster_lons))
            min_lat = float(np.min(cluster_lats) - dlat_deg / 2.0)
            max_lat = float(np.max(cluster_lats) + dlat_deg / 2.0)
            min_lon = float(np.min(cluster_lons) - dlon_deg / 2.0)
            max_lon = float(np.max(cluster_lons) + dlon_deg / 2.0)
            bounds = [min_lon, min_lat, max_lon, max_lat]

            # 5. Anomaly Scores & Peak Values
            scores = detection.score_grid[lat_idxs, lon_idxs]
            max_score = float(np.nanmax(scores)) if len(scores) > 0 else 0.0
            mean_score = float(np.nanmean(scores)) if len(scores) > 0 else 0.0

            # 6. Severity Classification
            severity, severity_level = cls._classify_severity(
                detection.category, 
                max_score, 
                thresholds,
                detection.metadata
            )

            # 7. GeoJSON Polygon Construction via Shapely
            polygon_coords = cls._build_polygon(
                cluster_lats, 
                cluster_lons, 
                dlat_deg, 
                dlon_deg, 
                config.simplify_tolerance_deg
            )

            # Coordinates display string
            lat_str = f"{abs(centroid_lat):.1f}°{'N' if centroid_lat >= 0 else 'S'}"
            lon_str = f"{abs(centroid_lon):.1f}°{'E' if centroid_lon >= 0 else 'W'}"
            coords_display = f"{lat_str}, {lon_str}"

            # Display name and hazard taxonomy
            display_name, hazard_type = cls._format_naming(detection.category, severity)

            peak_metric = float(detection.metadata.get(
                "max_temp_detected",
                detection.metadata.get(
                    "min_temp_detected",
                    detection.metadata.get(
                        "max_wind_ms",
                        detection.metadata.get("min_mslp_hpa", max_score)
                    )
                )
            ))

            event_id = f"ANOM-{detection.category[:4].upper()}-{cluster_id:03d}"

            footprints.append(
                FootprintEntity(
                    cluster_id=cluster_id,
                    event_id=event_id,
                    name=display_name,
                    category=detection.category,
                    hazard_type=hazard_type,
                    severity=severity,
                    severity_level=severity_level,
                    primary_variable=detection.variable,
                    canonical_unit=detection.canonical_unit,
                    centroid_lat=round(centroid_lat, 2),
                    centroid_lon=round(centroid_lon, 2),
                    coordinates_display=coords_display,
                    bounds=[round(b, 2) for b in bounds],
                    estimated_area_km2=round(total_area_km2, 1),
                    cell_count=cell_count,
                    max_anomaly_score=round(max_score, 2),
                    mean_anomaly_score=round(mean_score, 2),
                    peak_metric_value=round(peak_metric, 2),
                    polygon_coordinates=polygon_coords,
                    supporting_metrics=detection.metadata,
                    detection_method=detection.method,
                    is_simulated=True,
                )
            )

        return footprints

    @classmethod
    def _build_polygon(
        cls, 
        lats: np.ndarray, 
        lons: np.ndarray, 
        dlat: float, 
        dlon: float, 
        tolerance: float
    ) -> List[List[List[float]]]:
        """
        Creates a union of grid-cell bounding boxes, simplifies perimeter, and returns GeoJSON coordinates.
        """
        cell_boxes = []
        half_lat = dlat / 2.0
        half_lon = dlon / 2.0

        for lat, lon in zip(lats, lons):
            cell_boxes.append(box(lon - half_lon, lat - half_lat, lon + half_lon, lat + half_lat))

        if not cell_boxes:
            return []

        merged_poly = unary_union(cell_boxes)
        if tolerance > 0.0:
            merged_poly = merged_poly.simplify(tolerance, preserve_topology=True)

        # Extract exterior ring coordinates [Lon, Lat]
        if isinstance(merged_poly, Polygon):
            coords = [[round(x, 3), round(y, 3)] for x, y in merged_poly.exterior.coords]
            return [coords]
        elif isinstance(merged_poly, MultiPolygon):
            # Take largest polygon from multi-part
            largest = max(merged_poly.geoms, key=lambda p: p.area)
            coords = [[round(x, 3), round(y, 3)] for x, y in largest.exterior.coords]
            return [coords]
        else:
            # Fallback envelope
            minx, miny, maxx, maxy = merged_poly.bounds
            fallback_coords = [
                [minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy], [minx, miny]
            ]
            return [fallback_coords]

    @staticmethod
    def _classify_severity(
        category: str, 
        max_score: float, 
        thresholds: DetectorThresholds,
        meta: Dict[str, Any]
    ) -> Tuple[str, int]:
        """
        Variable-specific severity classification: Low (1), Medium (2), High (3).
        """
        if category == "heat_wave":
            peak_temp = meta.get("max_temp_detected", 40.0)
            if peak_temp >= thresholds.severe_heat_celsius or max_score >= 3.5:
                return "High", 3
            elif peak_temp >= thresholds.extreme_heat_celsius or max_score >= 2.5:
                return "Medium", 2
            return "Low", 1

        elif category == "cold_wave":
            min_temp = meta.get("min_temp_detected", 0.0)
            if min_temp <= thresholds.severe_cold_celsius or max_score >= 3.5:
                return "High", 3
            elif min_temp <= thresholds.extreme_cold_celsius or max_score >= 2.5:
                return "Medium", 2
            return "Low", 1

        elif category == "wind_anomaly":
            max_wind = meta.get("max_wind_ms", 17.5)
            if max_wind >= thresholds.hurricane_wind_ms or max_score >= 3.5:
                return "High", 3
            elif max_wind >= thresholds.storm_wind_ms or max_score >= 2.5:
                return "Medium", 2
            return "Low", 1

        elif category == "pressure_anomaly":
            min_p = meta.get("min_mslp_hpa", 995.0)
            if min_p <= thresholds.cyclonic_core_hpa or max_score >= 3.5:
                return "High", 3
            elif min_p <= thresholds.deep_depression_hpa or max_score >= 2.5:
                return "Medium", 2
            return "Low", 1

        elif category == "precipitation_anomaly":
            max_tp = meta.get("max_precip_mm", 65.0)
            if max_tp >= thresholds.extreme_rain_mm:
                return "High", 3
            elif max_tp >= thresholds.very_heavy_rain_mm:
                return "Medium", 2
            return "Low", 1

        # Fallback by score
        if max_score >= 3.0:
            return "High", 3
        elif max_score >= 2.0:
            return "Medium", 2
        return "Low", 1

    @staticmethod
    def _format_naming(category: str, severity: str) -> Tuple[str, str]:
        names = {
            "heat_wave": ("Severe Heat Dome" if severity == "High" else "Thermal Anomaly", "Heat Wave"),
            "cold_wave": ("Arctic Cold Wave Plunge" if severity == "High" else "Cold Wave Outbreak", "Cold Wave"),
            "wind_anomaly": ("Severe Gale Squall" if severity == "High" else "Unusual Wind Pattern", "Wind Anomaly"),
            "pressure_anomaly": ("Deep Cyclonic Depression" if severity == "High" else "Barometric Low Anomaly", "Pressure Anomaly"),
            "precipitation_anomaly": ("Extreme Precipitation Event", "Precipitation Anomaly"),
        }
        return names.get(category, ("Extreme Weather Anomaly", "General Anomaly"))
