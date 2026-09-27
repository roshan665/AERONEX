"""
Wind Speed Anomaly Detector for Gale, Storm, and High-Shear Winds
"""

from typing import List
import numpy as np
from app.engine.detectors.base import BaseAnomalyDetector
from app.engine.schemas import NormalizedWeatherGrid, DetectionResult


class WindAnomalyDetector(BaseAnomalyDetector):
    def detect(self, grid: NormalizedWeatherGrid) -> List[DetectionResult]:
        if grid.wind_speed_ms is None:
            return []

        wind = grid.wind_speed_ms
        has_clim = grid.wind_clim_mean is not None and grid.wind_clim_std is not None

        if has_clim:
            z_wind = self.compute_zscore(wind, grid.wind_clim_mean, grid.wind_clim_std)
            mask = (wind >= self.thresholds.gale_wind_ms) | (z_wind >= self.thresholds.wind_zscore_threshold)
            score_grid = np.where(np.isnan(z_wind), 0.0, z_wind)
            method = "Hybrid (Gale Threshold & Climatological Z-Score)"
        else:
            mask = wind >= self.thresholds.gale_wind_ms
            score_grid = np.maximum(0.0, wind - self.thresholds.gale_wind_ms)
            method = "Physical Gale-Force Threshold (>= 17.5 m/s)"

        mask = np.where(np.isnan(wind), False, mask)

        if not np.any(mask):
            return []

        max_wind_ms = float(np.nanmax(np.where(mask, wind, np.nan)))
        max_wind_kmh = max_wind_ms * 3.6

        return [
            DetectionResult(
                variable="wind_speed",
                category="wind_anomaly",
                method=method,
                mask=mask,
                score_grid=score_grid,
                threshold_value=self.thresholds.gale_wind_ms,
                canonical_unit="m/s",
                detected_cell_count=int(np.sum(mask)),
                metadata={
                    "gale_threshold_ms": self.thresholds.gale_wind_ms,
                    "storm_threshold_ms": self.thresholds.storm_wind_ms,
                    "hurricane_threshold_ms": self.thresholds.hurricane_wind_ms,
                    "max_wind_ms": max_wind_ms,
                    "max_wind_kmh": round(max_wind_kmh, 1),
                },
            )
        ]
