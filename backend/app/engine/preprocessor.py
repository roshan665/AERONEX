"""
Preprocessing Service for Meteorological Grids & Coordinate Normalization
"""

from typing import List, Tuple
import numpy as np
from app.engine.schemas import WeatherGridDataset, NormalizedWeatherGrid


class GridPreprocessor:
    """
    Validates, normalizes, and converts raw weather arrays into standardized canonical units.
    """

    @classmethod
    def preprocess(cls, dataset: WeatherGridDataset) -> NormalizedWeatherGrid:
        warnings: List[str] = []

        # 1. Coordinate Validation
        lats = np.asarray(dataset.lats, dtype=np.float64)
        lons = np.asarray(dataset.lons, dtype=np.float64)

        if lats.ndim != 1 or lons.ndim != 1:
            raise ValueError(f"Coordinates must be 1D arrays. Got lats.ndim={lats.ndim}, lons.ndim={lons.ndim}")

        if len(lats) < 2 or len(lons) < 2:
            raise ValueError(f"Grid must contain at least 2 latitude and longitude points. Got {len(lats)} x {len(lons)}")

        if np.any(lats < -90.0) or np.any(lats > 90.0):
            raise ValueError(f"Latitude values out of permissible range [-90.0, 90.0]: min={lats.min()}, max={lats.max()}")

        # Longitude Normalization: wrap from [0, 360) to [-180, 180] if necessary
        if np.any(lons > 180.0):
            lons = (lons + 180.0) % 360.0 - 180.0
            warnings.append("Normalized longitudes from [0, 360) to [-180, 180] domain.")

        # Ensure sorted coordinates for predictable spatial indexing
        if not np.all(np.diff(lats) > 0) and not np.all(np.diff(lats) < 0):
            warnings.append("Latitude array is not strictly monotonic.")

        expected_shape: Tuple[int, int] = (len(lats), len(lons))

        # 2. Variable Array Shape Verification & Canonical Unit Conversion
        temp_celsius = None
        wind_ms = None
        mslp_hpa = None
        precip_mm = None

        # --- Temperature Conversion ---
        if "temperature" in dataset.variables or "t2m" in dataset.variables:
            raw_temp = np.asarray(dataset.variables.get("temperature", dataset.variables.get("t2m")), dtype=np.float64)
            cls._validate_shape(raw_temp, expected_shape, "temperature")
            raw_temp = cls._clean_non_finite(raw_temp, warnings, "temperature")
            
            unit = dataset.units.get("temperature", dataset.units.get("t2m", "")).lower()
            if unit in ["k", "kelvin"]:
                temp_celsius = raw_temp - 273.15
            elif unit in ["c", "celsius", "°c"]:
                temp_celsius = raw_temp
            elif np.nanmean(raw_temp) > 150.0:
                # Heuristic: Atmospheric temps in Celsius are never > 150°C
                temp_celsius = raw_temp - 273.15
                warnings.append("Assumed Kelvin units for temperature based on magnitude (mean > 150).")
            else:
                temp_celsius = raw_temp
                warnings.append("Assumed Celsius units for temperature.")

        # --- Wind Speed Conversion ---
        if "wind_speed" in dataset.variables or "ws10" in dataset.variables:
            raw_wind = np.asarray(dataset.variables.get("wind_speed", dataset.variables.get("ws10")), dtype=np.float64)
            cls._validate_shape(raw_wind, expected_shape, "wind_speed")
            raw_wind = cls._clean_non_finite(raw_wind, warnings, "wind_speed")

            unit = dataset.units.get("wind_speed", dataset.units.get("ws10", "")).lower()
            if unit in ["m/s", "mps", "meter/second", "meters/second"]:
                wind_ms = raw_wind
            elif unit in ["km/h", "kmh"]:
                wind_ms = raw_wind / 3.6
            elif unit in ["knots", "kt"]:
                wind_ms = raw_wind * 0.514444
            else:
                wind_ms = raw_wind
                warnings.append(f"Unrecognized wind speed unit '{unit}'. Assumed m/s.")
        elif "u10" in dataset.variables and "v10" in dataset.variables:
            # Derive scalar magnitude from orthogonal components
            u10 = np.asarray(dataset.variables["u10"], dtype=np.float64)
            v10 = np.asarray(dataset.variables["v10"], dtype=np.float64)
            cls._validate_shape(u10, expected_shape, "u10")
            cls._validate_shape(v10, expected_shape, "v10")
            u10 = cls._clean_non_finite(u10, warnings, "u10")
            v10 = cls._clean_non_finite(v10, warnings, "v10")
            wind_ms = np.sqrt(u10**2 + v10**2)
            warnings.append("Derived scalar wind speed from u10 and v10 orthogonal components.")

        # --- Pressure Conversion ---
        if "mslp" in dataset.variables or "pressure" in dataset.variables or "prmsl" in dataset.variables:
            raw_p = np.asarray(dataset.variables.get("mslp", dataset.variables.get("pressure", dataset.variables.get("prmsl"))), dtype=np.float64)
            cls._validate_shape(raw_p, expected_shape, "mslp")
            raw_p = cls._clean_non_finite(raw_p, warnings, "mslp")

            unit = dataset.units.get("mslp", dataset.units.get("pressure", dataset.units.get("prmsl", ""))).lower()
            if unit in ["pa", "pascal"]:
                mslp_hpa = raw_p / 100.0
            elif unit in ["hpa", "hectopascal", "mbar", "mb"]:
                mslp_hpa = raw_p
            elif np.nanmean(raw_p) > 2000.0:
                # Heuristic: Mean sea level pressure in hPa is ~1013, in Pa is ~101325
                mslp_hpa = raw_p / 100.0
                warnings.append("Assumed Pascal units for pressure based on magnitude (mean > 2000).")
            else:
                mslp_hpa = raw_p
                warnings.append("Assumed hPa units for pressure.")

        # --- Precipitation Conversion ---
        if "precipitation" in dataset.variables or "tp" in dataset.variables:
            raw_tp = np.asarray(dataset.variables.get("precipitation", dataset.variables.get("tp")), dtype=np.float64)
            cls._validate_shape(raw_tp, expected_shape, "precipitation")
            raw_tp = cls._clean_non_finite(raw_tp, warnings, "precipitation")

            unit = dataset.units.get("precipitation", dataset.units.get("tp", "")).lower()
            if unit in ["m", "meter", "meters"]:
                precip_mm = raw_tp * 1000.0
            elif unit in ["mm", "kg/m^2", "kg/m2"]:
                precip_mm = raw_tp
            else:
                precip_mm = raw_tp
                warnings.append(f"Unrecognized precipitation unit '{unit}'. Assumed mm.")

        # Process Climatology if provided
        temp_mean, temp_std = cls._process_climatology(dataset, "temperature", expected_shape, warnings, is_temp=True)
        wind_mean, wind_std = cls._process_climatology(dataset, "wind_speed", expected_shape, warnings)
        mslp_mean, mslp_std = cls._process_climatology(dataset, "mslp", expected_shape, warnings, is_pressure=True)

        lead_day = max(1, int(np.ceil(dataset.lead_time_hours / 24.0))) if dataset.lead_time_hours > 0 else 1

        return NormalizedWeatherGrid(
            forecast_init_time=dataset.forecast_init_time,
            valid_time=dataset.valid_time,
            lead_time_hours=dataset.lead_time_hours,
            lead_day=lead_day,
            lats=lats,
            lons=lons,
            shape=expected_shape,
            temperature_celsius=temp_celsius,
            wind_speed_ms=wind_ms,
            mslp_hpa=mslp_hpa,
            precipitation_mm=precip_mm,
            precipitation_accumulation_hours=getattr(dataset, "precipitation_accumulation_hours", 24) or 24,
            temp_clim_mean=temp_mean,
            temp_clim_std=temp_std,
            wind_clim_mean=wind_mean,
            wind_clim_std=wind_std,
            mslp_clim_mean=mslp_mean,
            mslp_clim_std=mslp_std,
            preprocessing_warnings=warnings,
            is_simulated=dataset.is_simulated,
            data_source=dataset.data_source,
        )

    @staticmethod
    def _validate_shape(arr: np.ndarray, expected_shape: Tuple[int, int], var_name: str):
        if arr.shape != expected_shape:
            raise ValueError(f"Variable '{var_name}' shape {arr.shape} does not match coordinate grid dimensions {expected_shape}")

    @staticmethod
    def _clean_non_finite(arr: np.ndarray, warnings: List[str], var_name: str) -> np.ndarray:
        if np.isinf(arr).any():
            warnings.append(f"Infinite values detected in '{var_name}', replaced with NaN.")
            arr = np.where(np.isinf(arr), np.nan, arr)
        return arr

    @staticmethod
    def _process_climatology(
        dataset: WeatherGridDataset, 
        var_key: str, 
        expected_shape: Tuple[int, int], 
        warnings: List[str],
        is_temp: bool = False,
        is_pressure: bool = False
    ) -> Tuple[np.ndarray, np.ndarray]:
        if not dataset.climatology_mean or not dataset.climatology_std:
            return None, None
        
        mean = dataset.climatology_mean.get(var_key)
        std = dataset.climatology_std.get(var_key)
        if mean is None or std is None:
            return None, None

        mean = np.asarray(mean, dtype=np.float64)
        std = np.asarray(std, dtype=np.float64)

        if is_temp and np.nanmean(mean) > 150.0:
            mean = mean - 273.15
        elif is_pressure and np.nanmean(mean) > 2000.0:
            mean = mean / 100.0
            std = std / 100.0

        return mean, std
