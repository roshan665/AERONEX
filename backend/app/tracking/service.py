"""
Tracking Service for Associating Anomaly Footprints and Building Trajectory Histories
"""

from typing import List, Dict, Any, Optional
from app.tracking.models import (
    TrackPoint,
    EventTrackSummary,
    EventTrackDetail
)
from app.tracking.scenarios import (
    build_cyclone_track,
    build_heatwave_track,
    build_coldwave_track,
    build_storm_track
)
from app.tracking.geo_math import (
    haversine_distance_km,
    calculate_bearing,
    calculate_speed_kmh,
    calculate_area_change
)
from app.core.logging import logger


class TrackingService:
    """
    Manages temporal association, movement calculation, and track histories
    for extreme weather anomalies across multi-horizon forecasts.
    """

    def __init__(self):
        # Pre-seed with curated reproducible tracks
        self._tracks: Dict[str, EventTrackDetail] = {
            "TRK-CYC-001": build_cyclone_track(),
            "TRK-HEAT-002": build_heatwave_track(),
            "TRK-COLD-003": build_coldwave_track(),
            "TRK-STM-004": build_storm_track(),
        }


    def list_tracks(
        self,
        category: Optional[str] = None,
        min_detections: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[EventTrackSummary]:
        """Returns filtered summaries of all active and historical tracks."""
        summaries: List[EventTrackSummary] = []
        for track in self._tracks.values():
            if category and track.category.lower() != category.lower():
                continue
            if min_detections and track.total_detections < min_detections:
                continue
            if status and track.status.upper() != status.upper():
                continue

            summaries.append(
                EventTrackSummary(
                    track_id=track.track_id,
                    name=track.name,
                    category=track.category,
                    hazard_type=track.hazard_type,
                    first_detection_lead_hours=track.first_detection_lead_hours,
                    latest_detection_lead_hours=track.latest_detection_lead_hours,
                    total_detections=track.total_detections,
                    total_frames=track.total_frames,
                    initial_centroid=track.initial_centroid,
                    latest_centroid=track.latest_centroid,
                    cumulative_distance_km=track.cumulative_distance_km,
                    net_displacement_km=track.net_displacement_km,
                    mean_speed_kmh=track.mean_speed_kmh,
                    peak_magnitude=track.peak_magnitude,
                    magnitude_unit=track.magnitude_unit,
                    peak_severity=track.peak_severity,
                    max_area_km2=track.max_area_km2,
                    status=track.status,
                    trajectory_line=track.trajectory_line,
                    color=track.color,
                    data_provenance=track.data_provenance,
                    is_simulated=track.is_simulated
                )
            )
        return summaries

    def get_track(self, track_id: str) -> Optional[EventTrackDetail]:
        """Retrieves full detail for a specific track ID."""
        return self._tracks.get(track_id)

    def get_track_history(self, track_id: str) -> Optional[List[TrackPoint]]:
        """Retrieves the chronological list of TrackPoints for a track."""
        track = self.get_track(track_id)
        if not track:
            return None
        return track.points

    @classmethod
    def associate_sequential_events(
        cls,
        frames: List[Dict[str, Any]],
        max_displacement_km: float = 850.0,
        min_iou_overlap: float = 0.05
    ) -> List[EventTrackDetail]:
        """
        Dynamically stitches discrete event detections across consecutive forecast frames
        into contiguous EventTrackDetail series.

        Enforces:
        1. Exact category matching (cyclones do not merge with heat waves).
        2. Proximity threshold scaled by elapsed hours.
        3. Missing-frame representation (no synthetic interpolation of missing coords).
        4. Derived movement explicitly labeled as footprint centroid shift.
        """
        if not frames:
            return []

        # Sort frames chronologically by step_hours
        sorted_frames = sorted(frames, key=lambda f: f.get("step_hours", 0))
        all_steps = sorted(list(set(f.get("step_hours", 0) for f in sorted_frames)))
        total_steps = len(all_steps)

        # Group detections by step_hours
        detections_by_step: Dict[int, List[Dict[str, Any]]] = {}
        for s in all_steps:
            detections_by_step[s] = []

        for f in sorted_frames:
            step = f.get("step_hours", 0)
            detections_by_step[step].append(f)

        tracks: List[EventTrackDetail] = []
        track_counter = 1

        # We greedily build tracks from the earliest detections
        processed_event_ids = set()

        for start_idx, start_step in enumerate(all_steps):
            for det in detections_by_step[start_step]:
                det_id = det.get("id") or det.get("event_id")
                if det_id in processed_event_ids:
                    continue

                # Initiate new track candidate
                category = det.get("category_key") or det.get("category", "unknown")
                hazard_type = det.get("type") or det.get("hazard_type", category.title())
                name = det.get("name", f"Tracked {hazard_type}")
                color = det.get("color", "#FF4568")

                track_id = f"TRK-{category[:3].upper()}-{track_counter:03d}"
                track_counter += 1
                processed_event_ids.add(det_id)

                # Initialize sequence of points for all steps
                points: List[TrackPoint] = []
                trajectory_coords: List[List[float]] = []
                prev_detected: Optional[TrackPoint] = None
                cumulative_dist = 0.0
                total_detected_count = 0
                first_lead = start_step
                last_lead = start_step
                peak_mag = det.get("max_anomaly_score") or det.get("peak_metric_value") or 0.0
                peak_sev = det.get("severity", "Low")
                max_area = det.get("estimated_area_km2", 0.0)
                init_centroid = [det.get("lat", 0.0), det.get("lon", 0.0)]
                latest_centroid = init_centroid

                active_candidate = det

                for frame_idx, current_step in enumerate(all_steps):
                    valid_time = f"T+{current_step}h"
                    forecast_day = max(1, current_step // 24)

                    if current_step < start_step:
                        # Step occurred before track genesis
                        points.append(TrackPoint(
                            frame_index=frame_idx,
                            step_hours=current_step,
                            forecast_day=forecast_day,
                            valid_time=valid_time,
                            detection_status="MISSING"
                        ))
                        continue

                    # Search for best match in current_step
                    best_match = None
                    best_dist = float("inf")

                    if current_step == start_step:
                        best_match = active_candidate
                    else:
                        for cand in detections_by_step[current_step]:
                            cand_id = cand.get("id") or cand.get("event_id")
                            if cand_id in processed_event_ids:
                                continue
                            cand_cat = cand.get("category_key") or cand.get("category")
                            if cand_cat != category:
                                continue

                            # Compute distance
                            c_lat = cand.get("lat") or cand.get("centroid_lat")
                            c_lon = cand.get("lon") or cand.get("centroid_lon")
                            p_lat = prev_detected.centroid_lat if prev_detected else None
                            p_lon = prev_detected.centroid_lon if prev_detected else None

                            if c_lat is not None and c_lon is not None and p_lat is not None and p_lon is not None:
                                d = haversine_distance_km(p_lat, p_lon, c_lat, c_lon)
                                elapsed_hours = current_step - prev_detected.step_hours
                                scaled_max_dist = max_displacement_km * (elapsed_hours / 24.0)

                                if d <= scaled_max_dist and d < best_dist:
                                    best_dist = d
                                    best_match = cand

                    if best_match:
                        b_id = best_match.get("id") or best_match.get("event_id")
                        processed_event_ids.add(b_id)
                        total_detected_count += 1
                        last_lead = current_step

                        b_lat = best_match.get("lat") or best_match.get("centroid_lat")
                        b_lon = best_match.get("lon") or best_match.get("centroid_lon")
                        b_area = best_match.get("estimated_area_km2", 0.0)
                        b_mag = best_match.get("max_anomaly_score") or best_match.get("peak_metric_value")
                        b_sev = best_match.get("severity", "Medium")
                        b_poly = best_match.get("footprintPolygon") or best_match.get("polygon_coordinates")

                        if b_area > max_area:
                            max_area = b_area
                        if b_mag is not None and (peak_mag is None or b_mag > peak_mag):
                            peak_mag = b_mag

                        disp_km = None
                        bearing_deg = None
                        bearing_card = None
                        speed = None
                        area_diff = None
                        area_pct = None
                        mag_diff = None

                        if prev_detected and prev_detected.centroid_lat is not None and prev_detected.centroid_lon is not None:
                            disp_km = round(haversine_distance_km(prev_detected.centroid_lat, prev_detected.centroid_lon, b_lat, b_lon), 1)
                            bearing_deg, bearing_card = calculate_bearing(prev_detected.centroid_lat, prev_detected.centroid_lon, b_lat, b_lon)
                            speed = calculate_speed_kmh(disp_km, current_step - prev_detected.step_hours)
                            area_diff, area_pct = calculate_area_change(prev_detected.estimated_area_km2, b_area)
                            if prev_detected.max_magnitude is not None and b_mag is not None:
                                mag_diff = round(b_mag - prev_detected.max_magnitude, 1)
                            cumulative_dist += disp_km

                        trajectory_coords.append([b_lat, b_lon])
                        latest_centroid = [b_lat, b_lon]
                        coord_disp = f"{abs(b_lat):.1f}°{'S' if b_lat < 0 else 'N'}, {abs(b_lon):.1f}°{'W' if b_lon < 0 else 'E'}"

                        pt = TrackPoint(
                            frame_index=frame_idx,
                            step_hours=current_step,
                            forecast_day=forecast_day,
                            valid_time=valid_time,
                            detection_status="DETECTED",
                            event_id=b_id,
                            centroid_lat=b_lat,
                            centroid_lon=b_lon,
                            coordinates_display=coord_disp,
                            estimated_area_km2=b_area,
                            max_magnitude=b_mag,
                            magnitude_unit=best_match.get("canonical_unit", "metric"),
                            severity=b_sev,
                            polygon_coordinates=b_poly,
                            displacement_km=disp_km,
                            bearing_deg=bearing_deg,
                            bearing_cardinal=bearing_card,
                            speed_kmh=speed,
                            area_change_km2=area_diff,
                            area_change_pct=area_pct,
                            magnitude_change=mag_diff
                        )
                        prev_detected = pt
                        points.append(pt)
                    else:
                        # Event not detected at this frame
                        points.append(TrackPoint(
                            frame_index=frame_idx,
                            step_hours=current_step,
                            forecast_day=forecast_day,
                            valid_time=valid_time,
                            detection_status="MISSING"
                        ))

                net_disp = round(haversine_distance_km(init_centroid[0], init_centroid[1], latest_centroid[0], latest_centroid[1]), 1)
                duration_hours = max(1, last_lead - first_lead)
                mean_spd = round(cumulative_dist / duration_hours, 1) if duration_hours > 0 else 0.0

                tracks.append(
                    EventTrackDetail(
                        track_id=track_id,
                        name=name,
                        category=category,
                        hazard_type=hazard_type,
                        first_detection_lead_hours=first_lead,
                        latest_detection_lead_hours=last_lead,
                        total_detections=total_detected_count,
                        total_frames=total_steps,
                        initial_centroid=init_centroid,
                        latest_centroid=latest_centroid,
                        cumulative_distance_km=round(cumulative_dist, 1),
                        net_displacement_km=net_disp,
                        mean_speed_kmh=mean_spd,
                        peak_magnitude=peak_mag,
                        magnitude_unit="metric",
                        peak_severity=peak_sev,
                        max_area_km2=round(max_area, 1),
                        status="ACTIVE" if last_lead == all_steps[-1] else "DISSIPATED",
                        trajectory_line=trajectory_coords,
                        color=color,
                        data_provenance="DYNAMIC_STITCHED_SERIES",
                        is_simulated=True,
                        points=points
                    )
                )

        return tracks
