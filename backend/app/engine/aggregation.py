"""
Event Aggregation & Multi-Variable Physical Cross-Correlation Service
"""

from typing import List, Dict, Any, Optional
import numpy as np
from shapely.geometry import Polygon

from app.engine.schemas import FootprintEntity, NormalizedWeatherGrid
from app.models.anomaly import AnomalyEvent


class EventAggregator:
    """
    Consolidates individual variable footprint entities into holistic meteorological anomaly events.
    Applies multi-variable rules (e.g., Low Pressure + Gale Wind = Cyclone).
    """

    @classmethod
    def aggregate_events(
        cls,
        footprints: List[FootprintEntity],
        grid: NormalizedWeatherGrid,
    ) -> List[AnomalyEvent]:
        if not footprints:
            return []

        events: List[AnomalyEvent] = []
        processed_footprint_ids = set()

        # 1. Multi-variable pairing: Cyclone Detection
        # Check if any pressure anomaly footprint overlaps with a wind anomaly footprint
        pressure_footprints = [f for f in footprints if f.category == "pressure_anomaly"]
        wind_footprints = [f for f in footprints if f.category == "wind_anomaly"]

        cyclone_counter = 1
        for pf in pressure_footprints:
            p_poly = Polygon(pf.polygon_coordinates[0])
            matching_wf = None

            for wf in wind_footprints:
                wf_key = f"{wf.category}_{wf.cluster_id}"
                if wf_key in processed_footprint_ids:
                    continue
                w_poly = Polygon(wf.polygon_coordinates[0])
                if p_poly.intersects(w_poly):
                    matching_wf = wf
                    break

            if matching_wf and pf.severity in ["High", "Medium"]:
                # Coincident pressure deficit and high wind speed -> Cyclone Event
                processed_footprint_ids.add(f"{pf.category}_{pf.cluster_id}")
                processed_footprint_ids.add(f"{matching_wf.category}_{matching_wf.cluster_id}")

                # Deterministic stable ID based on spatial coordinates
                lat_int = abs(int(round(pf.centroid_lat * 10)))
                lon_int = abs(int(round(pf.centroid_lon * 10)))
                event_id = f"CYC-{grid.valid_time[:10].replace('-', '')}-{lat_int}_{lon_int}"
                cyclone_counter += 1

                max_wind_kmh = matching_wf.supporting_metrics.get("max_wind_kmh", 120.0)
                min_p = pf.supporting_metrics.get("min_mslp_hpa", 965.0)

                events.append(
                    AnomalyEvent(
                        id=event_id,
                        name="Tropical Cyclone Vortex",
                        type="Cyclone",
                        category_key="cyclone",
                        region=cls._approximate_region(pf.centroid_lat, pf.centroid_lon),
                        lat=pf.centroid_lat,
                        lon=pf.centroid_lon,
                        coordinates_display=pf.coordinates_display,
                        forecast_window=f"Day {grid.lead_day} – Day {min(10, grid.lead_day + 3)}",
                        forecast_days=[grid.lead_day, grid.lead_day + 1, grid.lead_day + 2],
                        severity="High" if min_p < 980.0 or max_wind_kmh > 118.0 else "Medium",
                        severity_level=3 if min_p < 980.0 else 2,
                        estimated_area=f"~ {int(pf.estimated_area_km2):,} km²",
                        estimated_area_km2=pf.estimated_area_km2,
                        max_wind=f"{int(max_wind_kmh * 0.85)} - {int(max_wind_kmh)} km/h",
                        central_pressure=f"{int(min_p)} - {int(min_p + 15)} hPa",
                        anomaly_score=f"+{max(pf.max_anomaly_score, matching_wf.max_anomaly_score):.1f}σ (Vortex Coupling)",
                        color="#ef4444",
                        description=(
                            f"Multi-variable cyclonic vortex detected with central pressure deficit of "
                            f"{pf.supporting_metrics.get('pressure_deficit_hpa', 35)} hPa coupled with sustained gale winds "
                            f"exceeding {int(max_wind_kmh)} km/h."
                        ),
                        updated_ago="Just now",
                        detection_timestamp=grid.valid_time,
                        is_simulated=True,
                        # Extended Phase 4 scientific attributes
                        primary_variable="mslp+wind_speed",
                        detection_method="Multi-Variable Physical Vortex Coupling (Low Pressure + Gale Wind)",
                        forecast_init_time=grid.forecast_init_time,
                        valid_time=grid.valid_time,
                        forecast_lead_day=grid.lead_day,
                        geographic_bounds=pf.bounds,
                        grid_cell_count=pf.cell_count + matching_wf.cell_count,
                        max_anomaly_magnitude=max(pf.max_anomaly_score, matching_wf.max_anomaly_score),
                        mean_anomaly_magnitude=round((pf.mean_anomaly_score + matching_wf.mean_anomaly_score) / 2.0, 2),
                        relevant_units="hPa & m/s",
                        supporting_measurements={
                            "min_mslp_hpa": min_p,
                            "max_wind_kmh": max_wind_kmh,
                            "pressure_deficit_hpa": pf.supporting_metrics.get("pressure_deficit_hpa", 35.0),
                        },
                        geometry={"type": "Polygon", "coordinates": pf.polygon_coordinates},
                        data_source=grid.data_source,
                        data_quality_warnings=grid.preprocessing_warnings,
                    )
                )

        # 2. Add remaining single-variable footprints
        for f in footprints:
            f_key = f"{f.category}_{f.cluster_id}"
            if f_key in processed_footprint_ids:
                continue

            cat_prefix = f.category[:4].upper()
            lat_int = abs(int(round(f.centroid_lat * 10)))
            lon_int = abs(int(round(f.centroid_lon * 10)))
            event_id = f"{cat_prefix}-{grid.valid_time[:10].replace('-', '')}-{lat_int}_{lon_int}"

            # Format measurements
            max_wind_str = "N/A"
            p_str = "N/A"
            if f.category == "wind_anomaly":
                kmh = f.supporting_metrics.get("max_wind_kmh", 80.0)
                max_wind_str = f"{int(kmh * 0.85)} - {int(kmh)} km/h"
            elif f.category == "pressure_anomaly":
                p = f.supporting_metrics.get("min_mslp_hpa", 995.0)
                p_str = f"{int(p)} - {int(p + 10)} hPa"
            elif f.category == "heat_wave":
                t = f.supporting_metrics.get("max_temp_detected", 42.0)
                p_str = f"{t:.1f}°C (Peak)"
            elif f.category == "cold_wave":
                t = f.supporting_metrics.get("min_temp_detected", -15.0)
                p_str = f"{t:.1f}°C (Min)"
            elif f.category == "precipitation_anomaly":
                tp = f.supporting_metrics.get("max_precip_mm", 75.0)
                p_str = f"{tp:.1f} mm (Peak)"

            events.append(
                AnomalyEvent(
                    id=event_id,
                    name=f.name,
                    type=f.hazard_type,
                    category_key=f.category,
                    region=cls._approximate_region(f.centroid_lat, f.centroid_lon),
                    lat=f.centroid_lat,
                    lon=f.centroid_lon,
                    coordinates_display=f.coordinates_display,
                    forecast_window=f"Day {grid.lead_day} – Day {min(10, grid.lead_day + 3)}",
                    forecast_days=[grid.lead_day],
                    severity=f.severity,
                    severity_level=f.severity_level,
                    estimated_area=f"~ {int(f.estimated_area_km2):,} km²",
                    estimated_area_km2=f.estimated_area_km2,
                    max_wind=max_wind_str,
                    central_pressure=p_str,
                    anomaly_score=f"{'+' if f.max_anomaly_score >= 0 else ''}{f.max_anomaly_score:.1f}σ ({f.hazard_type})",
                    color=cls._get_category_color(f.category, f.severity),
                    description=f"{f.name} detected via {f.detection_method}. Maximum anomaly score: {f.max_anomaly_score:.1f}σ.",
                    updated_ago="Just now",
                    detection_timestamp=grid.valid_time,
                    is_simulated=True,
                    # Extended Phase 4 scientific attributes
                    primary_variable=f.primary_variable,
                    detection_method=f.detection_method,
                    forecast_init_time=grid.forecast_init_time,
                    valid_time=grid.valid_time,
                    forecast_lead_day=grid.lead_day,
                    geographic_bounds=f.bounds,
                    grid_cell_count=f.cell_count,
                    max_anomaly_magnitude=f.max_anomaly_score,
                    mean_anomaly_magnitude=f.mean_anomaly_score,
                    relevant_units=f.canonical_unit,
                    supporting_measurements=f.supporting_metrics,
                    geometry={"type": "Polygon", "coordinates": f.polygon_coordinates},
                    data_source=grid.data_source,
                    data_quality_warnings=grid.preprocessing_warnings,
                )
            )

        return events

    @staticmethod
    def _approximate_region(lat: float, lon: float) -> str:
        """Determines approximate geographic basin from coordinates"""
        if -30.0 <= lat <= 5.0 and 50.0 <= lon <= 95.0:
            return "Western Indian Ocean"
        elif 35.0 <= lat <= 60.0 and 50.0 <= lon <= 85.0:
            return "Central Asia"
        elif 50.0 <= lat <= 80.0 and 85.0 <= lon <= 140.0:
            return "Siberia"
        elif 15.0 <= lat <= 50.0 and (lon >= 130.0 or lon <= -130.0):
            return "North Pacific"
        elif -55.0 <= lat <= -20.0 and -50.0 <= lon <= 10.0:
            return "South Atlantic"
        elif -30.0 <= lat <= 10.0 and -80.0 <= lon <= -35.0:
            return "South America"
        elif 5.0 <= lat <= 25.0 and 80.0 <= lon <= 95.0:
            return "Bay of Bengal"
        elif 5.0 <= lat <= 25.0 and 55.0 <= lon <= 77.0:
            return "Arabian Sea"
        return "Global Ocean / Continental Sector"

    @staticmethod
    def _get_category_color(category: str, severity: str) -> str:
        if severity == "High":
            return "#ef4444"
        colors = {
            "heat_wave": "#f97316",
            "cold_wave": "#38bdf8",
            "wind_anomaly": "#2dd4bf",
            "pressure_anomaly": "#a855f7",
            "precipitation_anomaly": "#3b82f6",
        }
        return colors.get(category, "#f59e0b")
