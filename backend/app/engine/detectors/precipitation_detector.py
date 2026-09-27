"""
Precipitation Anomaly Detector for Heavy and Extreme Rainfall
"""

from typing import List, Optional
import numpy as np
from app.engine.detectors.base import BaseAnomalyDetector
from app.engine.schemas import NormalizedWeatherGrid, DetectionResult


class PrecipitationAnomalyDetector(BaseAnomalyDetector):
    def detect(self, grid: NormalizedWeatherGrid) -> List[DetectionResult]:
        if grid.precipitation_mm is None:
            return []

        tp = grid.precipitation_mm
        accumulation_hours = getattr(grid, "precipitation_accumulation_hours", 24) or 24

        # Validate accumulation period
        acc_valid = isinstance(accumulation_hours, (int, float)) and accumulation_hours > 0
        if not acc_valid:
            accumulation_hours = 24  # Standard meteorological 24h accumulation period fallback

        # Adjust thresholds based on accumulation period if non-standard (e.g. 6h vs 24h)
        # Standard IMD/WMO 24h thresholds: Heavy >= 64.5mm, Very Heavy >= 115.5mm, Extreme >= 204.5mm
        scale_factor = (accumulation_hours / 24.0) ** 0.5  # Sub-linear duration scaling
        heavy_thresh = self.thresholds.heavy_rain_mm * scale_factor
        very_heavy_thresh = self.thresholds.very_heavy_rain_mm * scale_factor
        extreme_thresh = self.thresholds.extreme_rain_mm * scale_factor

        # Check climatology baseline
        has_clim = (
            getattr(grid, "precip_clim_mean", None) is not None
            and getattr(grid, "precip_clim_std", None) is not None
        )

        if has_clim:
            z_precip = self.compute_zscore(tp, grid.precip_clim_mean, grid.precip_clim_std)
            mask = (tp >= heavy_thresh) | (z_precip >= self.thresholds.precip_zscore_threshold)
            score_grid = np.where(np.isnan(z_precip), 0.0, z_precip)
            method = f"Hybrid (Rainfall Threshold >= {heavy_thresh:.1f}mm & Climatological Z-Score)"
        else:
            mask = tp >= heavy_thresh
            score_grid = np.maximum(0.0, (tp - heavy_thresh) / 50.0)
            method = f"Configurable Physical Rainfall Threshold (>={heavy_thresh:.1f} mm / {accumulation_hours}h)"

        mask = np.where(np.isnan(tp), False, mask)

        if not np.any(mask):
            return []

        max_tp = float(np.nanmax(np.where(mask, tp, np.nan)))

        return [
            DetectionResult(
                variable="precipitation",
                category="precipitation_anomaly",
                method=method,
                mask=mask,
                score_grid=score_grid,
                threshold_value=heavy_thresh,
                canonical_unit="mm",
                detected_cell_count=int(np.sum(mask)),
                metadata={
                    "accumulation_period_hours": accumulation_hours,
                    "heavy_threshold_mm": round(heavy_thresh, 1),
                    "very_heavy_threshold_mm": round(very_heavy_thresh, 1),
                    "extreme_threshold_mm": round(extreme_thresh, 1),
                    "max_precip_mm": round(max_tp, 1),
                },
            )
        ]
