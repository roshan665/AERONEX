"""
Unit Tests for AeroNex Meteorological Anomaly Detectors
"""

import pytest
import numpy as np
from app.engine.config import DetectorThresholds
from app.engine.schemas import NormalizedWeatherGrid
from app.engine.detectors.base import BaseAnomalyDetector
from app.engine.detectors.temperature_detector import TemperatureAnomalyDetector
from app.engine.detectors.wind_detector import WindAnomalyDetector
from app.engine.detectors.pressure_detector import PressureAnomalyDetector
from app.engine.detectors.precipitation_detector import PrecipitationAnomalyDetector


@pytest.fixture
def base_thresholds():
    return DetectorThresholds()


@pytest.fixture
def empty_grid():
    lats = np.linspace(10.0, 20.0, 11)
    lons = np.linspace(70.0, 80.0, 11)
    return NormalizedWeatherGrid(
        forecast_init_time="2025-04-26T00:00:00Z",
        valid_time="2025-04-27T00:00:00Z",
        lead_time_hours=24,
        lead_day=1,
        lats=lats,
        lons=lons,
        shape=(11, 11),
    )


def test_base_detector_safe_zscore_epsilon():
    observed = np.array([10.0, 20.0, 30.0])
    mean = np.array([10.0, 10.0, 10.0])
    # Near-zero standard deviation
    std = np.array([0.0, 1e-8, 5.0])

    z = BaseAnomalyDetector.compute_zscore(observed, mean, std, epsilon=1e-6)

    # Where std was 0 or below epsilon, result must be 0.0 without crash
    assert z[0] == 0.0
    assert z[1] == 0.0
    # Where std is valid: (30 - 10) / 5 = 4.0
    assert np.isclose(z[2], 4.0)
    assert not np.isnan(z).any()
    assert not np.isinf(z).any()


def test_temperature_detector_threshold_only(base_thresholds, empty_grid):
    detector = TemperatureAnomalyDetector(base_thresholds)
    
    # Create grid with normal background (30°C), a heat dome cell (45°C), and cold cell (-5°C)
    temp = np.full((11, 11), 30.0)
    temp[2, 2] = 45.0   # Heat dome
    temp[8, 8] = 2.0    # Cold wave (<= 4.0°C)
    
    empty_grid.temperature_celsius = temp
    results = detector.detect(empty_grid)

    assert len(results) == 2
    heat_res = next(r for r in results if r.category == "heat_wave")
    cold_res = next(r for r in results if r.category == "cold_wave")

    assert heat_res.detected_cell_count == 1
    assert heat_res.mask[2, 2] == True
    assert heat_res.metadata["max_temp_detected"] == 45.0
    assert "Configurable Physical" in heat_res.method

    assert cold_res.detected_cell_count == 1
    assert cold_res.mask[8, 8] == True
    assert cold_res.metadata["min_temp_detected"] == 2.0


def test_temperature_detector_climatology_zscore(base_thresholds, empty_grid):
    detector = TemperatureAnomalyDetector(base_thresholds)

    temp = np.full((11, 11), 32.0)
    clim_mean = np.full((11, 11), 30.0)
    clim_std = np.full((11, 11), 2.0)

    # Injected anomaly: 41°C (Z = (41-30)/2 = 5.5σ)
    temp[5, 5] = 41.0

    empty_grid.temperature_celsius = temp
    empty_grid.temp_clim_mean = clim_mean
    empty_grid.temp_clim_std = clim_std

    results = detector.detect(empty_grid)
    assert len(results) == 1
    heat = results[0]
    assert heat.category == "heat_wave"
    assert heat.mask[5, 5] == True
    assert np.isclose(heat.score_grid[5, 5], 5.5)
    assert "Hybrid" in heat.method


def test_wind_detector_gale_and_storm(base_thresholds, empty_grid):
    detector = WindAnomalyDetector(base_thresholds)

    # Background wind: 8 m/s, Gale cell: 25 m/s (~90 km/h)
    wind = np.full((11, 11), 8.0)
    wind[3, 3] = 25.0

    empty_grid.wind_speed_ms = wind
    results = detector.detect(empty_grid)

    assert len(results) == 1
    res = results[0]
    assert res.category == "wind_anomaly"
    assert res.mask[3, 3] == True
    assert res.metadata["max_wind_ms"] == 25.0
    assert np.isclose(res.metadata["max_wind_kmh"], 90.0)


def test_pressure_detector_cyclonic_depression(base_thresholds, empty_grid):
    detector = PressureAnomalyDetector(base_thresholds)

    # Background MSLP: 1012 hPa, Deep Depression: 970 hPa
    mslp = np.full((11, 11), 1012.0)
    mslp[4, 4] = 970.0

    empty_grid.mslp_hpa = mslp
    results = detector.detect(empty_grid)

    assert len(results) == 1
    res = results[0]
    assert res.category == "pressure_anomaly"
    assert res.mask[4, 4] == True
    assert res.metadata["min_mslp_hpa"] == 970.0
    assert np.isclose(res.metadata["pressure_deficit_hpa"], 1013.25 - 970.0, atol=0.1)


def test_precipitation_detector_heavy_rainfall(base_thresholds, empty_grid):
    detector = PrecipitationAnomalyDetector(base_thresholds)

    # Background: 10 mm, Extreme rain: 150 mm / 24h
    precip = np.full((11, 11), 10.0)
    precip[6, 6] = 150.0

    empty_grid.precipitation_mm = precip
    empty_grid.precipitation_accumulation_hours = 24

    results = detector.detect(empty_grid)
    assert len(results) == 1
    res = results[0]
    assert res.category == "precipitation_anomaly"
    assert res.mask[6, 6] == True
    assert res.metadata["max_precip_mm"] == 150.0
    assert res.metadata["accumulation_period_hours"] == 24


def test_detectors_handle_nan_values(base_thresholds, empty_grid):
    temp_detector = TemperatureAnomalyDetector(base_thresholds)
    wind_detector = WindAnomalyDetector(base_thresholds)

    temp = np.full((11, 11), np.nan)
    wind = np.full((11, 11), np.nan)

    empty_grid.temperature_celsius = temp
    empty_grid.wind_speed_ms = wind

    # Should safely return empty results, NOT treat NaNs as anomalies
    assert temp_detector.detect(empty_grid) == []
    assert wind_detector.detect(empty_grid) == []
