"""
Reproducible Synthetic Scenarios for Event Tracking and Forecast Uncertainty Evaluation
"""

from typing import List, Dict, Any
from app.tracking.models import (
    TrackPoint,
    EventTrackSummary,
    EventTrackDetail,
    DailyEnsembleSpread,
    EventUncertaintyDetail,
    UncertaintyLeadTimeBand
)
from app.tracking.geo_math import (
    haversine_distance_km,
    calculate_bearing,
    calculate_speed_kmh,
    calculate_area_change
)

# Reference Base Timestamps
INIT_TIME = "2026-09-26T00:00:00Z"

# 1. Standard Lead Time Confidence Decay Guidelines (Deterministic Atmospheric Skill)
STANDARD_LEAD_TIME_DECAY = [
    UncertaintyLeadTimeBand(day=1, step_hours=24, confidence_pct=94.5, confidence_level="HIGH", description="High synoptic skill; tight deterministic bounds."),
    UncertaintyLeadTimeBand(day=2, step_hours=48, confidence_pct=89.0, confidence_level="HIGH", description="Strong model consensus across atmospheric layers."),
    UncertaintyLeadTimeBand(day=3, step_hours=72, confidence_pct=81.5, confidence_level="HIGH", description="Good deterministic guidance; emergence of minor track variance."),
    UncertaintyLeadTimeBand(day=4, step_hours=96, confidence_pct=72.0, confidence_level="MODERATE", description="Moderate confidence; convective parameterization divergence starts."),
    UncertaintyLeadTimeBand(day=5, step_hours=120, confidence_pct=62.5, confidence_level="MODERATE", description="Moderate confidence; increasing track spread."),
    UncertaintyLeadTimeBand(day=6, step_hours=144, confidence_pct=52.0, confidence_level="MODERATE", description="Baroclinic phase shifts increase timing uncertainty."),
    UncertaintyLeadTimeBand(day=7, step_hours=168, confidence_pct=42.5, confidence_level="LOW_TREND_ONLY", description="Low confidence; indicative of synoptic trends only."),
    UncertaintyLeadTimeBand(day=8, step_hours=192, confidence_pct=34.0, confidence_level="LOW_TREND_ONLY", description="High ensemble spread; low deterministic skill."),
    UncertaintyLeadTimeBand(day=9, step_hours=216, confidence_pct=28.0, confidence_level="LOW_TREND_ONLY", description="Large uncertainty envelope; advisory caution."),
    UncertaintyLeadTimeBand(day=10, step_hours=240, confidence_pct=22.0, confidence_level="LOW_TREND_ONLY", description="Chaotic limit; qualitative medium-range outlook only.")
]


