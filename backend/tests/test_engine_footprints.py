"""
Unit Tests for Geospatial Footprint Extraction & Connected-Component Clustering
"""

import pytest
import numpy as np
from app.engine.config import FootprintConfig, DetectorThresholds
from app.engine.schemas import DetectionResult
from app.engine.footprints import FootprintExtractor


@pytest.fixture
def test_coords():
    lats = np.linspace(10.0, 20.0, 11)  # 1.0 deg spacing
    lons = np.linspace(70.0, 80.0, 11)  # 1.0 deg spacing
    return lats, lons


@pytest.fixture
def default_config():
    return FootprintConfig(
        connectivity=8,
        min_cells=2,
        min_area_km2=1000.0,
        simplify_tolerance_deg=0.05
    )


@pytest.fixture
def default_thresholds():
    return DetectorThresholds()


def test_connectivity_4_vs_8(test_coords, default_thresholds):
    lats, lons = test_coords
    
    # Create two diagonally adjacent cells: (4, 4) and (5, 5)
    mask = np.zeros((11, 11), dtype=bool)
    mask[4, 4] = True
    mask[5, 5] = True
    score_grid = np.where(mask, 3.5, 0.0)

    det = DetectionResult(
        variable="temperature",
        category="heat_wave",
        method="Test Method",
        mask=mask,
        score_grid=score_grid,
        threshold_value=40.0,
        canonical_unit="°C",
        detected_cell_count=2,
        metadata={"max_temp_detected": 44.0}
    )

    # Under 8-connectivity: diagonally adjacent cells form 1 component
    config_8 = FootprintConfig(connectivity=8, min_cells=1, min_area_km2=0.0)
    footprints_8 = FootprintExtractor.extract_footprints(det, lats, lons, config_8, default_thresholds)
    assert len(footprints_8) == 1
    assert footprints_8[0].cell_count == 2

    # Under 4-connectivity: diagonally adjacent cells form 2 separate components
    config_4 = FootprintConfig(connectivity=4, min_cells=1, min_area_km2=0.0)
    footprints_4 = FootprintExtractor.extract_footprints(det, lats, lons, config_4, default_thresholds)
    assert len(footprints_4) == 2
    assert footprints_4[0].cell_count == 1
    assert footprints_4[1].cell_count == 1


def test_cosine_latitude_area_scaling(default_config, default_thresholds):
    """
    Validates spherical area calculation:
    Area at 60° latitude should be approximately half of area at equator (cos(60°) = 0.5).
    """
    ddeg = 1.0
    lats_eq = np.array([0.0, 1.0])
    lons_eq = np.array([70.0, 71.0])

    lats_pole = np.array([60.0, 61.0])
    lons_pole = np.array([70.0, 71.0])

    # Single cell mask
    mask = np.array([[True, False], [False, False]])
    score = np.array([[3.0, 0.0], [0.0, 0.0]])

    det = DetectionResult(
        variable="temperature",
        category="heat_wave",
        method="Test",
        mask=mask,
        score_grid=score,
        threshold_value=40.0,
        canonical_unit="°C",
        detected_cell_count=1,
        metadata={"max_temp_detected": 43.0}
    )

    cfg = FootprintConfig(connectivity=8, min_cells=1, min_area_km2=0.0)

    fps_eq = FootprintExtractor.extract_footprints(det, lats_eq, lons_eq, cfg, default_thresholds)
    fps_pole = FootprintExtractor.extract_footprints(det, lats_pole, lons_pole, cfg, default_thresholds)

    area_eq = fps_eq[0].estimated_area_km2
    area_pole = fps_pole[0].estimated_area_km2

    # Ratio should be close to cos(60°) / cos(0°) = 0.5
    ratio = area_pole / area_eq
    assert np.isclose(ratio, 0.5, atol=0.05)


def test_minimum_area_filtering(test_coords, default_thresholds):
    lats, lons = test_coords
    mask = np.zeros((11, 11), dtype=bool)
    mask[2, 2] = True
    score_grid = np.where(mask, 3.0, 0.0)

    det = DetectionResult(
        variable="wind_speed",
        category="wind_anomaly",
        method="Test",
        mask=mask,
        score_grid=score_grid,
        threshold_value=17.5,
        canonical_unit="m/s",
        detected_cell_count=1,
        metadata={"max_wind_ms": 20.0}
    )

    # Min area set impossibly high -> should filter out
    cfg_strict = FootprintConfig(connectivity=8, min_cells=1, min_area_km2=1_000_000.0)
    footprints = FootprintExtractor.extract_footprints(det, lats, lons, cfg_strict, default_thresholds)
    assert len(footprints) == 0


def test_geojson_polygon_structure_and_rfc7946(test_coords, default_thresholds):
    lats, lons = test_coords
    # 2x2 contiguous block
    mask = np.zeros((11, 11), dtype=bool)
    mask[4:6, 4:6] = True
    score_grid = np.where(mask, 4.0, 0.0)

    det = DetectionResult(
        variable="temperature",
        category="heat_wave",
        method="Test",
        mask=mask,
        score_grid=score_grid,
        threshold_value=40.0,
        canonical_unit="°C",
        detected_cell_count=4,
        metadata={"max_temp_detected": 46.0}
    )

    cfg = FootprintConfig(connectivity=8, min_cells=2, min_area_km2=100.0)
    footprints = FootprintExtractor.extract_footprints(det, lats, lons, cfg, default_thresholds)

    assert len(footprints) == 1
    fp = footprints[0]

    # Verify polygon coordinates structure [[[lon, lat], ...]]
    assert isinstance(fp.polygon_coordinates, list)
    assert len(fp.polygon_coordinates) >= 1
    ring = fp.polygon_coordinates[0]
    assert len(ring) >= 4

    # RFC 7946: Closed ring (first coord == last coord)
    assert ring[0] == ring[-1]

    # RFC 7946: Longitude first [-180, 180], then Latitude [-90, 90]
    for pt in ring:
        lon_val, lat_val = pt[0], pt[1]
        assert -180.0 <= lon_val <= 180.0
        assert -90.0 <= lat_val <= 90.0
        # Centroid within bounding box
        assert fp.bounds[0] <= lon_val <= fp.bounds[2]
        assert fp.bounds[1] <= lat_val <= fp.bounds[3]
