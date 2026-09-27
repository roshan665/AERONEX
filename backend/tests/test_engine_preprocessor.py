"""
Unit Tests for Weather Grid Preprocessing and Coordinate Normalization
"""

import pytest
import numpy as np
from app.engine.schemas import WeatherGridDataset
from app.engine.preprocessor import GridPreprocessor


def test_preprocessor_coordinate_validation():
    # Test valid grid
    lats = np.array([10.0, 20.0, 30.0])
    lons = np.array([70.0, 80.0, 90.0])
    dataset = WeatherGridDataset(
        forecast_init_time="2025-04-26T00:00:00Z",
        valid_time="2025-04-27T00:00:00Z",
        lead_time_hours=24,
        lats=lats,
        lons=lons,
        variables={
            "temperature": np.full((3, 3), 300.0),
            "mslp": np.full((3, 3), 101325.0),
            "wind_speed": np.full((3, 3), 10.0),
        },
        units={"temperature": "K", "mslp": "Pa", "wind_speed": "m/s"},
    )
    grid = GridPreprocessor.preprocess(dataset)
    assert grid.shape == (3, 3)
    assert grid.lead_day == 1

    # Unit conversions verified
    assert np.isclose(grid.temperature_celsius[0, 0], 300.0 - 273.15, atol=1e-3)
    assert np.isclose(grid.mslp_hpa[0, 0], 1013.25, atol=1e-3)
    assert grid.wind_speed_ms[0, 0] == 10.0


def test_preprocessor_longitude_wrapping():
    lats = np.array([10.0, 20.0])
    lons = np.array([350.0, 355.0])  # In [0, 360)
    dataset = WeatherGridDataset(
        forecast_init_time="2025-04-26T00:00:00Z",
        valid_time="2025-04-27T00:00:00Z",
        lead_time_hours=24,
        lats=lats,
        lons=lons,
        variables={"temperature": np.full((2, 2), 25.0)},
        units={"temperature": "C"},
    )
    grid = GridPreprocessor.preprocess(dataset)
    # Longitudes must be wrapped to [-180, 180]
    assert np.all(grid.lons <= 180.0)
    assert np.all(grid.lons >= -180.0)
    assert any("Normalized longitudes" in w for w in grid.preprocessing_warnings)


def test_preprocessor_out_of_bounds_latitude():
    lats = np.array([85.0, 95.0])  # 95 > 90
    lons = np.array([10.0, 20.0])
    dataset = WeatherGridDataset(
        forecast_init_time="2025-04-26T00:00:00Z",
        valid_time="2025-04-27T00:00:00Z",
        lead_time_hours=24,
        lats=lats,
        lons=lons,
        variables={"temperature": np.full((2, 2), 25.0)},
        units={"temperature": "C"},
    )
    with pytest.raises(ValueError, match="Latitude values out of permissible range"):
        GridPreprocessor.preprocess(dataset)


def test_preprocessor_shape_mismatch():
    lats = np.array([10.0, 20.0, 30.0])
    lons = np.array([70.0, 80.0])
    dataset = WeatherGridDataset(
        forecast_init_time="2025-04-26T00:00:00Z",
        valid_time="2025-04-27T00:00:00Z",
        lead_time_hours=24,
        lats=lats,
        lons=lons,
        variables={"temperature": np.full((4, 4), 25.0)},  # Shape mismatch
        units={"temperature": "C"},
    )
    with pytest.raises(ValueError, match="does not match coordinate grid dimensions"):
        GridPreprocessor.preprocess(dataset)


def test_preprocessor_orthogonal_wind_derivation():
    lats = np.array([10.0, 20.0])
    lons = np.array([70.0, 80.0])
    dataset = WeatherGridDataset(
        forecast_init_time="2025-04-26T00:00:00Z",
        valid_time="2025-04-27T00:00:00Z",
        lead_time_hours=24,
        lats=lats,
        lons=lons,
        variables={
            "u10": np.full((2, 2), 3.0),
            "v10": np.full((2, 2), 4.0),
        },
        units={"u10": "m/s", "v10": "m/s"},
    )
    grid = GridPreprocessor.preprocess(dataset)
    # sqrt(3^2 + 4^2) = 5.0
    assert np.isclose(grid.wind_speed_ms[0, 0], 5.0)


def test_preprocessor_nan_handling():
    lats = np.array([10.0, 20.0])
    lons = np.array([70.0, 80.0])
    temp_with_nan = np.array([[25.0, np.nan], [np.inf, 28.0]])
    dataset = WeatherGridDataset(
        forecast_init_time="2025-04-26T00:00:00Z",
        valid_time="2025-04-27T00:00:00Z",
        lead_time_hours=24,
        lats=lats,
        lons=lons,
        variables={"temperature": temp_with_nan},
        units={"temperature": "C"},
    )
    grid = GridPreprocessor.preprocess(dataset)
    assert np.isnan(grid.temperature_celsius[0, 1])
    assert np.isnan(grid.temperature_celsius[1, 0])  # Inf converted to NaN
    assert grid.temperature_celsius[0, 0] == 25.0
    assert any("Infinite values detected" in w for w in grid.preprocessing_warnings)
