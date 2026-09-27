"""
Deterministic Synthetic Meteorological Grid Generator with Injected Anomaly Ground-Truth
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np
from app.engine.schemas import WeatherGridDataset


class SyntheticWeatherGenerator:
    """
    Produces deterministic, physically plausible multidimensional weather grids
    with precisely embedded anomaly signatures and ground-truth validation masks.
    """

    @classmethod
    def generate_dataset(
        cls, 
        lead_time_hours: int = 24, 
        seed: int = 42,
        scenario: Optional[str] = None
    ) -> Tuple[WeatherGridDataset, Dict[str, np.ndarray]]:
        """
        Generates a 0.5-degree grid spanning [-30.0, 65.0] Lat and [40.0, 120.0] Lon.
        Supports focusing on specific reproducible scenarios: 'cyclone', 'heatwave', 'coldwave', or None (all).
        Returns:
            - WeatherGridDataset ready for preprocessor & detection pipeline
            - ground_truth_masks: Dict mapping anomaly name to boolean 2D numpy mask
        """
        rng = np.random.RandomState(seed + lead_time_hours)
        scenario_key = scenario.lower().strip() if scenario else "all"

        # 1. Coordinates: 96 lat points x 161 lon points (0.5 degree resolution)
        lats = np.linspace(-30.0, 65.0, 96, dtype=np.float64)
        lons = np.linspace(40.0, 120.0, 161, dtype=np.float64)
        lat_grid, lon_grid = np.meshgrid(lats, lons, indexing="ij")
        shape = lat_grid.shape

        # 2. Climatological Background Normals
        # Temperature: Pre-monsoon continental thermal profile with subtropical peak
        temp_clim_mean = 31.0 - 0.012 * (lat_grid - 22.0)**2 + rng.normal(0, 0.2, size=shape)
        temp_clim_std = 2.5 + 0.8 * (np.abs(lat_grid) / 60.0)

        # Mean Sea-Level Pressure: 1013.25 hPa background with mild synoptic variations
        mslp_clim_mean = 1013.25 + 4.0 * np.sin(np.radians(lat_grid * 2)) + rng.normal(0, 0.4, size=shape)
        mslp_clim_std = np.full(shape, 3.5, dtype=np.float64)

        # Wind Speed: 6 to 12 m/s background
        wind_clim_mean = 7.0 + 3.0 * np.abs(np.sin(np.radians(lat_grid * 3))) + rng.normal(0, 0.3, size=shape)
        wind_clim_std = np.full(shape, 2.0, dtype=np.float64)

        # Initialize observed fields with baseline values
        temp_obs = temp_clim_mean.copy()
        mslp_obs = mslp_clim_mean.copy()
        wind_obs = wind_clim_mean.copy()
        precip_obs = np.maximum(0.0, rng.exponential(scale=2.5, size=shape))

        # 3. Ground-Truth Masks Dictionary for Evaluation
        ground_truth_masks = {
            "cyclone_pressure": np.zeros(shape, dtype=bool),
            "cyclone_wind": np.zeros(shape, dtype=bool),
            "heat_dome": np.zeros(shape, dtype=bool),
            "cold_wave": np.zeros(shape, dtype=bool),
            "wind_squall": np.zeros(shape, dtype=bool),
            "heavy_rain": np.zeros(shape, dtype=bool),
        }

        # Step offset for temporal movement
        day_offset = (lead_time_hours // 24)

        # -------------------------------------------------------------
        # INJECTED ANOMALY 1: Tropical Cyclone (Western Indian Ocean)
        # Deep pressure depression (< 975 hPa) + Gale winds (> 35 m/s)
        # Centroid translates with lead time
        # -------------------------------------------------------------
        if scenario_key in ("cyclone", "all"):
            cyc_lat = -12.0 - (day_offset * 1.5)
            cyc_lon = 78.0 - (day_offset * 1.8)
            cyc_dist = np.sqrt((lat_grid - cyc_lat)**2 + (lon_grid - cyc_lon)**2)
            cyc_radius = 4.5  # ~500 km radius

            cyc_mask = cyc_dist <= cyc_radius
            # Inject pressure dip: drops by up to 55 hPa in core
            mslp_obs[cyc_mask] -= 55.0 * np.exp(-((cyc_dist[cyc_mask] / 2.5)**2))
            ground_truth_masks["cyclone_pressure"] = (cyc_dist <= 3.8) & (mslp_obs <= 998.0)

            # Inject cyclonic eyewall wind: peak ~ 38 m/s at 1.5 deg radius
            wind_ring = 35.0 * np.exp(-(((cyc_dist - 1.5) / 1.5)**2))
            wind_obs[cyc_mask] = np.maximum(wind_obs[cyc_mask], wind_ring[cyc_mask])
            ground_truth_masks["cyclone_wind"] = (cyc_dist <= 3.5) & (wind_obs >= 17.5)

        # -------------------------------------------------------------
        # INJECTED ANOMALY 2: Severe Heat Dome (Northwest Subtropics)
        # Elevated temperatures (> 42°C, Z > 3.0)
        # -------------------------------------------------------------
        if scenario_key in ("heatwave", "heat_dome", "all"):
            heat_lat = 26.5 + (day_offset * 0.4)
            heat_lon = 71.5 + (day_offset * 0.6)
            heat_dist = np.sqrt((lat_grid - heat_lat)**2 + (lon_grid - heat_lon)**2)
            heat_radius = 4.8

            heat_mask = heat_dist <= heat_radius
            # Add +15°C thermal dome anomaly
            temp_obs[heat_mask] += 15.0 * np.exp(-((heat_dist[heat_mask] / 2.6)**2))
            z_heat_calc = (temp_obs - temp_clim_mean) / temp_clim_std
            ground_truth_masks["heat_dome"] = (heat_dist <= 3.8) & ((temp_obs >= 40.0) | (z_heat_calc >= 2.5))

        # -------------------------------------------------------------
        # INJECTED ANOMALY 3: Arctic Cold Wave Outbreak (Siberia)
        # Plunging sub-zero freeze (< -15°C, Z < -3.0)
        # -------------------------------------------------------------
        if scenario_key in ("coldwave", "cold_wave", "all"):
            cold_lat = 58.0 - (day_offset * 1.0)
            cold_lon = 102.0 + (day_offset * 1.2)
            cold_dist = np.sqrt((lat_grid - cold_lat)**2 + (lon_grid - cold_lon)**2)
            cold_radius = 5.0

            cold_mask = cold_dist <= cold_radius
            # Drop temperature by -28°C
            temp_obs[cold_mask] -= 28.0 * np.exp(-((cold_dist[cold_mask] / 2.8)**2))
            z_cold_calc = (temp_obs - temp_clim_mean) / temp_clim_std
            ground_truth_masks["cold_wave"] = (cold_dist <= 3.8) & (temp_obs <= 4.0) & (z_cold_calc <= -2.5)

        # -------------------------------------------------------------
        # INJECTED ANOMALY 4: Monsoonal Wind Squall (Arabian Sea)
        # Sustained gale wind (> 22 m/s)
        # -------------------------------------------------------------
        if scenario_key == "all":
            squall_lat = 16.0
            squall_lon = 65.0
            squall_dist = np.sqrt((lat_grid - squall_lat)**2 + (lon_grid - squall_lon)**2)
            squall_radius = 3.5

            squall_mask = squall_dist <= squall_radius
            wind_obs[squall_mask] = np.maximum(wind_obs[squall_mask], 24.0 * np.exp(-((squall_dist[squall_mask] / 2.0)**2)))
            ground_truth_masks["wind_squall"] = (squall_dist <= 2.5) & (wind_obs >= 18.0)

            # -------------------------------------------------------------
            # INJECTED ANOMALY 5: Extreme Monsoon Rainfall (Western Ghats)
            # Heavy/Extreme Precipitation (> 120 mm / 24h)
            # -------------------------------------------------------------
            rain_lat = 14.5
            rain_lon = 74.8
            rain_dist = np.sqrt((lat_grid - rain_lat)**2 + (lon_grid - rain_lon)**2)
            rain_radius = 3.0

            rain_mask = rain_dist <= rain_radius
            precip_obs[rain_mask] += 160.0 * np.exp(-((rain_dist[rain_mask] / 1.8)**2))
            ground_truth_masks["heavy_rain"] = (rain_dist <= 2.2) & (precip_obs >= 64.5)

        # Construct WeatherGridDataset with Kelvin, Pascal, m/s, mm to test canonical preprocessing
        dataset = WeatherGridDataset(
            forecast_init_time="2025-04-26T00:00:00Z",
            valid_time=f"2025-04-{26 + day_offset:02d}T00:00:00Z",
            lead_time_hours=lead_time_hours,
            lats=lats,
            lons=lons,
            variables={
                "temperature": temp_obs + 273.15,     # In Kelvin (tests K -> °C conversion)
                "mslp": mslp_obs * 100.0,              # In Pascal (tests Pa -> hPa conversion)
                "wind_speed": wind_obs,                # In m/s
                "precipitation": precip_obs,           # In mm (tests mm handling)
            },
            units={
                "temperature": "K",
                "mslp": "Pa",
                "wind_speed": "m/s",
                "precipitation": "mm",
            },
            climatology_mean={
                "temperature": temp_clim_mean + 273.15,
                "mslp": mslp_clim_mean * 100.0,
                "wind_speed": wind_clim_mean,
            },
            climatology_std={
                "temperature": temp_clim_std,
                "mslp": mslp_clim_std * 100.0,
                "wind_speed": wind_clim_std,
            },
            is_simulated=True,
            data_source="AERONEX_SYNTHETIC_EVAL_GENERATOR",
        )

        return dataset, ground_truth_masks
