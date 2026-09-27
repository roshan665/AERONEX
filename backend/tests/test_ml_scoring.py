"""
Unit Tests for Phase 6 Multi-Component Anomaly Scoring Framework
"""

import pytest
from app.ml.scoring import AnomalyScoringService
from app.ml.schemas import ScoringWeightsConfig, CompositeAnomalyScore


def test_temperature_normalization_bounds():
    # Normal temperature departure
    score, raw, interp = AnomalyScoringService.normalize_temperature(30.0, baseline_celsius=28.0, clim_std=2.5)
    assert 0.0 <= score <= 1.0
    assert raw == 30.0
    assert "Thermal departure" in interp

    # Extreme heat departure (+15°C anomaly)
    score_extreme, _, _ = AnomalyScoringService.normalize_temperature(45.0, baseline_celsius=28.0, clim_std=2.5)
    assert 0.8 <= score_extreme <= 1.0

    # None input
    score_none, raw_none, _ = AnomalyScoringService.normalize_temperature(None)
    assert score_none == 0.0
    assert raw_none is None


def test_wind_normalization_bounds():
    # Ambient breeze
    score_breeze, _, _ = AnomalyScoringService.normalize_wind(20.0)
    assert 0.0 <= score_breeze <= 0.1

    # Severe tropical cyclone force
    score_cyclone, raw, interp = AnomalyScoringService.normalize_wind(165.0)
    assert 0.8 <= score_cyclone <= 1.0
    assert raw == 165.0
    assert "Peak sustained wind" in interp


def test_pressure_normalization_bounds():
    # Ambient standard pressure
    score_std, _, _ = AnomalyScoringService.normalize_pressure(1013.25)
    assert score_std == 0.0

    # Deep cyclone deficit (940 hPa)
    score_deep, raw, interp = AnomalyScoringService.normalize_pressure(940.0)
    assert 0.8 <= score_deep <= 1.0
    assert raw == 940.0
    assert "barometric deficit" in interp


def test_spatial_extent_logarithmic_normalization():
    # Small localized footprint (5,000 km²)
    s_small, _, _ = AnomalyScoringService.normalize_spatial_extent(5000.0)
    assert s_small == 0.0

    # Synoptic macroscale footprint (750,000 km²)
    s_large, _, _ = AnomalyScoringService.normalize_spatial_extent(750000.0)
    assert s_large == 1.0

    # Mid-scale footprint (60,000 km²)
    s_mid, _, _ = AnomalyScoringService.normalize_spatial_extent(60000.0)
    assert 0.0 < s_mid < 1.0


def test_weights_validation_and_composite_score():
    # Valid weights
    valid_weights = ScoringWeightsConfig(
        w_temp=0.30,
        w_wind=0.20,
        w_pressure=0.20,
        w_spatial=0.10,
        w_persistence=0.10,
        w_quality=0.10
    )
    assert valid_weights is not None

    # Invalid weights sum
    with pytest.raises(ValueError):
        ScoringWeightsConfig(
            w_temp=0.50,
            w_wind=0.50,
            w_pressure=0.50,
            w_spatial=0.10,
            w_persistence=0.10,
            w_quality=0.10
        )


def test_composite_anomaly_score_full_synthesis():
    result = AnomalyScoringService.compute_composite_score(
        event_id="TEST-CYC-001",
        observed_temperature=31.5,
        baseline_temperature=28.0,
        clim_temp_std=2.0,
        max_wind_kmh=150.0,
        min_mslp_hpa=955.0,
        area_km2=320000.0,
        forecast_days=[1, 2, 3, 4],
        missing_cell_fraction=0.0
    )

    assert isinstance(result, CompositeAnomalyScore)
    assert result.event_id == "TEST-CYC-001"
    assert 0.0 <= result.composite_score <= 1.0
    assert 0.0 <= result.overall_score_100 <= 100.0
    assert result.is_probability is False  # Must NOT be presented as a probability
    assert result.severity_tier in ["High", "Extreme"]
    assert len(result.primary_contributing_variables) >= 1
    assert "thermal_deviation" in result.components
    assert "wind_magnitude" in result.components
    assert "pressure_deficit" in result.components
    assert "spatial_extent" in result.components
    assert "temporal_persistence" in result.components
    assert "data_quality" in result.components

    # Verify each component is properly normalized
    for comp in result.components.values():
        assert 0.0 <= comp.normalized_score <= 1.0
        assert comp.weight >= 0.0
        assert 0.0 <= comp.contribution_percent <= 100.0
        assert len(comp.interpretation) > 0

    assert len(result.score_limitations) >= 2
