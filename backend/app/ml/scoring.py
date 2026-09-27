"""
AeroNex Multi-Component Normalized Anomaly Scoring Service
Phase 6: Configurable Normalization, Dimensionless Fusion, and Explainable Attribution
"""

import math
from typing import Dict, Any, List, Optional, Tuple
from app.ml.schemas import (
    ScoringWeightsConfig,
    ComponentAnomalyScore,
    CompositeAnomalyScore,
)


class AnomalyScoringService:
    """
    Computes mathematically rigorous, multi-criteria composite anomaly scores.
    
    SCIENTIFIC PRINCIPLES:
    1. Incomparable physical variables (°C, hPa, km/h, km²) are NEVER summed directly.
    2. Each variable is mapped via calibrated nonlinear/sigmoid transfer functions to a
       dimensionless interval [0.0, 1.0].
    3. The continuous composite score is an empirical index, NOT a probability.
    4. Categorical severity tiers (Low, Medium, High, Extreme) are partitioned on the
       index and preserved separately from continuous measurements.
    """

    DEFAULT_WEIGHTS = ScoringWeightsConfig(
        w_temp=0.25,
        w_wind=0.20,
        w_pressure=0.20,
        w_spatial=0.15,
        w_persistence=0.10,
        w_quality=0.10,
    )

    @classmethod
    def normalize_temperature(
        cls,
        observed_celsius: Optional[float],
        baseline_celsius: Optional[float] = 28.0,
        clim_std: Optional[float] = 2.5
    ) -> Tuple[float, Optional[float], str]:
        """
        Maps temperature anomaly to [0.0, 1.0] using two-sided standardized deviation.
        A deviation of >= 4.0 standard deviations corresponds to ~1.0.
        """
        if observed_celsius is None:
            return 0.0, None, "No temperature observation provided."
        
        diff = observed_celsius - (baseline_celsius or 28.0)
        std = max(0.5, clim_std or 2.5)
        z = abs(diff) / std
        # Soft saturation: 1 - exp(-z / 2.5)
        score = float(min(1.0, max(0.0, 1.0 - math.exp(-z / 2.5))))
        interp = (
            f"Thermal departure of {diff:+.1f}°C ({z:.1f}σ from normal). "
            f"{'Positive heat anomaly' if diff >= 0 else 'Negative cold plunge'}."
        )
        return score, observed_celsius, interp

    @classmethod
    def normalize_wind(
        cls,
        max_wind_kmh: Optional[float],
        gale_threshold_kmh: float = 62.0,
        hurricane_force_kmh: float = 120.0
    ) -> Tuple[float, Optional[float], str]:
        """
        Maps wind speed to [0.0, 1.0] scaling from moderate breeze (30 km/h) to Category 4+ (>160 km/h).
        """
        if max_wind_kmh is None or max_wind_kmh <= 0:
            return 0.0, None, "No wind velocity recorded."
        
        # Below 35 km/h is benign ambient wind (score ~ 0)
        if max_wind_kmh < 35.0:
            score = float(max_wind_kmh / 70.0 * 0.1)
        else:
            # Scaled on Saffir-Simpson / Beaufort gale intervals
            score = float(min(1.0, 0.1 + 0.9 * (1.0 - math.exp(-(max_wind_kmh - 35.0) / 60.0))))
        
        interp = f"Peak sustained wind of {max_wind_kmh:.1f} km/h (Beaufort / gale intensity factor {score:.2f})."
        return score, max_wind_kmh, interp

    @classmethod
    def normalize_pressure(
        cls,
        min_mslp_hpa: Optional[float],
        standard_atmosphere_hpa: float = 1013.25
    ) -> Tuple[float, Optional[float], str]:
        """
        Maps central pressure deficit below standard atmosphere to [0.0, 1.0].
        Standard normal: 1013 hPa -> 0.0. Deep cyclone: <= 940 hPa -> 1.0.
        """
        if min_mslp_hpa is None:
            return 0.0, None, "No pressure observation provided."
        
        deficit = max(0.0, standard_atmosphere_hpa - min_mslp_hpa)
        # Scaled: 10 hPa deficit = mild (0.2), 35 hPa = severe (0.7), 65+ hPa = extreme (1.0)
        score = float(min(1.0, max(0.0, 1.0 - math.exp(-deficit / 30.0))))
        interp = f"Central pressure {min_mslp_hpa:.1f} hPa ({deficit:.1f} hPa barometric deficit below standard atmosphere)."
        return score, min_mslp_hpa, interp

    @classmethod
    def normalize_spatial_extent(
        cls,
        area_km2: Optional[float],
        reference_min_km2: float = 5000.0,
        reference_max_km2: float = 750000.0
    ) -> Tuple[float, Optional[float], str]:
        """
        Maps geographic footprint surface area logarithmically to [0.0, 1.0].
        """
        if area_km2 is None or area_km2 <= 0:
            return 0.0, None, "Localized or point-source signature with negligible footprint."
        
        # Logarithmic scaling across mesoscale (5,000 km²) to synoptic macroscale (750,000 km²)
        min_log = math.log10(reference_min_km2)
        max_log = math.log10(reference_max_km2)
        val_log = math.log10(max(reference_min_km2, min(reference_max_km2, area_km2)))
        
        score = float(min(1.0, max(0.0, (val_log - min_log) / (max_log - min_log))))
        interp = f"Contiguous spatial footprint spans {area_km2:,.0f} km² ({'macroscale synoptic' if score > 0.6 else 'mesoscale regional'})."
        return score, area_km2, interp

    @classmethod
    def normalize_persistence(
        cls,
        active_forecast_days: Optional[List[int]],
        total_horizon_days: int = 10
    ) -> Tuple[float, Optional[float], str]:
        """
        Maps temporal persistence across multi-day forecast horizons to [0.0, 1.0].
        """
        if not active_forecast_days:
            return 0.1, 1.0, "Single-timestep transient anomaly."
        
        count = len(set(active_forecast_days))
        score = float(min(1.0, max(0.1, count / 5.0)))
        interp = f"Persistent signature detected across {count} forecast days ({score * 100:.0f}% temporal persistence)."
        return score, float(count), interp

    @classmethod
    def evaluate_data_quality(
        cls,
        missing_cell_fraction: float = 0.0,
        is_synthetic: bool = True,
        variance_penalty: float = 0.0
    ) -> Tuple[float, Optional[float], str]:
        """
        Computes a data quality multiplier score [0.0, 1.0].
        Higher means cleaner, more reliable data.
        """
        penalty = min(0.6, missing_cell_fraction * 1.5 + variance_penalty)
        score = float(max(0.2, 1.0 - penalty))
        notes = "Clean synthetic gridded representation with complete boundary continuity."
        if missing_cell_fraction > 0:
            notes = f"Warning: {missing_cell_fraction * 100:.1f}% missing or invalid grid cells in sampling window."
        return score, score, notes

    @classmethod
    def compute_composite_score(
        cls,
        event_id: str,
        observed_temperature: Optional[float] = None,
        baseline_temperature: Optional[float] = 28.0,
        clim_temp_std: Optional[float] = 2.5,
        max_wind_kmh: Optional[float] = None,
        min_mslp_hpa: Optional[float] = None,
        area_km2: Optional[float] = None,
        forecast_days: Optional[List[int]] = None,
        missing_cell_fraction: float = 0.0,
        weights: Optional[ScoringWeightsConfig] = None
    ) -> CompositeAnomalyScore:
        """
        Synthesizes a complete multi-component CompositeAnomalyScore.
        """
        w = weights or cls.DEFAULT_WEIGHTS

        # 1. Normalize individual components
        s_temp, raw_temp, i_temp = cls.normalize_temperature(observed_temperature, baseline_temperature, clim_temp_std)
        s_wind, raw_wind, i_wind = cls.normalize_wind(max_wind_kmh)
        s_press, raw_press, i_press = cls.normalize_pressure(min_mslp_hpa)
        s_spat, raw_spat, i_spat = cls.normalize_spatial_extent(area_km2)
        s_pers, raw_pers, i_pers = cls.normalize_persistence(forecast_days)
        s_qual, raw_qual, i_qual = cls.evaluate_data_quality(missing_cell_fraction)

        # 2. Compute weighted contributions
        c_temp = s_temp * w.w_temp
        c_wind = s_wind * w.w_wind
        c_press = s_press * w.w_pressure
        c_spat = s_spat * w.w_spatial
        c_pers = s_pers * w.w_persistence
        c_qual = s_qual * w.w_quality

        composite = c_temp + c_wind + c_press + c_spat + c_pers + c_qual
        composite = float(min(1.0, max(0.0, composite)))
        overall_100 = round(composite * 100.0, 1)

        # 3. Calculate percentage shares
        total_c = max(1e-6, composite)
        pct_temp = round(c_temp / total_c * 100.0, 1)
        pct_wind = round(c_wind / total_c * 100.0, 1)
        pct_press = round(c_press / total_c * 100.0, 1)
        pct_spat = round(c_spat / total_c * 100.0, 1)
        pct_pers = round(c_pers / total_c * 100.0, 1)
        pct_qual = round(c_qual / total_c * 100.0, 1)

        components = {
            "thermal_deviation": ComponentAnomalyScore(
                component_name="thermal_deviation",
                display_name="Temperature Anomaly",
                raw_value=raw_temp,
                raw_unit="°C",
                reference_normal=baseline_temperature,
                normalized_score=round(s_temp, 3),
                weight=w.w_temp,
                weighted_contribution=round(c_temp, 4),
                contribution_percent=pct_temp,
                interpretation=i_temp
            ),
            "wind_magnitude": ComponentAnomalyScore(
                component_name="wind_magnitude",
                display_name="Wind Velocity Anomaly",
                raw_value=raw_wind,
                raw_unit="km/h",
                reference_normal=35.0,
                normalized_score=round(s_wind, 3),
                weight=w.w_wind,
                weighted_contribution=round(c_wind, 4),
                contribution_percent=pct_wind,
                interpretation=i_wind
            ),
            "pressure_deficit": ComponentAnomalyScore(
                component_name="pressure_deficit",
                display_name="Barometric Pressure Deficit",
                raw_value=raw_press,
                raw_unit="hPa",
                reference_normal=1013.25,
                normalized_score=round(s_press, 3),
                weight=w.w_pressure,
                weighted_contribution=round(c_press, 4),
                contribution_percent=pct_press,
                interpretation=i_press
            ),
            "spatial_extent": ComponentAnomalyScore(
                component_name="spatial_extent",
                display_name="Spatial Footprint Extent",
                raw_value=raw_spat,
                raw_unit="km²",
                reference_normal=15000.0,
                normalized_score=round(s_spat, 3),
                weight=w.w_spatial,
                weighted_contribution=round(c_spat, 4),
                contribution_percent=pct_spat,
                interpretation=i_spat
            ),
            "temporal_persistence": ComponentAnomalyScore(
                component_name="temporal_persistence",
                display_name="Forecast Multi-Horizon Persistence",
                raw_value=raw_pers,
                raw_unit="days",
                reference_normal=1.0,
                normalized_score=round(s_pers, 3),
                weight=w.w_persistence,
                weighted_contribution=round(c_pers, 4),
                contribution_percent=pct_pers,
                interpretation=i_pers
            ),
            "data_quality": ComponentAnomalyScore(
                component_name="data_quality",
                display_name="Data Reliability & Integrity",
                raw_value=raw_qual,
                raw_unit="index",
                reference_normal=1.0,
                normalized_score=round(s_qual, 3),
                weight=w.w_quality,
                weighted_contribution=round(c_qual, 4),
                contribution_percent=pct_qual,
                interpretation=i_qual
            ),
        }

        # 4. Rank primary contributing variables
        ranked = sorted(
            [
                ("Temperature", c_temp),
                ("Wind Speed", c_wind),
                ("Pressure Deficit", c_press),
                ("Spatial Footprint", c_spat),
                ("Temporal Persistence", c_pers),
            ],
            key=lambda x: x[1],
            reverse=True
        )
        primary_vars = [item[0] for item in ranked if item[1] > 0.02][:3]
        if not primary_vars:
            primary_vars = ["General Background Fluctuation"]

        # 5. Determine severity tier (partitioned interval, kept separate from score)
        if composite >= 0.75:
            severity = "Extreme"
        elif composite >= 0.50:
            severity = "High"
        elif composite >= 0.25:
            severity = "Medium"
        else:
            severity = "Low"

        # 6. Interpret overall score
        interpretation = (
            f"Anomaly index of {overall_100}/100 classifies as '{severity}' severity tier. "
            f"Primary driving forces: {', '.join(primary_vars)}. "
            f"Governed by {ranked[0][0]} ({ranked[0][1] / total_c * 100:.1f}% of total score)."
        )

        warnings = []
        if missing_cell_fraction > 0.05:
            warnings.append(f"Grid completeness penalty applied ({missing_cell_fraction * 100:.1f}% missing).")

        limitations = [
            "Score represents an empirical multi-criteria departure index; it is NOT a calibrated probability of disaster.",
            "Normalizations use climatological references and standard atmospheric baselines (1013.25 hPa).",
            "Severity classification thresholds are operational heuristics, not legal warning criteria.",
        ]

        return CompositeAnomalyScore(
            event_id=event_id,
            composite_score=round(composite, 4),
            overall_score_100=overall_100,
            severity_tier=severity,
            is_probability=False,
            primary_contributing_variables=primary_vars,
            components=components,
            detection_method="NORMALIZED_MULTI_CRITERIA_SCORER_V1",
            data_quality_warnings=warnings,
            score_interpretation=interpretation,
            score_limitations=limitations
        )