def build_cyclone_track() -> EventTrackDetail:
    """
    Scenario 1: Tropical Cyclone Vortex (Western Indian Ocean)
    Characteristics:
    - Shifts location across successive forecast frames (northwestward progression).
    - Footprint area grows from Day 1 to Day 3, then contracts.
    - Anomaly magnitude (winds) intensifies up to Day 3, then decays.
    - Dissipates after Day 5 (Days 6-10 marked MISSING/DISSIPATED).
    """
    raw_frames = [
        # (day, hours, valid_time, status, lat, lon, area, wind, mslp, severity, polygon)
        (1, 24, "2026-09-27T00:00:00Z", "DETECTED", -12.4, 78.6, 320000.0, 126.0, "km/h", "High", [[75.0, -9.5], [82.5, -10.2], [83.0, -15.0], [76.5, -16.5], [74.0, -12.0], [75.0, -9.5]]),
        (2, 48, "2026-09-28T00:00:00Z", "DETECTED", -13.8, 77.1, 365000.0, 138.0, "km/h", "High", [[74.0, -11.0], [81.0, -11.5], [81.5, -16.5], [75.0, -18.0], [72.5, -13.5], [74.0, -11.0]]),
        (3, 72, "2026-09-29T00:00:00Z", "DETECTED", -15.2, 75.4, 420000.0, 150.0, "km/h", "High", [[72.0, -12.5], [79.5, -13.0], [80.0, -18.0], [73.5, -19.5], [70.5, -15.0], [72.0, -12.5]]),
        (4, 96, "2026-09-30T00:00:00Z", "DETECTED", -16.8, 73.5, 380000.0, 132.0, "km/h", "High", [[70.5, -14.0], [77.5, -14.5], [78.0, -19.5], [71.5, -21.0], [69.0, -16.5], [70.5, -14.0]]),
        (5, 120, "2026-10-01T00:00:00Z", "DETECTED", -18.5, 71.0, 245000.0, 95.0, "km/h", "Medium", [[68.5, -16.0], [74.5, -16.5], [75.0, -21.0], [69.5, -22.5], [67.0, -18.5], [68.5, -16.0]]),
        (6, 144, "2026-10-02T00:00:00Z", "DISSIPATED", None, None, None, None, "km/h", None, None),
        (7, 168, "2026-10-03T00:00:00Z", "MISSING", None, None, None, None, "km/h", None, None),
        (8, 192, "2026-10-04T00:00:00Z", "MISSING", None, None, None, None, "km/h", None, None),
        (9, 216, "2026-10-05T00:00:00Z", "MISSING", None, None, None, None, "km/h", None, None),
        (10, 240, "2026-10-06T00:00:00Z", "MISSING", None, None, None, None, "km/h", None, None),
    ]

    points: List[TrackPoint] = []
    trajectory_line: List[List[float]] = []
    prev_point: Optional[TrackPoint] = None
    cumulative_distance_km = 0.0

    for idx, (day, hours, valid_time, status, lat, lon, area, mag, unit, sev, poly) in enumerate(raw_frames):
        disp_km = None
        bearing_deg = None
        bearing_card = None
        speed = None
        area_diff = None
        area_pct = None
        mag_diff = None

        if status == "DETECTED" and lat is not None and lon is not None:
            trajectory_line.append([lat, lon])
            coord_str = f"{abs(lat):.1f}°{'S' if lat < 0 else 'N'}, {abs(lon):.1f}°{'W' if lon < 0 else 'E'}"

            if prev_point and prev_point.centroid_lat is not None and prev_point.centroid_lon is not None:
                disp_km = round(haversine_distance_km(prev_point.centroid_lat, prev_point.centroid_lon, lat, lon), 1)
                bearing_deg, bearing_card = calculate_bearing(prev_point.centroid_lat, prev_point.centroid_lon, lat, lon)
                speed = calculate_speed_kmh(disp_km, hours - prev_point.step_hours)
                area_diff, area_pct = calculate_area_change(prev_point.estimated_area_km2, area)
                if prev_point.max_magnitude is not None and mag is not None:
                    mag_diff = round(mag - prev_point.max_magnitude, 1)
                cumulative_distance_km += disp_km

            pt = TrackPoint(
                frame_index=idx,
                step_hours=hours,
                forecast_day=day,
                valid_time=valid_time,
                detection_status="DETECTED",
                event_id=f"EVT-CYC-F{hours:03d}",
                centroid_lat=lat,
                centroid_lon=lon,
                coordinates_display=coord_str,
                estimated_area_km2=area,
                max_magnitude=mag,
                magnitude_unit=unit,
                severity=sev,
                polygon_coordinates=poly,
                displacement_km=disp_km,
                bearing_deg=bearing_deg,
                bearing_cardinal=bearing_card,
                speed_kmh=speed,
                area_change_km2=area_diff,
                area_change_pct=area_pct,
                magnitude_change=mag_diff
            )
            prev_point = pt
        else:
            pt = TrackPoint(
                frame_index=idx,
                step_hours=hours,
                forecast_day=day,
                valid_time=valid_time,
                detection_status=status
            )

        points.append(pt)

    net_disp = round(haversine_distance_km(-12.4, 78.6, -18.5, 71.0), 1)

    return EventTrackDetail(
        track_id="TRK-CYC-001",
        name="Tropical Cyclone Vortex",
        category="cyclone",
        hazard_type="Tropical Cyclone",
        first_detection_lead_hours=24,
        latest_detection_lead_hours=120,
        total_detections=5,
        total_frames=10,
        initial_centroid=[-12.4, 78.6],
        latest_centroid=[-18.5, 71.0],
        cumulative_distance_km=round(cumulative_distance_km, 1),
        net_displacement_km=net_disp,
        mean_speed_kmh=round(cumulative_distance_km / 96.0, 1),
        peak_magnitude=150.0,
        magnitude_unit="km/h",
        peak_severity="High",
        max_area_km2=420000.0,
        status="ACTIVE",
        trajectory_line=trajectory_line,
        color="#FF4568",
        data_provenance="DEMO_SYNTHETIC_DATASET",
        is_simulated=True,
        points=points,
        movement_notes=(
            "Derived movement represents displacement of detected forecast footprint centroids across "
            "successive forecast frames; it does not constitute a verified operational storm track."
        ),
        uncertainty_summary={
            "mode": "DETERMINISTIC_ONLY",
            "message": "Ensemble spread unavailable for deterministic run. Predictability decays with lead time.",
            "lead_time_decay_day5": "62.5% confidence"
        }
    )


