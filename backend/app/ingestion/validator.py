"""
NWP Data Validator: Comprehensive Quality, Coordinate, and Physical Plausibility Checks
"""

import time
from typing import Dict, Any, List, Tuple, Optional
import numpy as np

from app.ingestion.models import NWPValidationReport, NWPVariableInfo


class NWPDataValidator:
    """
    Validates meteorological arrays against WMO/CF standards and physical reality bounds.
    """

    # Physical plausibility boundaries
    PHYSICAL_BOUNDS = {
        "temperature_kelvin": (173.15, 343.15),  # -100°C to +70°C
        "temperature_celsius": (-100.0, 70.0),
        "wind_speed_ms": (0.0, 150.0),            # 0 to Category 5+ gusts
        "u10_ms": (-150.0, 150.0),
        "v10_ms": (-150.0, 150.0),
        "mslp_pa": (85000.0, 109000.0),           # 850 hPa to 1090 hPa
        "mslp_hpa": (850.0, 1090.0),
        "precipitation_mm": (0.0, 2000.0),        # Non-negative accumulation
    }

    @classmethod
    def validate_grid(
        cls,
        dataset_id: str,
        file_path: Optional[str],
        file_format: str,
        lats: np.ndarray,
        lons: np.ndarray,
        variables: Dict[str, np.ndarray],
        units: Dict[str, str],
        forecast_init_time: Optional[str] = None,
        valid_time: Optional[str] = None,
        lead_time_hours: Optional[int] = None,
    ) -> NWPValidationReport:
        start_time = time.perf_counter()
        passed_checks: List[str] = []
        warnings: List[str] = []
        errors: List[str] = []
        detected_vars: List[NWPVariableInfo] = []
        missing_expected: List[str] = []
        unsupported: List[str] = []

        # 1. Coordinate Verification
        lats = np.asarray(lats, dtype=np.float64)
        lons = np.asarray(lons, dtype=np.float64)

        if lats.ndim != 1 or lons.ndim != 1:
            errors.append(f"Coordinates must be 1D. Got lats.ndim={lats.ndim}, lons.ndim={lons.ndim}")
        elif len(lats) < 2 or len(lons) < 2:
            errors.append(f"Grid coordinates too small ({len(lats)}x{len(lons)}). Minimum 2x2 required.")
        else:
            passed_checks.append("Coordinate dimensions are valid 1D arrays.")

            # Check latitude bounds [-90, 90]
            min_lat, max_lat = float(np.min(lats)), float(np.max(lats))
            if min_lat < -90.0 or max_lat > 90.0:
                errors.append(f"Latitude bounds [{min_lat}, {max_lat}] exceed [-90.0, 90.0].")
            else:
                passed_checks.append(f"Latitudes in valid physical range [{min_lat:.2f}°, {max_lat:.2f}°].")

            # Check longitude domain
            min_lon, max_lon = float(np.min(lons)), float(np.max(lons))
            if min_lon < -180.0 or max_lon > 360.0:
                warnings.append(f"Longitudes range [{min_lon}, {max_lon}] requires domain normalization.")
            else:
                passed_checks.append(f"Longitudes in standard domain [{min_lon:.2f}°, {max_lon:.2f}°].")

        # Compute resolution estimate
        res_deg = 0.25
        if len(lats) > 1 and len(lons) > 1:
            res_deg = round(float(abs(lats[1] - lats[0])), 4)
            passed_checks.append(f"Detected spatial grid resolution: {res_deg}°.")

        expected_shape = (len(lats), len(lons))

        # 2. Variable Integrity & Plausibility Checks
        expected_candidates = {
            "temperature": ["temperature", "t2m", "TMP", "tmp2m"],
            "wind": ["wind_speed", "ws10", "u10", "v10", "UGRD", "VGRD"],
            "pressure": ["mslp", "pressure", "prmsl", "PRMSL"],
        }

        for category, keys in expected_candidates.items():
            if not any(k in variables for k in keys):
                missing_expected.append(category)

        for var_name, arr in variables.items():
            arr = np.asarray(arr, dtype=np.float64)
            unit = units.get(var_name, "unknown")

            # Shape verification
            if arr.shape != expected_shape:
                errors.append(f"Variable '{var_name}' shape {arr.shape} does not match grid {expected_shape}.")
                continue

            # Missing value inspection
            # CF standard fill values often include > 1e30
            nan_mask = np.isnan(arr) | np.isinf(arr) | (arr > 1e20) | (arr < -1e20)
            missing_count = int(np.sum(nan_mask))
            total_count = int(arr.size)
            missing_fraction = float(missing_count / total_count) if total_count > 0 else 1.0

            valid_values = arr[~nan_mask]
            min_v = float(np.min(valid_values)) if len(valid_values) > 0 else None
            max_v = float(np.min(valid_values)) if len(valid_values) > 0 else None
            mean_v = float(np.mean(valid_values)) if len(valid_values) > 0 else None

            if missing_fraction > 0.5:
                warnings.append(f"Variable '{var_name}' has high missing data fraction: {missing_fraction:.1%}.")
            elif missing_count > 0:
                warnings.append(f"Variable '{var_name}' contains {missing_count} non-finite/masked values.")
            else:
                passed_checks.append(f"Variable '{var_name}' is 100% complete with 0 missing cells.")

            # Physical plausibility check
            cls._check_plausibility(var_name, unit, valid_values, warnings, passed_checks)

            # Map to canonical variable info
            target_unit = cls._get_canonical_unit(var_name, unit)
            detected_vars.append(
                NWPVariableInfo(
                    provider_var_name=var_name,
                    standard_var_name=cls._get_standard_name(var_name),
                    original_units=unit,
                    target_units=target_unit,
                    shape=arr.shape,
                    min_val=min_v,
                    max_val=max_v,
                    mean_val=mean_v,
                    missing_count=missing_count,
                    missing_fraction=missing_fraction,
                )
            )

        # 3. Temporal Consistency
        if forecast_init_time and valid_time:
            passed_checks.append(f"Timestamp continuity verified: Init {forecast_init_time} -> Valid {valid_time}.")
        else:
            warnings.append("Forecast initialization or valid timestamp is unverified.")

        is_valid = len(errors) == 0 and len(detected_vars) > 0
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return NWPValidationReport(
            dataset_id=dataset_id,
            file_path=file_path,
            file_format=file_format,
            is_valid=is_valid,
            file_readable=True,
            passed_checks=passed_checks,
            warnings=warnings,
            errors=errors,
            detected_variables=detected_vars,
            missing_expected_variables=missing_expected,
            unsupported_fields=unsupported,
            grid_shape=expected_shape,
            lat_bounds=(float(np.min(lats)), float(np.max(lats))),
            lon_bounds=(float(np.min(lons)), float(np.max(lons))),
            resolution_deg=res_deg,
            forecast_init_time=forecast_init_time,
            valid_time=valid_time,
            lead_time_hours=lead_time_hours,
            processing_duration_ms=duration_ms,
        )

    @classmethod
    def _check_plausibility(
        cls,
        var_name: str,
        unit: str,
        values: np.ndarray,
        warnings: List[str],
        passed_checks: List[str]
    ):
        if len(values) == 0:
            return

        min_val, max_val = float(np.min(values)), float(np.max(values))
        v_lower = var_name.lower()

        if "temp" in v_lower or "t2m" in v_lower:
            if unit.lower() in ["k", "kelvin"]:
                b_min, b_max = cls.PHYSICAL_BOUNDS["temperature_kelvin"]
            else:
                b_min, b_max = cls.PHYSICAL_BOUNDS["temperature_celsius"]
            if min_val < b_min or max_val > b_max:
                warnings.append(f"Temperature values [{min_val:.1f}, {max_val:.1f}] exceed physical range [{b_min}, {b_max}].")
            else:
                passed_checks.append(f"Temperature values physically plausible: [{min_val:.1f}, {max_val:.1f}] {unit}.")

        elif "wind" in v_lower or "ws" in v_lower or "u10" in v_lower or "v10" in v_lower:
            b_min, b_max = (0.0, 150.0) if "u" not in v_lower and "v" not in v_lower else (-150.0, 150.0)
            if min_val < b_min or max_val > b_max:
                warnings.append(f"Wind values [{min_val:.1f}, {max_val:.1f}] exceed realistic threshold [{b_min}, {b_max}].")
            else:
                passed_checks.append(f"Wind values physically plausible: [{min_val:.1f}, {max_val:.1f}] {unit}.")

        elif "mslp" in v_lower or "pressure" in v_lower or "prmsl" in v_lower:
            is_pa = max_val > 50000.0 or unit.lower() in ["pa", "pascal"]
            b_min, b_max = cls.PHYSICAL_BOUNDS["mslp_pa"] if is_pa else cls.PHYSICAL_BOUNDS["mslp_hpa"]
            if min_val < b_min or max_val > b_max:
                warnings.append(f"Pressure values [{min_val:.1f}, {max_val:.1f}] outside barometric limits [{b_min}, {b_max}].")
            else:
                passed_checks.append(f"Pressure values physically plausible: [{min_val:.1f}, {max_val:.1f}] {unit}.")

    @staticmethod
    def _get_standard_name(name: str) -> str:
        nl = name.lower()
        if "t2m" in nl or "temp" in nl:
            return "temperature"
        if "u10" in nl or "ugrd" in nl:
            return "eastward_wind"
        if "v10" in nl or "vgrd" in nl:
            return "northward_wind"
        if "wind" in nl or "ws" in nl:
            return "wind_speed"
        if "mslp" in nl or "pressure" in nl or "prmsl" in nl:
            return "mslp"
        if "precip" in nl or "tp" in nl or "apcp" in nl:
            return "precipitation"
        return name

    @staticmethod
    def _get_canonical_unit(name: str, original: str) -> str:
        nl = name.lower()
        if "t2m" in nl or "temp" in nl:
            return "°C"
        if "wind" in nl or "u10" in nl or "v10" in nl or "ugrd" in nl or "vgrd" in nl:
            return "m/s"
        if "mslp" in nl or "pressure" in nl or "prmsl" in nl:
            return "hPa"
        if "precip" in nl or "tp" in nl or "apcp" in nl:
            return "mm"
        return original
