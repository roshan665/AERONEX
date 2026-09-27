"""
Unit Tests for Forecast Uncertainty Service & Descriptive Statistics
"""

import pytest
from app.ml.uncertainty import ForecastUncertaintyService


def test_ensemble_descriptive_statistics():
    members = [24.0, 25.0, 26.0, 27.0, 28.0]
    stats = ForecastUncertaintyService.calculate_ensemble_statistics(members, missing_member_fraction=0.0)

    assert stats["mean"] == 26.0
    assert stats["std"] > 1.0
    assert stats["member_count"] == 5
    assert stats["missing_member_fraction"] == 0.0

    quantiles = stats["quantiles"]
    assert quantiles.p10 <= quantiles.p25 <= quantiles.p50 <= quantiles.p75 <= quantiles.p90
    assert quantiles.p50 == 26.0


def test_uncertainty_series_ensemble_mode():
    series = ForecastUncertaintyService.get_variable_uncertainty(variable="temperature", mode="ensemble")

    assert series.variable == "temperature"
    assert series.is_available is True
    assert series.uncertainty_mode == "ENSEMBLE_MEMBERS"
    assert series.member_count == 5
    assert len(series.timeline) == 10

    first_pt = series.timeline[0]
    assert first_pt.lead_day == 1
    assert first_pt.ensemble_std > 0.0
    assert first_pt.quantiles.p10 <= first_pt.quantiles.p90
    assert len(series.caveats) >= 2


def test_uncertainty_series_deterministic_unavailable_mode():
    series = ForecastUncertaintyService.get_variable_uncertainty(variable="wind", mode="deterministic")

    assert series.variable == "wind"
    assert series.is_available is False
    assert series.uncertainty_mode == "DETERMINISTIC_ONLY"
    assert series.member_count == 1
    assert series.empty_state_explanation is not None
    assert "No multi-member ensemble forecast is configured" in series.empty_state_explanation
    assert len(series.caveats) >= 2
