"""
AeroNex Forecast Uncertainty Service
Phase 6: Ensemble Spread Statistics, Quantile Calculation, and Deterministic Unavailable States
"""

import math
from typing import List, Dict, Any, Optional
import numpy as np

from app.ml.schemas import (
    EnsembleQuantiles,
    LeadTimeUncertaintyPoint,
    ForecastUncertaintySeries,
)
from app.data.demo_data import FORECAST_TIME_SERIES


class ForecastUncertaintyService:
    """
    Computes ensemble dispersion statistics (mean, std, p10-p90 quantiles) when multi-member
    ensemble data is provided, or returns explicit unavailable states with explanatory guidance
    when only deterministic single-member data exists.
    """

    @classmethod
    def calculate_ensemble_statistics(
        cls,
        member_values: List[float],
        missing_member_fraction: float = 0.0,
        unit: str = "°C"
    ) -> Dict[str, Any]:
        """
        Calculates ensemble descriptive statistics across valid numerical member values.
        """
        arr = np.array([v for v in member_values if v is not None and not math.isnan(v)], dtype=np.float64)
        if len(arr) == 0:
            return {
                "mean": 0.0,
                "std": 0.0,
                "quantiles": EnsembleQuantiles(p10=0.0, p25=0.0, p50=0.0, p75=0.0, p90=0.0),
                "member_count": 0,
                "missing_member_fraction": 1.0,
            }

        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
        q10 = float(np.percentile(arr, 10))
        q25 = float(np.percentile(arr, 25))
        q50 = float(np.percentile(arr, 50))
        q75 = float(np.percentile(arr, 75))
        q90 = float(np.percentile(arr, 90))

        return {
            "mean": round(mean_val, 2),
            "std": round(std_val, 2),
            "quantiles": EnsembleQuantiles(
                p10=round(q10, 2),
                p25=round(q25, 2),
                p50=round(q50, 2),
                p75=round(q75, 2),
                p90=round(q90, 2)
            ),
            "member_count": len(arr),
            "missing_member_fraction": round(missing_member_fraction, 3),
        }

    @classmethod
    def get_variable_uncertainty(
        cls,
        variable: str = "temperature",
        mode: str = "ensemble"
    ) -> ForecastUncertaintySeries:
        """
        Retrieves uncertainty profile across lead days for a requested variable.
        If mode == 'deterministic' or genuine ensemble is unavailable, returns explicit
        unavailable status with empty state explanation.
        """
        var_key = variable.lower().strip()
        if var_key not in FORECAST_TIME_SERIES:
            var_key = "temperature"

        meta = FORECAST_TIME_SERIES[var_key]
        var_name = meta["variable_name"]
        unit = meta["unit"]

        # Deterministic Single-Run Mode: Explicitly unavailable
        if mode == "deterministic":
            timeline: List[LeadTimeUncertaintyPoint] = []
            for item in meta["timeline"]:
                timeline.append(
                    LeadTimeUncertaintyPoint(
                        lead_day=item["lead_day"],
                        lead_time_hours=item["lead_time_hours"],
                        valid_time=item["valid_time"],
                        ensemble_mean=item["global_avg"],
                        ensemble_std=0.0,
                        quantiles=EnsembleQuantiles(
                            p10=item["global_avg"],
                            p25=item["global_avg"],
                            p50=item["global_avg"],
                            p75=item["global_avg"],
                            p90=item["global_avg"]
                        ),
                        member_count=1,
                        missing_member_fraction=0.0,
                        unit=unit
                    )
                )

            return ForecastUncertaintySeries(
                variable=var_key,
                variable_name=var_name,
                unit=unit,
                horizon_days=10,
                is_available=False,
                uncertainty_mode="DETERMINISTIC_ONLY",
                member_count=1,
                timeline=timeline,
                caveats=[
                    "Ensemble spread is unavailable: Single-run deterministic forecasts produce an individual trajectory without ensemble variance.",
                    "Predictability inherently decays with forecast lead time; deterministic output does not quantify confidence intervals.",
                    "Do NOT interpret the single deterministic line as a guarantee of forecast outcome.",
                ],
                empty_state_explanation=(
                    f"No multi-member ensemble forecast is configured for {var_name}. "
                    "The active data stream originates from a single deterministic model run. "
                    "Ensemble spread, quantiles, and member dispersion require an operational ensemble dataset "
                    "(e.g., GEFS 31-member or ECMWF EPS 51-member)."
                ),
                data_provenance="NOAA_GFS_DETERMINISTIC_0.25",
                is_simulated=True
            )

        # Demonstration Synthetic Ensemble Mode (5 reproducible perturbed members)
        timeline: List[LeadTimeUncertaintyPoint] = []
        rng = np.random.RandomState(42)

        for item in meta["timeline"]:
            day = item["lead_day"]
            base = item["global_avg"]
            # Error growth increases with lead time
            spread_factor = 0.5 + 0.35 * (day - 1)
            
            # Generate 5 perturbed synthetic members
            members = [
                base - 1.2 * spread_factor,
                base - 0.4 * spread_factor,
                base + 0.1 * spread_factor,
                base + 0.6 * spread_factor,
                base + 1.4 * spread_factor,
            ]
            # Day 5+ has 1 member drop out to demonstrate missing-member handling
            missing_fraction = 0.2 if day >= 6 else 0.0
            if missing_fraction > 0:
                members = members[:4]

            stats = cls.calculate_ensemble_statistics(members, missing_member_fraction=missing_fraction, unit=unit)

            timeline.append(
                LeadTimeUncertaintyPoint(
                    lead_day=day,
                    lead_time_hours=item["lead_time_hours"],
                    valid_time=item["valid_time"],
                    ensemble_mean=stats["mean"],
                    ensemble_std=stats["std"],
                    quantiles=stats["quantiles"],
                    member_count=stats["member_count"],
                    missing_member_fraction=stats["missing_member_fraction"],
                    unit=unit
                )
            )

        return ForecastUncertaintySeries(
            variable=var_key,
            variable_name=var_name,
            unit=unit,
            horizon_days=10,
            is_available=True,
            uncertainty_mode="ENSEMBLE_MEMBERS",
            member_count=5,
            timeline=timeline,
            caveats=[
                "SYNTHETIC DEMO ONLY: Generated across 5 reproducible perturbed pseudo-ensemble members.",
                "Ensemble spread reflects intra-member dispersion, NOT verified forecast error.",
                "Small ensemble size (5 members) underestimates the true probability distribution tail compared to 31-51 member operational ensembles.",
            ],
            empty_state_explanation=None,
            data_provenance="SYNTHETIC_ENSEMBLE_DEMO",
            is_simulated=True
        )
