"""
Unit Tests for Temporal Footprint Tracking Service
"""

import pytest
import numpy as np
from app.engine.config import TemporalTrackingConfig
from app.engine.schemas import FootprintEntity
from app.engine.tracker import TemporalEventTracker


@pytest.fixture
def tracking_config():
    return TemporalTrackingConfig(
        iou_threshold=0.15,
        max_centroid_displacement_km=850.0
    )


def test_temporal_tracking_association(tracking_config):
    # Footprint at T0 (24h lead)
    poly_t0 = [[[70.0, 10.0], [74.0, 10.0], [74.0, 14.0], [70.0, 14.0], [70.0, 10.0]]]
    prev_fp = FootprintEntity(
        cluster_id=1,
        event_id="HEAT-20250426-120_720",
        name="Thermal Anomaly",
        category="heat_wave",
        hazard_type="Heat Wave",
        severity="Medium",
        severity_level=2,
        primary_variable="temperature",
        canonical_unit="°C",
        centroid_lat=12.0,
        centroid_lon=72.0,
        coordinates_display="12.0°N, 72.0°E",
        bounds=[70.0, 10.0, 74.0, 14.0],
        estimated_area_km2=50000.0,
        cell_count=16,
        max_anomaly_score=2.8,
        mean_anomaly_score=2.2,
        peak_metric_value=42.0,
        polygon_coordinates=poly_t0,
        supporting_metrics={"max_temp_detected": 42.0},
        detection_method="Physical Threshold",
    )

    # Footprint at T1 (48h lead) shifted slightly northeast
    # [71.0, 11.0] to [75.0, 15.0] -> Significant spatial overlap with poly_t0
    poly_t1 = [[[71.0, 11.0], [75.0, 11.0], [75.0, 15.0], [71.0, 15.0], [71.0, 11.0]]]
    curr_fp = FootprintEntity(
        cluster_id=2,
        event_id="HEAT-20250427-130_730",
        name="Severe Heat Dome",
        category="heat_wave",
        hazard_type="Heat Wave",
        severity="High",
        severity_level=3,
        primary_variable="temperature",
        canonical_unit="°C",
        centroid_lat=13.0,
        centroid_lon=73.0,
        coordinates_display="13.0°N, 73.0°E",
        bounds=[71.0, 11.0, 75.0, 15.0],
        estimated_area_km2=60000.0,  # +20% area
        cell_count=20,
        max_anomaly_score=3.4,       # +0.6 magnitude
        mean_anomaly_score=2.7,
        peak_metric_value=44.5,
        polygon_coordinates=poly_t1,
        supporting_metrics={"max_temp_detected": 44.5},
        detection_method="Physical Threshold",
    )

    associations = TemporalEventTracker.track_footprints(
        current_footprints=[curr_fp],
        previous_footprints=[prev_fp],
        config=tracking_config
    )

    assert len(associations) == 1
    assoc = associations[0]
    assert assoc["current_event_id"] == "HEAT-20250427-130_730"
    assert assoc["previous_event_id"] == "HEAT-20250426-120_720"
    assert assoc["category"] == "heat_wave"
    assert assoc["iou_overlap"] > 0.3  # Shared 3x3 overlap out of 4x4
    assert assoc["area_change_pct"] == 20.0
    assert np.isclose(assoc["magnitude_change"], 0.6)
    assert assoc["displacement_km"] < 200.0
    assert assoc["status"] == "ASSOCIATED_TIMESTEP"


def test_temporal_tracking_different_category_no_link(tracking_config):
    # Overlapping coordinates but different categories (Heat Wave vs Cold Wave)
    poly = [[[70.0, 10.0], [74.0, 10.0], [74.0, 14.0], [70.0, 14.0], [70.0, 10.0]]]
    prev_fp = FootprintEntity(
        cluster_id=1,
        event_id="HEAT-20250426-120_720",
        name="Thermal Anomaly",
        category="heat_wave",
        hazard_type="Heat Wave",
        severity="Medium",
        severity_level=2,
        primary_variable="temperature",
        canonical_unit="°C",
        centroid_lat=12.0,
        centroid_lon=72.0,
        coordinates_display="12.0°N, 72.0°E",
        bounds=[70.0, 10.0, 74.0, 14.0],
        estimated_area_km2=50000.0,
        cell_count=16,
        max_anomaly_score=2.8,
        mean_anomaly_score=2.2,
        peak_metric_value=42.0,
        polygon_coordinates=poly,
        detection_method="Physical Threshold",
    )

    curr_fp = FootprintEntity(
        cluster_id=2,
        event_id="COLD-20250427-120_720",
        name="Cold Wave Outbreak",
        category="cold_wave",
        hazard_type="Cold Wave",
        severity="High",
        severity_level=3,
        primary_variable="temperature",
        canonical_unit="°C",
        centroid_lat=12.0,
        centroid_lon=72.0,
        coordinates_display="12.0°N, 72.0°E",
        bounds=[70.0, 10.0, 74.0, 14.0],
        estimated_area_km2=50000.0,
        cell_count=16,
        max_anomaly_score=3.2,
        mean_anomaly_score=2.5,
        peak_metric_value=-5.0,
        polygon_coordinates=poly,
        detection_method="Physical Threshold",
    )

    associations = TemporalEventTracker.track_footprints(
        current_footprints=[curr_fp],
        previous_footprints=[prev_fp],
        config=tracking_config
    )

    # Must NOT link different meteorological categories
    assert len(associations) == 0
