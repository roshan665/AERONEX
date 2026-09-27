"""
Forecast Service for Multi-Variable Time-Series & Run Metadata
"""

from typing import Optional, List
from fastapi import HTTPException
from app.data.demo_data import FORECAST_TIME_SERIES, SYSTEM_METADATA
from app.models.forecast import (
    ForecastResponse, 
    ForecastTimelineItem, 
    ForecastRunMetadata
)

SUPPORTED_VARIABLES = {
    "temperature": {"name": "2m Air Temperature", "unit": "°C"},
    "wind": {"name": "10m Wind Speed", "unit": "km/h"},
    "pressure": {"name": "Mean Sea-Level Pressure", "unit": "hPa"},
    "precipitation": {"name": "Accumulated Precipitation", "unit": "mm"},
}


class ForecastService:
    @staticmethod
    def get_forecasts(
        variable: str = "temperature",
        region_id: Optional[str] = None,
        lead_day: Optional[int] = None,
    ) -> ForecastResponse:
        var_key = variable.lower().strip()
        if var_key not in SUPPORTED_VARIABLES:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported meteorological variable '{variable}'. Supported variables are: {list(SUPPORTED_VARIABLES.keys())}"
            )

        if lead_day is not None and (lead_day < 1 or lead_day > 10):
            raise HTTPException(
                status_code=422,
                detail=f"Lead day {lead_day} is out of bounds. The forecast horizon is restricted to Days 1–10."
            )

        var_data = FORECAST_TIME_SERIES[var_key]
        raw_timeline = var_data["timeline"]

        if lead_day is not None:
            raw_timeline = [item for item in raw_timeline if item["lead_day"] == lead_day]

        timeline_items = [
            ForecastTimelineItem(
                day=item["day"],
                lead_day=item["lead_day"],
                lead_time_hours=item["lead_time_hours"],
                valid_time=item["valid_time"],
                global_avg=item["global_avg"],
                max=item["max"],
                min=item["min"],
                uncertainty_upper=item["uncertainty_upper"],
                uncertainty_lower=item["uncertainty_lower"],
                confidence_rating=item["confidence_rating"],
            )
            for item in raw_timeline
        ]

        return ForecastResponse(
            forecast_id=f"GFS-SIM-{SYSTEM_METADATA['initialization_time'][:10]}-00Z",
            variable=var_key,
            variable_name=var_data["variable_name"],
            unit=var_data["unit"],
            model_initialization=SYSTEM_METADATA["initialization_time"],
            region_id=region_id,
            horizon_days=10,
            timeline=timeline_items,
            data_provenance=SYSTEM_METADATA["data_provenance"],
            is_simulated=True,
            disclaimer=SYSTEM_METADATA["disclaimer"],
        )

    @staticmethod
    def get_forecast_by_id(forecast_id: str) -> ForecastRunMetadata:
        # Standard synthetic forecast run IDs: GFS-20250426-00Z or similar
        if not forecast_id.startswith("GFS-"):
            raise HTTPException(
                status_code=404,
                detail=f"Forecast model run ID '{forecast_id}' does not exist in the active catalog."
            )

        return ForecastRunMetadata(
            forecast_id=forecast_id,
            model_name="NOAA-GFS-SYNTHETIC-2025",
            initialization_time=SYSTEM_METADATA["initialization_time"],
            spatial_resolution_deg=SYSTEM_METADATA["grid_spacing_degrees"],
            spatial_resolution=f"{SYSTEM_METADATA['grid_spacing_degrees']}°",
            grid_dimensions={"n_lat": 721, "n_lon": 1440},
            available_lead_times_hours=[24, 48, 72, 96, 120, 144, 168, 192, 216, 240],
            available_variables=list(SUPPORTED_VARIABLES.keys()),
            format="NetCDF4-Compatible",
            data_provenance=SYSTEM_METADATA["data_provenance"],
            is_simulated=True,
        )
