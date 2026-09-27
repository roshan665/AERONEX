"""
Barometric Pressure Anomaly Detector for Cyclonic Depressions and Lows
"""

from typing import List
import numpy as np
from app.engine.detectors.base import BaseAnomalyDetector
from app.engine.schemas import NormalizedWeatherGrid, DetectionResult


class PressureAnomalyDetector(BaseAnomalyDetector):
    def detect(self, grid: NormalizedWeatherGrid) -> List[DetectionResult]:
        if grid.mslp_hpa is None:
            return []

        p = grid.mslp_hpa
        has_clim = grid.mslp_clim_mean is not None and grid.mslp_clim_std is not None

        if has_clim:
            z_p = self.compute_zscore(p, grid.mslp_clim_mean, grid.mslp_clim_std)
            # Negative Z-score indicates anomalous low pressure deficit
            mask = (p <= self.thresholds.low_pressure_hpa) | (z_p <= self.thresholds.pressure_zscore_threshold)
            score_grid = np.where(np.isnan(z_p), 0.0, -z_p)
            method = "Hybrid (Barometric Threshold & Negative Z-Score)"
        else:
            mask = p <= self.thresholds.low_pressure_hpa
            score_grid = np.maximum(0.0, self.thresholds.low_pressure_hpa - p)
            method = "Physical Barometric Low Threshold (<= 998 hPa)"

        mask = np.where(np.isnan(p), False, mask)

        if not np.any(mask):
            return []

        min_mslp = float(np.nanmin(np.where(mask, p, np.nan)))

        return [
            DetectionResult(
                variable="mslp",
                category="pressure_anomaly",
                method=method,
                mask=mask,
                score_grid=score_grid,
                threshold_value=self.thresholds.low_pressure_hpa,
                canonical_unit="hPa",
                detected_cell_count=int(np.sum(mask)),
                metadata={
                    "low_threshold_hpa": self.thresholds.low_pressure_hpa,
                    "deep_threshold_hpa": self.thresholds.deep_depression_hpa,
                    "cyclonic_core_hpa": self.thresholds.cyclonic_core_hpa,
                    "min_mslp_hpa": min_mslp,
                    "pressure_deficit_hpa": round(1013.25 - min_mslp, 1),
                },
            )
        ]
