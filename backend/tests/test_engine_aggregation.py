"""
Unit Tests for Event Aggregation & Physical Cross-Correlation Service
"""

import pytest
import numpy as np
from app.engine.schemas import FootprintEntity, NormalizedWeatherGrid
from app.engine.aggregation import EventAggregator


@pytest.fixture
def mock_grid():
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


def test_cyclone_multivariable_coupling(mock_grid):
    # Coincident spatial polygon between low pressure and gale wind
    shared_polygon = [[[72.0, 12.0], [75.0, 12.0], [75.0, 15.0], [72.0, 15.0], [72.0, 12.0]]]

    fp_pressure = FootprintEntity(
        cluster_id=1,
        event_id="ANOM-PRES-001",
        name="Deep Cyclonic Depression",
        category="pressure_anomaly",
        hazard_type="Pressure Anomaly",
        severity="High",
        severity_level=3,
        primary_variable="mslp",
        canonical_unit="hPa",
        centroid_lat=13.5,
        centroid_lon=73.5,
        coordinates_display="13.5°N, 73.5°E",
        bounds=[72.0, 12.0, 75.0, 15.0],
        estimated_area_km2=85000.0,
        cell_count=12,
        max_anomaly_score=4.2,
        mean_anomaly_score=3.1,
        peak_metric_value=968.0,
        polygon_coordinates=shared_polygon,
        supporting_metrics={"min_mslp_hpa": 968.0, "pressure_deficit_hpa": 45.2},
        detection_method="Barometric Low Threshold",
    )

    fp_wind = FootprintEntity(
        cluster_id=2,
        event_id="ANOM-WIND-002",
        name="Severe Gale Squall",
        category="wind_anomaly",
        hazard_type="Wind Anomaly",
        severity="High",
        severity_level=3,
        primary_variable="wind_speed",
        canonical_unit="m/s",
        centroid_lat=13.6,
        centroid_lon=73.6,
        coordinates_display="13.6°N, 73.6°E",
        bounds=[72.0, 12.0, 75.0, 15.0],
        estimated_area_km2=78000.0,
        cell_count=10,
        max_anomaly_score=3.8,
        mean_anomaly_score=2.9,
        peak_metric_value=36.0,
        polygon_coordinates=shared_polygon,
        supporting_metrics={"max_wind_ms": 36.0, "max_wind_kmh": 129.6},
        detection_method="Gale Force Threshold",
    )

    events = EventAggregator.aggregate_events([fp_pressure, fp_wind], mock_grid)

    # Both footprints should merge into 1 Tropical Cyclone event
    assert len(events) == 1
    cyc = events[0]
    assert cyc.type == "Cyclone"
    assert cyc.category_key == "cyclone"
    assert "CYC-" in cyc.id
    assert cyc.severity == "High"
    assert cyc.primary_variable == "mslp+wind_speed"
    assert "Vortex Coupling" in cyc.detection_method
    assert cyc.geometry is not None
    assert cyc.geometry["type"] == "Polygon"


def test_independent_single_variable_aggregation(mock_grid):
    # Two spatially separated footprints
    poly_heat = [[[70.0, 10.0], [72.0, 10.0], [72.0, 12.0], [70.0, 12.0], [70.0, 10.0]]]
    poly_cold = [[[78.0, 18.0], [80.0, 18.0], [80.0, 20.0], [78.0, 20.0], [78.0, 18.0]]]

    fp_heat = FootprintEntity(
        cluster_id=1,
        event_id="ANOM-HEAT-001",
        name="Thermal Anomaly",
        category="heat_wave",
        hazard_type="Heat Wave",
        severity="Medium",
        severity_level=2,
        primary_variable="temperature",
        canonical_unit="°C",
        centroid_lat=11.0,
        centroid_lon=71.0,
        coordinates_display="11.0°N, 71.0°E",
        bounds=[70.0, 10.0, 72.0, 12.0],
        estimated_area_km2=45000.0,
        cell_count=6,
        max_anomaly_score=2.8,
        mean_anomaly_score=2.3,
        peak_metric_value=42.5,
        polygon_coordinates=poly_heat,
        supporting_metrics={"max_temp_detected": 42.5},
        detection_method="Physical Threshold",
    )

    fp_cold = FootprintEntity(
        cluster_id=2,
        event_id="ANOM-COLD-002",
        name="Cold Wave Outbreak",
        category="cold_wave",
        hazard_type="Cold Wave",
        severity="High",
        severity_level=3,
        primary_variable="temperature",
        canonical_unit="°C",
        centroid_lat=19.0,
        centroid_lon=79.0,
        coordinates_display="19.0°N, 79.0°E",
        bounds=[78.0, 18.0, 80.0, 20.0],
        estimated_area_km2=52000.0,
        cell_count=8,
        max_anomaly_score=3.6,
        mean_anomaly_score=2.9,
        peak_metric_value=-8.0,
        polygon_coordinates=poly_cold,
        supporting_metrics={"min_temp_detected": -8.0},
        detection_method="Physical Threshold",
    )

    events = EventAggregator.aggregate_events([fp_heat, fp_cold], mock_grid)

    assert len(events) == 2
    categories = {e.category_key for e in events}
    assert "heat_wave" in categories
    assert "cold_wave" in categories

    # Verify stable IDs on repeated calls
    events_recheck = EventAggregator.aggregate_events([fp_heat, fp_cold], mock_grid)
    assert events[0].id == events_recheck[0].id
    assert events[1].id == events_recheck[1].id
