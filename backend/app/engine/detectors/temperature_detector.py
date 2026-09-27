"""
Temperature Anomaly Detector for Heat Domes and Cold Waves
"""

from typing import List
import numpy as np
from app.engine.detectors.base import BaseAnomalyDetector
from app.engine.schemas import NormalizedWeatherGrid, DetectionResult


class TemperatureAnomalyDetector(BaseAnomalyDetector):
    def detect(self, grid: NormalizedWeatherGrid) -> List[DetectionResult]:
        if grid.temperature_celsius is None:
            return []

        temp = grid.temperature_celsius
        results = []

        has_clim = grid.temp_clim_mean is not None and grid.temp_clim_std is not None

        # 1. Extreme Heat Anomaly / Heat Dome Detection
        if has_clim:
            z_heat = self.compute_zscore(temp, grid.temp_clim_mean, grid.temp_clim_std)
            heat_mask = (temp >= self.thresholds.extreme_heat_celsius) | (z_heat >= self.thresholds.temp_zscore_threshold)
            score_heat = np.where(np.isnan(z_heat), 0.0, z_heat)
            method = "Hybrid (Absolute Threshold & Climatological Z-Score)"
        else:
            heat_mask = temp >= self.thresholds.extreme_heat_celsius
            score_heat = np.maximum(0.0, temp - self.thresholds.extreme_heat_celsius)
            method = "Configurable Physical Absolute Threshold"

        # Suppress NaNs in mask
        heat_mask = np.where(np.isnan(temp), False, heat_mask)

        if np.any(heat_mask):
            results.append(
                DetectionResult(
                    variable="temperature",
                    category="heat_wave",
                    method=method,
                    mask=heat_mask,
                    score_grid=score_heat,
                    threshold_value=self.thresholds.extreme_heat_celsius,
                    canonical_unit="°C",
                    detected_cell_count=int(np.sum(heat_mask)),
                    metadata={
                        "extreme_threshold_celsius": self.thresholds.extreme_heat_celsius,
                        "severe_threshold_celsius": self.thresholds.severe_heat_celsius,
                        "max_temp_detected": float(np.nanmax(np.where(heat_mask, temp, np.nan))),
                    },
                )
            )

        # 2. Cold Wave / Severe Freezing Outbreak Detection
        if has_clim:
            z_cold = self.compute_zscore(temp, grid.temp_clim_mean, grid.temp_clim_std)
            cold_mask = (temp <= self.thresholds.severe_cold_celsius) | (
                (temp <= self.thresholds.extreme_cold_celsius) & (z_cold <= -self.thresholds.temp_zscore_threshold)
            )
            score_cold = np.where(np.isnan(z_cold), 0.0, -z_cold)
            method = "Hybrid (Absolute Threshold & Climatological Z-Score)"
        else:
            cold_mask = temp <= self.thresholds.extreme_cold_celsius
            score_cold = np.maximum(0.0, self.thresholds.extreme_cold_celsius - temp)
            method = "Configurable Physical Absolute Threshold"

        cold_mask = np.where(np.isnan(temp), False, cold_mask)

        if np.any(cold_mask):
            results.append(
                DetectionResult(
                    variable="temperature",
                    category="cold_wave",
                    method=method,
                    mask=cold_mask,
                    score_grid=score_cold,
                    threshold_value=self.thresholds.extreme_cold_celsius,
                    canonical_unit="°C",
                    detected_cell_count=int(np.sum(cold_mask)),
                    metadata={
                        "extreme_threshold_celsius": self.thresholds.extreme_cold_celsius,
                        "severe_threshold_celsius": self.thresholds.severe_cold_celsius,
                        "min_temp_detected": float(np.nanmin(np.where(cold_mask, temp, np.nan))),
                    },
                )
            )

        return results
