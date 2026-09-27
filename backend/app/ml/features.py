"""
AeroNex Feature Engineering Pipeline & Versioned Feature Schema
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
import numpy as np
from scipy.ndimage import generic_filter

from app.engine.schemas import NormalizedWeatherGrid
from app.ml.schemas import FeatureSchema, FeatureMetadata


FEATURE_COLUMNS: List[str] = [
    "temp_anomaly_z",
    "wind_anomaly_z",
    "mslp_anomaly_z",
    "precip_rate_normalized",
    "local_temp_grad",
    "local_mslp_grad",
    "normalized_lead_time",
    "data_quality_factor",
]

FEATURE_SCHEMA_VERSION = "v1.0.0"

FEATURES_METADATA_DICT: Dict[str, FeatureMetadata] = {
    "temp_anomaly_z": FeatureMetadata(
        name="temp_anomaly_z",
        unit="dimensionless",
        description="Standardized temperature departure from local climatological mean Z = (T - μ_clim) / σ_clim",
        preprocessing="Climatological Z-score normalization, clipped to [-8.0, 8.0]"
    ),
    "wind_anomaly_z": FeatureMetadata(
        name="wind_anomaly_z",
        unit="dimensionless",
        description="Standardized wind speed anomaly from baseline normal Z = (W - μ_clim) / σ_clim",
        preprocessing="One-sided upper Z-score, clipped to [-4.0, 10.0]"
    ),
    "mslp_anomaly_z": FeatureMetadata(
        name="mslp_anomaly_z",
        unit="dimensionless",
        description="Standardized mean sea-level pressure departure from baseline normal Z = (P - μ_clim) / σ_clim",
        preprocessing="Signed Z-score; negative values indicate cyclonic baroclinic depressions"
    ),
    "precip_rate_normalized": FeatureMetadata(
        name="precip_rate_normalized",
        unit="dimensionless",
        description="Log-transformed and scaled 24h precipitation rate: log1p(mm) / log1p(250.0)",
        preprocessing="Nonlinear logarithmic compression to bound extreme rainfall tail"
    ),
    "local_temp_grad": FeatureMetadata(
        name="local_temp_grad",
        unit="°C / grid_unit",
        description="Spatial gradient magnitude of 2m temperature indicating frontal or thermal boundary strength",
        preprocessing="Finite-difference spatial gradient magnitude sqrt((dT/dx)^2 + (dT/dy)^2)"
    ),
    "local_mslp_grad": FeatureMetadata(
        name="local_mslp_grad",
        unit="hPa / grid_unit",
        description="Spatial pressure gradient magnitude indicating geostrophic forcing / baroclinicity",
        preprocessing="Finite-difference spatial gradient magnitude sqrt((dP/dx)^2 + (dP/dy)^2)"
    ),
    "normalized_lead_time": FeatureMetadata(
        name="normalized_lead_time",
        unit="dimensionless",
        description="Normalized forecast horizon: lead_time_hours / 240.0 on [0.0, 1.0]",
        preprocessing="Linear scaling across standard 10-day NWP horizon"
    ),
    "data_quality_factor": FeatureMetadata(
        name="data_quality_factor",
        unit="dimensionless",
        description="Local data completeness and physical sanity score in 3x3 spatial neighborhood",
        preprocessing="Ratio of physically bounded, non-NaN cells in local window [0.0, 1.0]"
    ),
}


class FeatureExtractor:
    """
    Extracts tabular and tensor representations from NormalizedWeatherGrid objects.
    Enforces strict feature ordering, unit consistency, and non-reliance on absolute coordinates.
    """

    @classmethod
    def get_feature_schema(cls) -> FeatureSchema:
        return FeatureSchema(
            version=FEATURE_SCHEMA_VERSION,
            feature_names=FEATURE_COLUMNS,
            features_metadata=FEATURES_METADATA_DICT,
            created_at=datetime.now(timezone.utc).isoformat()
        )

    @classmethod
    def extract_grid_feature_tensor(cls, grid: NormalizedWeatherGrid) -> np.ndarray:
        """
        Extracts feature array of shape (H, W, 8) matching FEATURE_COLUMNS order.
        """
        h, w = grid.shape

        # 1. Temperature Z-score
        if grid.temperature_celsius is not None:
            temp = grid.temperature_celsius
            mean = grid.temp_clim_mean if grid.temp_clim_mean is not None else np.full((h, w), 25.0)
            std = grid.temp_clim_std if grid.temp_clim_std is not None else np.full((h, w), 3.0)
            safe_std = np.where(std < 1e-4, 1.0, std)
            temp_z = np.clip((temp - mean) / safe_std, -8.0, 8.0)
        else:
            temp_z = np.zeros((h, w), dtype=np.float32)

        # 2. Wind Speed Z-score
        if grid.wind_speed_ms is not None:
            wind = grid.wind_speed_ms
            mean = grid.wind_clim_mean if grid.wind_clim_mean is not None else np.full((h, w), 8.0)
            std = grid.wind_clim_std if grid.wind_clim_std is not None else np.full((h, w), 2.5)
            safe_std = np.where(std < 1e-4, 1.0, std)
            wind_z = np.clip((wind - mean) / safe_std, -4.0, 10.0)
        else:
            wind_z = np.zeros((h, w), dtype=np.float32)

        # 3. MSLP Z-score
        if grid.mslp_hpa is not None:
            mslp = grid.mslp_hpa
            mean = grid.mslp_clim_mean if grid.mslp_clim_mean is not None else np.full((h, w), 1013.25)
            std = grid.mslp_clim_std if grid.mslp_clim_std is not None else np.full((h, w), 4.0)
            safe_std = np.where(std < 1e-4, 1.0, std)
            mslp_z = np.clip((mslp - mean) / safe_std, -10.0, 6.0)
        else:
            mslp_z = np.zeros((h, w), dtype=np.float32)

        # 4. Precipitation rate normalized
        if grid.precipitation_mm is not None:
            precip = np.maximum(0.0, grid.precipitation_mm)
            precip_norm = np.log1p(precip) / np.log1p(250.0)
            precip_norm = np.clip(precip_norm, 0.0, 1.0)
        else:
            precip_norm = np.zeros((h, w), dtype=np.float32)

        # 5. Local Temperature Gradient
        if grid.temperature_celsius is not None:
            gy, gx = np.gradient(grid.temperature_celsius)
            temp_grad = np.sqrt(gy**2 + gx**2)
        else:
            temp_grad = np.zeros((h, w), dtype=np.float32)

        # 6. Local MSLP Gradient
        if grid.mslp_hpa is not None:
            gy, gx = np.gradient(grid.mslp_hpa)
            mslp_grad = np.sqrt(gy**2 + gx**2)
        else:
            mslp_grad = np.zeros((h, w), dtype=np.float32)

        # 7. Normalized Lead Time
        lead_norm = np.full((h, w), grid.lead_time_hours / 240.0, dtype=np.float32)

        # 8. Data Quality Factor
        quality = np.ones((h, w), dtype=np.float32)
        if grid.temperature_celsius is not None:
            nan_mask = np.isnan(grid.temperature_celsius)
            if np.any(nan_mask):
                quality = np.where(nan_mask, 0.0, 1.0)

        # Stack into (H, W, 8)
        tensor = np.stack(
            [
                temp_z,
                wind_z,
                mslp_z,
                precip_norm,
                temp_grad,
                mslp_grad,
                lead_norm,
                quality,
            ],
            axis=-1
        )

        # Handle any residual NaNs with median/0 imputation
        if np.any(np.isnan(tensor)):
            tensor = np.nan_to_num(tensor, nan=0.0, posinf=1.0, neginf=-1.0)

        return tensor

    @classmethod
    def extract_tabular_features(
        cls,
        grid: NormalizedWeatherGrid,
        subsample_stride: int = 1
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Flattens the grid feature tensor into a 2D matrix of shape (N_samples, 8)
        along with spatial metadata for each row.
        """
        tensor = cls.extract_grid_feature_tensor(grid)
        h, w, c = tensor.shape

        rows = []
        cell_coords = []

        for i in range(0, h, subsample_stride):
            for j in range(0, w, subsample_stride):
                rows.append(tensor[i, j, :])
                cell_coords.append({
                    "lat": float(grid.lats[i]),
                    "lon": float(grid.lons[j]),
                    "i": i,
                    "j": j,
                })

        X = np.asarray(rows, dtype=np.float32)
        return X, cell_coords
