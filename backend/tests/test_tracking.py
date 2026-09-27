"""
Comprehensive Automated Test Suite for Phase 6: Event Tracking & Forecast Uncertainty
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.tracking.geo_math import (
    haversine_distance_km,
    calculate_bearing,
    calculate_speed_kmh,
    calculate_area_change,
    calculate_centroid_dispersion_km,
    wrap_longitude
)
from app.tracking.service import TrackingService
from app.tracking.uncertainty import UncertaintyService
from app.tracking.scenarios import (
    build_cyclone_track,
    build_heatwave_track,
    build_coldwave_track,
    build_synthetic_ensemble_scenario
)

client = TestClient(app)


class TestGeodesicMath:
    """Tests for geospatial distance, bearing, and wraparound math."""

    def test_haversine_same_point(self):
        dist = haversine_distance_km(15.0, 75.0, 15.0, 75.0)
        assert dist == pytest.approx(0.0, abs=1e-3)

    def test_haversine_known_distance(self):
        # Mumbai (19.0760, 72.8777) to Delhi (28.7041, 77.1025) is approx 1148 km
        dist = haversine_distance_km(19.0760, 72.8777, 28.7041, 77.1025)
        assert 1140.0 < dist < 1160.0

    def test_haversine_longitude_antimeridian_wraparound(self):
        # 179°E to -179°W at equator is 2° longitude apart (~222 km), NOT 358° (~39,800 km)
        dist = haversine_distance_km(0.0, 179.0, 0.0, -179.0)
        assert 220.0 < dist < 225.0

    def test_wrap_longitude(self):
        assert wrap_longitude(180.0) == 180.0
        assert wrap_longitude(190.0) == -170.0
        assert wrap_longitude(-190.0) == 170.0
        assert wrap_longitude(360.0) == 0.0

    def test_calculate_bearing_cardinal(self):
        # Directly North
        bearing, card = calculate_bearing(0.0, 0.0, 10.0, 0.0)
        assert bearing == 0.0
        assert card == "N"

        # Directly East
        bearing, card = calculate_bearing(0.0, 0.0, 0.0, 10.0)
        assert bearing == 90.0
        assert card == "E"

        # Stationary point
        bearing, card = calculate_bearing(10.0, 20.0, 10.0, 20.0)
        assert bearing == 0.0
        assert card == "STATIONARY"

    def test_calculate_speed_kmh(self):
        # 240 km in 24 hours -> 10.0 km/h
        speed = calculate_speed_kmh(240.0, 24.0)
        assert speed == 10.0

        # Zero delta hours
        assert calculate_speed_kmh(100.0, 0.0) == 0.0

    def test_calculate_area_change(self):
        diff, pct = calculate_area_change(100000.0, 125000.0)
        assert diff == 25000.0
        assert pct == 25.0

        # None input handling
        diff_none, pct_none = calculate_area_change(None, 50000.0)
        assert diff_none is None
        assert pct_none is None

    def test_centroid_spatial_dispersion(self):
        # 3 points forming a triangle
        centroids = [[10.0, 20.0], [10.2, 20.0], [10.1, 20.2]]
        disp = calculate_centroid_dispersion_km(centroids)
        assert disp > 0.0
        assert disp < 25.0


class TestSyntheticScenarios:
    """Validates the 5 reproducible synthetic evaluation scenarios."""

    def test_scenario1_cyclone_track_shifting_and_area_evolution(self):
        track = build_cyclone_track()
        assert track.track_id == "TRK-CYC-001"
        assert track.category == "cyclone"
        assert track.total_detections == 5
        assert track.total_frames == 10

        # Check movement: initial centroid (-12.4, 78.6) to (-18.5, 71.0)
        assert track.initial_centroid == [-12.4, 78.6]
        assert track.latest_centroid == [-18.5, 71.0]
        assert track.net_displacement_km > 800.0

        # Area growth then contraction
        detected_points = [p for p in track.points if p.detection_status == "DETECTED"]
        assert len(detected_points) == 5
        assert detected_points[0].estimated_area_km2 == 320000.0
        assert detected_points[2].estimated_area_km2 == 420000.0  # peak
        assert detected_points[4].estimated_area_km2 == 245000.0  # contracted

        # Later frames must be DISSIPATED or MISSING without fake coordinates
        missing_points = [p for p in track.points if p.detection_status != "DETECTED"]
        assert len(missing_points) == 5
        for mp in missing_points:
            assert mp.centroid_lat is None
            assert mp.centroid_lon is None

    def test_scenario2_heatwave_track_growth_and_dissipation(self):
        track = build_heatwave_track()
        assert track.track_id == "TRK-HEAT-002"
        assert track.category == "heat_wave"
        assert track.total_detections == 4

        # Footprint area peak
        assert track.max_area_km2 == 610000.0
        # Peak temperature
        assert track.peak_magnitude == 44.8

    def test_scenario3_coldwave_intermittent_missing_frame(self):
        track = build_coldwave_track()
        assert track.status == "INTERMITTENT"
        assert track.total_detections == 3

        # Frame index 2 (Day 3, Step 72h) must be explicitly MISSING
        day3_point = track.points[2]
        assert day3_point.forecast_day == 3
        assert day3_point.detection_status == "MISSING"
        assert day3_point.centroid_lat is None

        # Day 4 is DETECTED and computes speed across the 48h gap
        day4_point = track.points[3]
        assert day4_point.forecast_day == 4
        assert day4_point.detection_status == "DETECTED"
        assert day4_point.speed_kmh is not None

    def test_scenario5_synthetic_ensemble_spread_and_agreement(self):
        ens = build_synthetic_ensemble_scenario()
        assert ens.uncertainty_mode == "ENSEMBLE_MEMBERS"
        assert ens.ensemble_members_count == 5
        assert len(ens.daily_spread) == 5

        # Check agreement decay across days
        assert ens.daily_spread[0].member_agreement_pct == 100.0
        assert ens.daily_spread[3].member_agreement_pct == 80.0
        assert ens.daily_spread[4].member_agreement_pct == 60.0

        # Centroid spatial dispersion increases over time
        disp_day1 = ens.daily_spread[0].centroid_spatial_dispersion_km
        disp_day5 = ens.daily_spread[4].centroid_spatial_dispersion_km
        assert disp_day5 > disp_day1


class TestTrackingService:
    """Validates the TrackingService logic and non-merging rules."""

    def test_list_tracks(self):
        svc = TrackingService()
        tracks = svc.list_tracks()
        assert len(tracks) >= 3
        ids = [t.track_id for t in tracks]
        assert "TRK-CYC-001" in ids
        assert "TRK-HEAT-002" in ids
        assert "TRK-COLD-003" in ids

    def test_filter_tracks_by_category(self):
        svc = TrackingService()
        cyclone_tracks = svc.list_tracks(category="cyclone")
        assert len(cyclone_tracks) == 1
        assert cyclone_tracks[0].track_id == "TRK-CYC-001"

    def test_get_track_detail_and_history(self):
        svc = TrackingService()
        detail = svc.get_track("TRK-CYC-001")
        assert detail is not None
        assert detail.track_id == "TRK-CYC-001"
        assert len(detail.points) == 10

        history = svc.get_track_history("TRK-CYC-001")
        assert history is not None
        assert len(history) == 10

    def test_unrelated_events_not_merged(self):
        """
        Scenario 4: Two events with different categories (Cyclone vs Heat Wave)
        or large spatial distance must NEVER be merged into a single track.
        """
        frames = [
            # Day 1: Cyclone in Indian Ocean & Heat Wave in Central Asia
            {"id": "EVT-1", "step_hours": 24, "category_key": "cyclone", "type": "Cyclone", "lat": -12.4, "lon": 78.6, "estimated_area_km2": 320000.0},
            {"id": "EVT-2", "step_hours": 24, "category_key": "heat_wave", "type": "Heat Wave", "lat": 45.2, "lon": 67.1, "estimated_area_km2": 420000.0},
            # Day 2: Consecutive steps
            {"id": "EVT-3", "step_hours": 48, "category_key": "cyclone", "type": "Cyclone", "lat": -13.8, "lon": 77.1, "estimated_area_km2": 365000.0},
            {"id": "EVT-4", "step_hours": 48, "category_key": "heat_wave", "type": "Heat Wave", "lat": 45.8, "lon": 68.5, "estimated_area_km2": 540000.0},
        ]

        tracks = TrackingService.associate_sequential_events(frames, max_displacement_km=850.0)
        # Must produce exactly 2 separate tracks
        assert len(tracks) == 2
        categories = set(t.category for t in tracks)
        assert categories == {"cyclone", "heat_wave"}

        # Cyclone track must not contain the heat wave coords
        cyc_track = next(t for t in tracks if t.category == "cyclone")
        assert cyc_track.initial_centroid == [-12.4, 78.6]
        assert cyc_track.latest_centroid == [-13.8, 77.1]


class TestUncertaintyService:
    """Validates deterministic vs ensemble uncertainty handling."""

    def test_deterministic_summary_mode(self):
        summary = UncertaintyService.get_summary()
        assert summary.uncertainty_mode == "DETERMINISTIC_ONLY"
        assert summary.is_available is False
        assert summary.ensemble_members_count == 1
        assert len(summary.lead_time_decay) == 10
        assert "Ensemble spread is unavailable" in summary.message

    def test_ensemble_summary_mode(self):
        summary = UncertaintyService.get_summary(dataset_id="synthetic_ensemble_demo")
        assert summary.uncertainty_mode == "ENSEMBLE_MEMBERS"
        assert summary.is_available is True
        assert summary.ensemble_members_count == 5

    def test_event_uncertainty_cyclone_demo(self):
        unc = UncertaintyService.get_event_uncertainty("TRK-CYC-001")
        assert unc.uncertainty_mode == "ENSEMBLE_MEMBERS"
        assert unc.is_available is True
        assert unc.ensemble_members_count == 5
        assert len(unc.daily_spread) == 5

    def test_event_uncertainty_deterministic_fallback(self):
        unc = UncertaintyService.get_event_uncertainty("TRK-HEAT-002")
        assert unc.uncertainty_mode == "DETERMINISTIC_ONLY"
        assert unc.is_available is False
        assert unc.ensemble_members_count == 1
        assert len(unc.daily_spread) == 0
        assert len(unc.lead_time_decay) == 10


class TestTrackingAPIRoutes:
    """Integration tests for all Phase 6 tracking and uncertainty REST endpoints."""

    def test_get_tracks_endpoint(self):
        response = client.get("/api/events/tracks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        assert any(t["track_id"] == "TRK-CYC-001" for t in data)

    def test_get_tracks_with_category_filter(self):
        response = client.get("/api/events/tracks?category=heat_wave")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["track_id"] == "TRK-HEAT-002"

    def test_get_track_detail_success(self):
        response = client.get("/api/events/tracks/TRK-CYC-001")
        assert response.status_code == 200
        data = response.json()
        assert data["track_id"] == "TRK-CYC-001"
        assert data["category"] == "cyclone"
        assert "points" in data
        assert len(data["points"]) == 10
        assert "movement_notes" in data

    def test_get_track_detail_not_found(self):
        response = client.get("/api/events/tracks/NONEXISTENT_TRACK")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_track_history_endpoint(self):
        response = client.get("/api/events/tracks/TRK-CYC-001/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 10
        assert data[0]["forecast_day"] == 1
        assert data[0]["detection_status"] == "DETECTED"

    def test_get_uncertainty_endpoint_default(self):
        response = client.get("/api/uncertainty")
        assert response.status_code == 200
        data = response.json()
        assert data["uncertainty_mode"] == "DETERMINISTIC_ONLY"
        assert data["is_available"] is False
        assert data["ensemble_members_count"] == 1
        assert len(data["lead_time_decay"]) == 10

    def test_get_uncertainty_endpoint_ensemble_mode(self):
        response = client.get("/api/uncertainty?mode=ensemble")
        assert response.status_code == 200
        data = response.json()
        assert data["uncertainty_mode"] == "ENSEMBLE_MEMBERS"
        assert data["is_available"] is True
        assert data["ensemble_members_count"] == 5

    def test_get_event_uncertainty_endpoint(self):
        response = client.get("/api/uncertainty/evt-001")
        assert response.status_code == 200
        data = response.json()
        assert data["event_id"] == "evt-001"
        assert data["is_available"] is True
        assert len(data["daily_spread"]) == 5