def build_heatwave_track() -> EventTrackDetail:
    """
    Scenario 2: Heat Dome (Central Asia)
    Characteristics:
    - Quasi-stationary footprint that expands from Day 1 to Day 3, then contracts on Day 4.
    - Collapses/dissipates by Day 5.
    """
    raw_frames = [
        (1, 24, "2026-09-27T00:00:00Z", "DETECTED", 45.2, 67.1, 420000.0, 41.2, "°C", "High", [[60.0, 42.0], [62.0, 49.0], [75.0, 50.5], [76.5, 44.0], [66.0, 40.5], [60.0, 42.0]]),
        (2, 48, "2026-09-28T00:00:00Z", "DETECTED", 45.8, 68.5, 540000.0, 43.5, "°C", "High", [[60.5, 42.5], [62.8, 49.5], [76.0, 51.0], [77.5, 44.5], [67.0, 41.0], [60.5, 42.5]]),
        (3, 72, "2026-09-29T00:00:00Z", "DETECTED", 46.4, 70.2, 610000.0, 44.8, "°C", "High", [[61.5, 43.0], [63.5, 50.2], [77.5, 51.8], [78.8, 45.2], [68.0, 41.5], [61.5, 43.0]]),
        (4, 96, "2026-09-30T00:00:00Z", "DETECTED", 46.8, 72.0, 480000.0, 42.1, "°C", "High", [[63.0, 43.5], [65.0, 50.5], [78.5, 52.0], [79.5, 45.8], [69.5, 42.0], [63.0, 43.5]]),
        (5, 120, "2026-10-01T00:00:00Z", "DISSIPATED", None, None, None, None, "°C", None, None),
        (6, 144, "2026-10-02T00:00:00Z", "MISSING", None, None, None, None, "°C", None, None),
        (7, 168, "2026-10-03T00:00:00Z", "MISSING", None, None, None, None, "°C", None, None),
        (8, 192, "2026-10-04T00:00:00Z", "MISSING", None, None, None, None, "°C", None, None),
        (9, 216, "2026-10-05T00:00:00Z", "MISSING", None, None, None, None, "°C", None, None),
        (10, 240, "2026-10-06T00:00:00Z", "MISSING", None, None, None, None, "°C", None, None),
    ]

    points: List[TrackPoint] = []
    trajectory_line: List[List[float]] = []
    prev_point: Optional[TrackPoint] = None
    cumulative_distance_km = 0.0

    for idx, (day, hours, valid_time, status, lat, lon, area, mag, unit, sev, poly) in enumerate(raw_frames):
        disp_km = None
        bearing_deg = None
        bearing_card = None
        speed = None
        area_diff = None
        area_pct = None
        mag_diff = None

        if status == "DETECTED" and lat is not None and lon is not None:
            trajectory_line.append([lat, lon])
            coord_str = f"{abs(lat):.1f}°{'S' if lat < 0 else 'N'}, {abs(lon):.1f}°{'W' if lon < 0 else 'E'}"

            if prev_point and prev_point.centroid_lat is not None and prev_point.centroid_lon is not None:
                disp_km = round(haversine_distance_km(prev_point.centroid_lat, prev_point.centroid_lon, lat, lon), 1)
                bearing_deg, bearing_card = calculate_bearing(prev_point.centroid_lat, prev_point.centroid_lon, lat, lon)
                speed = calculate_speed_kmh(disp_km, hours - prev_point.step_hours)
                area_diff, area_pct = calculate_area_change(prev_point.estimated_area_km2, area)
                if prev_point.max_magnitude is not None and mag is not None:
                    mag_diff = round(mag - prev_point.max_magnitude, 1)
                cumulative_distance_km += disp_km

            pt = TrackPoint(
                frame_index=idx,
                step_hours=hours,
                forecast_day=day,
                valid_time=valid_time,
                detection_status="DETECTED",
                event_id=f"EVT-HEAT-F{hours:03d}",
                centroid_lat=lat,
                centroid_lon=lon,
                coordinates_display=coord_str,
                estimated_area_km2=area,
                max_magnitude=mag,
                magnitude_unit=unit,
                severity=sev,
                polygon_coordinates=poly,
                displacement_km=disp_km,
                bearing_deg=bearing_deg,
                bearing_cardinal=bearing_card,
                speed_kmh=speed,
                area_change_km2=area_diff,
                area_change_pct=area_pct,
                magnitude_change=mag_diff
            )
            prev_point = pt
        else:
            pt = TrackPoint(
                frame_index=idx,
                step_hours=hours,
                forecast_day=day,
                valid_time=valid_time,
                detection_status=status
            )
        points.append(pt)

    net_disp = round(haversine_distance_km(45.2, 67.1, 46.8, 72.0), 1)

    return EventTrackDetail(
        track_id="TRK-HEAT-002",
        name="Extreme Heat Dome",
        category="heat_wave",
        hazard_type="Heat Wave",
        first_detection_lead_hours=24,
        latest_detection_lead_hours=96,
        total_detections=4,
        total_frames=10,
        initial_centroid=[45.2, 67.1],
        latest_centroid=[46.8, 72.0],
        cumulative_distance_km=round(cumulative_distance_km, 1),
        net_displacement_km=net_disp,
        mean_speed_kmh=round(cumulative_distance_km / 72.0, 1),
        peak_magnitude=44.8,
        magnitude_unit="°C",
        peak_severity="High",
        max_area_km2=610000.0,
        status="ACTIVE",
        trajectory_line=trajectory_line,
        color="#F97316",
        data_provenance="DEMO_SYNTHETIC_DATASET",
        is_simulated=True,
        points=points,
        movement_notes="Slow-moving anticyclonic ridge displacement over continental landmass."
    )


def build_coldwave_track() -> EventTrackDetail:
    """
    Scenario 3: Arctic Cold Wave (Siberia)
    Characteristics:
    - Demonstrates intermittent / missing detection handling:
      Day 1 & 2: Detected
      Day 3: MISSING (temporarily falls below threshold)
      Day 4: DETECTED (re-emerging surge)
      Day 5+: Dissipated
    """
    raw_frames = [
        (1, 24, "2026-09-27T00:00:00Z", "DETECTED", 62.3, 105.2, 410000.0, -32.5, "°C", "Medium", [[98.0, 58.0], [100.0, 66.0], [114.0, 67.5], [115.0, 60.0], [104.0, 57.0], [98.0, 58.0]]),
        (2, 48, "2026-09-28T00:00:00Z", "DETECTED", 60.5, 106.8, 440000.0, -34.8, "°C", "Medium", [[99.0, 56.5], [101.5, 64.5], [115.5, 66.0], [116.5, 58.5], [105.0, 55.5], [99.0, 56.5]]),
        (3, 72, "2026-09-29T00:00:00Z", "MISSING", None, None, None, None, "°C", None, None),
        (4, 96, "2026-09-30T00:00:00Z", "DETECTED", 56.0, 110.0, 310000.0, -29.0, "°C", "Medium", [[102.0, 52.0], [105.0, 60.0], [118.0, 61.5], [119.0, 54.0], [108.0, 51.0], [102.0, 52.0]]),
        (5, 120, "2026-10-01T00:00:00Z", "DISSIPATED", None, None, None, None, "°C", None, None),
        (6, 144, "2026-10-02T00:00:00Z", "MISSING", None, None, None, None, "°C", None, None),
        (7, 168, "2026-10-03T00:00:00Z", "MISSING", None, None, None, None, "°C", None, None),
        (8, 192, "2026-10-04T00:00:00Z", "MISSING", None, None, None, None, "°C", None, None),
        (9, 216, "2026-10-05T00:00:00Z", "MISSING", None, None, None, None, "°C", None, None),
        (10, 240, "2026-10-06T00:00:00Z", "MISSING", None, None, None, None, "°C", None, None),
    ]

    points: List[TrackPoint] = []
    trajectory_line: List[List[float]] = []
    prev_point: Optional[TrackPoint] = None
    cumulative_distance_km = 0.0

    for idx, (day, hours, valid_time, status, lat, lon, area, mag, unit, sev, poly) in enumerate(raw_frames):
        disp_km = None
        bearing_deg = None
        bearing_card = None
        speed = None
        area_diff = None
        area_pct = None
        mag_diff = None

        if status == "DETECTED" and lat is not None and lon is not None:
            trajectory_line.append([lat, lon])
            coord_str = f"{abs(lat):.1f}°{'S' if lat < 0 else 'N'}, {abs(lon):.1f}°{'W' if lon < 0 else 'E'}"

            if prev_point and prev_point.centroid_lat is not None and prev_point.centroid_lon is not None:
                disp_km = round(haversine_distance_km(prev_point.centroid_lat, prev_point.centroid_lon, lat, lon), 1)
                bearing_deg, bearing_card = calculate_bearing(prev_point.centroid_lat, prev_point.centroid_lon, lat, lon)
                # Compute speed across actual elapsed time difference (could be 48h if missing frame in between)
                delta_t = hours - prev_point.step_hours
                speed = calculate_speed_kmh(disp_km, delta_t)
                area_diff, area_pct = calculate_area_change(prev_point.estimated_area_km2, area)
                if prev_point.max_magnitude is not None and mag is not None:
                    mag_diff = round(mag - prev_point.max_magnitude, 1)
                cumulative_distance_km += disp_km

            pt = TrackPoint(
                frame_index=idx,
                step_hours=hours,
                forecast_day=day,
                valid_time=valid_time,
                detection_status="DETECTED",
                event_id=f"EVT-COLD-F{hours:03d}",
                centroid_lat=lat,
                centroid_lon=lon,
                coordinates_display=coord_str,
                estimated_area_km2=area,
                max_magnitude=mag,
                magnitude_unit=unit,
                severity=sev,
                polygon_coordinates=poly,
                displacement_km=disp_km,
                bearing_deg=bearing_deg,
                bearing_cardinal=bearing_card,
                speed_kmh=speed,
                area_change_km2=area_diff,
                area_change_pct=area_pct,
                magnitude_change=mag_diff
            )
            prev_point = pt
        else:
            pt = TrackPoint(
                frame_index=idx,
                step_hours=hours,
                forecast_day=day,
                valid_time=valid_time,
                detection_status=status
            )
        points.append(pt)

    net_disp = round(haversine_distance_km(62.3, 105.2, 56.0, 110.0), 1)

    return EventTrackDetail(
        track_id="TRK-COLD-003",
        name="Siberian Cold Wave",
        category="cold_wave",
        hazard_type="Cold Wave",
        first_detection_lead_hours=24,
        latest_detection_lead_hours=96,
        total_detections=3,
        total_frames=10,
        initial_centroid=[62.3, 105.2],
        latest_centroid=[56.0, 110.0],
        cumulative_distance_km=round(cumulative_distance_km, 1),
        net_displacement_km=net_disp,
        mean_speed_kmh=round(cumulative_distance_km / 72.0, 1),
        peak_magnitude=-34.8,
        magnitude_unit="°C",
        peak_severity="Medium",
        max_area_km2=440000.0,
        status="INTERMITTENT",
        trajectory_line=trajectory_line,
        color="#38BDF8",
        data_provenance="DEMO_SYNTHETIC_DATASET",
        is_simulated=True,
        points=points,
        movement_notes="Southward plunge of polar vortex core across Central Siberia with intermittent Day 3 detection."
    )


def build_storm_track() -> EventTrackDetail:
    """
    Scenario 4: Bay of Bengal Severe Storm System
    Active track demonstrating continuous northward propagation.
    """
    raw_frames = [
        (1, 24, "2026-09-27T00:00:00Z", "DETECTED", 14.5, 88.2, 180000.0, 85.0, "km/h", "Medium", [[86.0, 13.0], [90.0, 13.5], [90.5, 16.0], [86.5, 15.5], [86.0, 13.0]]),
        (2, 48, "2026-09-28T00:00:00Z", "DETECTED", 16.2, 88.8, 220000.0, 95.0, "km/h", "High", [[86.5, 14.8], [91.0, 15.2], [91.2, 17.8], [87.0, 17.2], [86.5, 14.8]]),
        (3, 72, "2026-09-29T00:00:00Z", "DETECTED", 18.0, 89.4, 250000.0, 105.0, "km/h", "High", [[87.0, 16.5], [91.8, 17.0], [92.0, 19.5], [87.5, 19.0], [87.0, 16.5]]),
        (4, 96, "2026-09-30T00:00:00Z", "DETECTED", 19.8, 89.9, 210000.0, 90.0, "km/h", "Medium", [[88.0, 18.2], [92.2, 18.8], [92.5, 21.0], [88.2, 20.8], [88.0, 18.2]]),
        (5, 120, "2026-10-01T00:00:00Z", "DISSIPATED", None, None, None, None, "km/h", None, None),
        (6, 144, "2026-10-02T00:00:00Z", "MISSING", None, None, None, None, "km/h", None, None),
        (7, 168, "2026-10-03T00:00:00Z", "MISSING", None, None, None, None, "km/h", None, None),
        (8, 192, "2026-10-04T00:00:00Z", "MISSING", None, None, None, None, "km/h", None, None),
        (9, 216, "2026-10-05T00:00:00Z", "MISSING", None, None, None, None, "km/h", None, None),
        (10, 240, "2026-10-06T00:00:00Z", "MISSING", None, None, None, None, "km/h", None, None),
    ]

    points: List[TrackPoint] = []
    trajectory_line: List[List[float]] = []
    prev_point: Optional[TrackPoint] = None
    cumulative_distance_km = 0.0

    for idx, (day, hours, valid_time, status, lat, lon, area, mag, unit, sev, poly) in enumerate(raw_frames):
        disp_km = None
        bearing_deg = None
        bearing_card = None
        speed = None
        area_diff = None
        area_pct = None
        mag_diff = None

        if status == "DETECTED" and lat is not None and lon is not None:
            trajectory_line.append([lat, lon])
            coord_str = f"{abs(lat):.1f}°{'S' if lat < 0 else 'N'}, {abs(lon):.1f}°{'W' if lon < 0 else 'E'}"

            if prev_point and prev_point.centroid_lat is not None and prev_point.centroid_lon is not None:
                disp_km = round(haversine_distance_km(prev_point.centroid_lat, prev_point.centroid_lon, lat, lon), 1)
                bearing_deg, bearing_card = calculate_bearing(prev_point.centroid_lat, prev_point.centroid_lon, lat, lon)
                speed = calculate_speed_kmh(disp_km, hours - prev_point.step_hours)
                area_diff, area_pct = calculate_area_change(prev_point.estimated_area_km2, area)
                if prev_point.max_magnitude is not None and mag is not None:
                    mag_diff = round(mag - prev_point.max_magnitude, 1)
                cumulative_distance_km += disp_km

            pt = TrackPoint(
                frame_index=idx,
                step_hours=hours,
                forecast_day=day,
                valid_time=valid_time,
                detection_status="DETECTED",
                event_id=f"EVT-STM-F{hours:03d}",
                centroid_lat=lat,
                centroid_lon=lon,
                coordinates_display=coord_str,
                estimated_area_km2=area,
                max_magnitude=mag,
                magnitude_unit=unit,
                severity=sev,
                polygon_coordinates=poly,
                displacement_km=disp_km,
                bearing_deg=bearing_deg,
                bearing_cardinal=bearing_card,
                speed_kmh=speed,
                area_change_km2=area_diff,
                area_change_pct=area_pct,
                magnitude_change=mag_diff
            )
            prev_point = pt
        else:
            pt = TrackPoint(
                frame_index=idx,
                step_hours=hours,
                forecast_day=day,
                valid_time=valid_time,
                detection_status=status
            )
        points.append(pt)

    net_disp = round(haversine_distance_km(14.5, 88.2, 19.8, 89.9), 1)

    return EventTrackDetail(
        track_id="TRK-STM-004",
        name="Bay of Bengal Severe Depression",
        category="severe_storm",
        hazard_type="Severe Storm",
        first_detection_lead_hours=24,
        latest_detection_lead_hours=96,
        total_detections=4,
        total_frames=10,
        initial_centroid=[14.5, 88.2],
        latest_centroid=[19.8, 89.9],
        cumulative_distance_km=round(cumulative_distance_km, 1),
        net_displacement_km=net_disp,
        mean_speed_kmh=round(cumulative_distance_km / 72.0, 1),
        peak_magnitude=105.0,
        magnitude_unit="km/h",
        peak_severity="High",
        max_area_km2=250000.0,
        status="ACTIVE",
        trajectory_line=trajectory_line,
        color="#F59E0B",
        data_provenance="DEMO_SYNTHETIC_DATASET",
        is_simulated=True,
        points=points,
        movement_notes="North-northeastward translation across central Bay of Bengal basin."
    )



def build_synthetic_ensemble_scenario() -> EventUncertaintyDetail:
    """
    Scenario 5: Reproducible 5-Member Synthetic Ensemble Demonstration
    Explicitly labeled: 'SYNTHETIC_ENSEMBLE_DEMO'
    Characteristics:
    - 5 reproducible perturbed members for the Cyclone event over Days 1-5.
    - Demonstrates member agreement decay from 100% to 60%.
    - Computes exact mean, std, IQR, and centroid spatial dispersion in km.
    """
    daily_spread = [
        DailyEnsembleSpread(
            forecast_day=1,
            step_hours=24,
            members_count=5,
            member_agreement_pct=100.0,
            mean_centroid=[-12.4, 78.6],
            centroid_spatial_dispersion_km=14.2,
            area_mean_km2=321000.0,
            area_std_km2=12400.0,
            area_iqr_km2=15000.0,
            magnitude_mean=125.8,
            magnitude_std=4.2,
            magnitude_unit="km/h",
            member_centroids=[
                [-12.4, 78.6], [-12.3, 78.7], [-12.5, 78.5], [-12.4, 78.8], [-12.3, 78.4]
            ]
        ),
        DailyEnsembleSpread(
            forecast_day=2,
            step_hours=48,
            members_count=5,
            member_agreement_pct=100.0,
            mean_centroid=[-13.8, 77.1],
            centroid_spatial_dispersion_km=32.8,
            area_mean_km2=368000.0,
            area_std_km2=24500.0,
            area_iqr_km2=31000.0,
            magnitude_mean=137.4,
            magnitude_std=7.5,
            magnitude_unit="km/h",
            member_centroids=[
                [-13.8, 77.1], [-13.6, 77.4], [-14.1, 76.8], [-13.7, 77.5], [-14.0, 76.7]
            ]
        ),
        DailyEnsembleSpread(
            forecast_day=3,
            step_hours=72,
            members_count=5,
            member_agreement_pct=100.0,
            mean_centroid=[-15.2, 75.4],
            centroid_spatial_dispersion_km=58.4,
            area_mean_km2=418000.0,
            area_std_km2=38200.0,
            area_iqr_km2=46000.0,
            magnitude_mean=149.2,
            magnitude_std=12.1,
            magnitude_unit="km/h",
            member_centroids=[
                [-15.2, 75.4], [-14.8, 75.9], [-15.6, 74.8], [-15.0, 76.1], [-15.4, 74.8]
            ]
        ),
        DailyEnsembleSpread(
            forecast_day=4,
            step_hours=96,
            members_count=5,
            member_agreement_pct=80.0,  # 4 of 5 detect
            mean_centroid=[-16.8, 73.5],
            centroid_spatial_dispersion_km=94.6,
            area_mean_km2=376000.0,
            area_std_km2=52000.0,
            area_iqr_km2=68000.0,
            magnitude_mean=131.0,
            magnitude_std=16.8,
            magnitude_unit="km/h",
            member_centroids=[
                [-16.8, 73.5], [-16.2, 74.3], [-17.4, 72.6], [-16.6, 74.2]
            ]
        ),
        DailyEnsembleSpread(
            forecast_day=5,
            step_hours=120,
            members_count=5,
            member_agreement_pct=60.0,  # 3 of 5 detect
            mean_centroid=[-18.5, 71.0],
            centroid_spatial_dispersion_km=142.1,
            area_mean_km2=248000.0,
            area_std_km2=68000.0,
            area_iqr_km2=85000.0,
            magnitude_mean=96.5,
            magnitude_std=21.4,
            magnitude_unit="km/h",
            member_centroids=[
                [-18.5, 71.0], [-17.7, 72.2], [-19.2, 69.8]
            ]
        ),
    ]

    return EventUncertaintyDetail(
        event_id="evt-001",
        track_id="TRK-CYC-001",
        uncertainty_mode="ENSEMBLE_MEMBERS",
        is_available=True,
        ensemble_members_count=5,
        daily_spread=daily_spread,
        lead_time_decay=STANDARD_LEAD_TIME_DECAY,
        methodology_notes=(
            "DEMO ONLY: Calculated across 5 reproducible synthetic ensemble members with controlled spatial "
            "perturbations. Spread reflects intra-ensemble standard deviation and member agreement percentage."
        ),
        known_limitations=[
            "Synthetic ensemble members are perturbed demonstrations; they do not represent operational GEFS 31-member runs.",
            "Member agreement decays beyond Day 4 due to divergent track trajectories."
        ]
    )
