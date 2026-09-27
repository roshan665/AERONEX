# AeroNex: REST API Specification

[![OpenAPI Spec](https://img.shields.io/badge/OpenAPI-3.1.0-teal.svg)](https://swagger.io/specification/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com)
[![Validation](https://img.shields.io/badge/Validation-Pydantic%20v2-red.svg)](https://docs.pydantic.dev)

This document establishes the formal REST API contract for the **AeroNex** backend services. All endpoints adhere to REST conventions, return standard HTTP status codes, serialize responses in JSON (or GeoJSON `RFC 7946`), and emit standardized error objects.

---

## 1. Global Conventions & Standards

* **Base URL**: `http://localhost:8000/api/v1` (Development)
* **Standard Headers**:
  * `Content-Type: application/json`
  * `Accept: application/json`
* **Error Envelope (RFC 7807 Compliant)**:
  ```json
  {
    "type": "https://aeronex.gov.in/errors/INVALID_COORDINATE_RANGE",
    "title": "Invalid Coordinate Range",
    "status": 422,
    "detail": "Latitude value 112.5 exceeds permissible bounds [-90.0, 90.0].",
    "instance": "/api/v1/forecasts",
    "timestamp": "2026-09-26T08:15:00Z"
  }
  ```
* **Coordinate Ordering**:
  * GeoJSON Standard: `[Longitude, Latitude]` (i.e. `[x, y]`).
  * Tabular / Scalar Attributes: `latitude` (Float, -90 to +90), `longitude` (Float, -180 to +180).

---

## 2. API Endpoints Overview

| Method | Endpoint Path | Summary | Primary Return Format |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Service health status and runtime environment. | JSON |
| `GET` | `/overview` | Executive situational dashboard KPIs and alerts. | JSON |
| `GET` | `/forecasts` | Time-series meteorological forecast slices by location. | JSON |
| `GET` | `/forecasts/{forecast_id}` | Detailed multidimensional grid metadata for a specific run. | JSON |
| `GET` | `/anomalies` | Detected extreme anomaly event catalog & footprints. | GeoJSON FeatureCollection |
| `GET` | `/anomalies/{anomaly_id}` | Comprehensive diagnostic profile of a single anomaly event. | GeoJSON Feature |
| `GET` | `/map/layers` | Active raster/contour layer descriptors and color ramps. | JSON |
| `GET` | `/regions` | Predefined geographic bounding boxes and monitor status. | JSON |
| `GET` | `/metadata` | Dataset provenance, model initialization, and data dictionary. | JSON |
| `GET` | `/datasets` | Enumerate available real and cached NWP datasets. | JSON |
| `GET` | `/datasets/{dataset_id}` | Detailed metadata for a specific NWP dataset. | JSON |
| `POST` | `/ingestion/validate` | Dry-run physics and coordinate validation for a dataset. | JSON |
| `POST` | `/ingestion/run` | Execute ingestion pipeline and optional anomaly detection. | JSON |
| `GET` | `/ingestion/status` | Current ingestion pipeline state and data provenance. | JSON |
| `GET` | `/events/tracks` | Enumerate multi-horizon anomaly tracked series. | JSON |
| `GET` | `/events/tracks/{track_id}` | Detailed trajectory profile and movement notes. | JSON |
| `GET` | `/events/tracks/{track_id}/history` | Chronological TrackPoint sequence (Days 1–10). | JSON |
| `GET` | `/uncertainty` | System uncertainty status, mode, and decay guide. | JSON |
| `GET` | `/uncertainty/{event_id}` | Event-specific ensemble spread or decay profile. | JSON |

---

## 3. Endpoint Specifications

### 3.1 `GET /api/v1/health`

#### Purpose
Liveness and readiness probe for container orchestrators and frontend initialization checks.

#### Query Parameters
*None.*

#### Response Status
* `200 OK`: Service operational.

#### Response Body Example
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 14250.4,
  "data_mode": "DEMO_SYNTHETIC",
  "dataset_timestamp": "2026-09-26T00:00:00Z",
  "services": {
    "api_gateway": "ONLINE",
    "xarray_engine": "ONLINE",
    "footprint_engine": "ONLINE"
  }
}
```

---

### 3.2 `GET /api/v1/overview`

#### Purpose
Delivers aggregated situational intelligence to populate the main dashboard KPI cards and high-priority alert ticker.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `region_id` | `string` | Optional | `null` | Filters metrics to a specific region (e.g., `bay_of_bengal`). |

#### Response Status
* `200 OK`: Successfully computed KPIs.
* `404 Not Found`: Unknown `region_id`.

#### Response Body Example
```json
{
  "summary": {
    "active_anomaly_count": 4,
    "critical_alerts_count": 2,
    "monitored_regions_count": 5,
    "forecast_horizon_hours": 240,
    "latest_model_run": "2026-09-26T00:00:00Z",
    "data_provenance": "DEMO_SYNTHETIC"
  },
  "hazard_breakdown": {
    "cyclones": 1,
    "heat_domes": 2,
    "cold_waves": 1,
    "gale_winds": 0
  },
  "critical_alerts": [
    {
      "event_id": "CYC-202410-001",
      "hazard_type": "CYCLONIC_DEPRESSION",
      "severity": "EXTREME",
      "region": "Bay of Bengal",
      "centroid": [87.4, 18.8],
      "peak_intensity": "974 hPa / 38.2 m/s",
      "lead_time_hours": 48,
      "valid_time": "2026-09-28T00:00:00Z"
    },
    {
      "event_id": "HEAT-202410-002",
      "hazard_type": "HEAT_DOME",
      "severity": "SEVERE",
      "region": "Northern Plains",
      "centroid": [76.2, 28.6],
      "peak_intensity": "44.6 °C (+3.4σ)",
      "lead_time_hours": 72,
      "valid_time": "2026-09-29T00:00:00Z"
    }
  ]
}
```

---

### 3.3 `GET /api/v1/forecasts`

#### Purpose
Retrieves multi-timestep forecast curves and uncertainty envelopes for a specific coordinate point or region.

#### Query Parameters
| Parameter | Type | Required | Default | Validation | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `lat` | `float` | Required | — | $[-90.0, 90.0]$ | Latitude coordinate. |
| `lon` | `float` | Required | — | $[-180.0, 180.0]$ | Longitude coordinate. |
| `variable` | `string` | Optional | `t2m` | Enum: `t2m`, `ws10`, `mslp` | Meteorological variable. |

#### Response Status
* `200 OK`: Valid time-series returned.
* `422 Unprocessable Entity`: Coordinate values out of range.

#### Response Body Example
```json
{
  "location": {
    "latitude": 20.27,
    "longitude": 85.84,
    "name": "Bhubaneswar Coastal Sector"
  },
  "variable": "t2m",
  "unit": "°C",
  "model_run": "2026-09-26T00:00:00Z",
  "climatological_normal": {
    "mean": 32.4,
    "std_dev": 2.1
  },
  "timeline": [
    {
      "lead_time_hours": 0,
      "valid_time": "2026-09-26T00:00:00Z",
      "deterministic_value": 31.8,
      "uncertainty_lower_p10": 31.2,
      "uncertainty_upper_p90": 32.4,
      "confidence_rating": "HIGH",
      "is_anomalous": false
    },
    {
      "lead_time_hours": 48,
      "valid_time": "2026-09-28T00:00:00Z",
      "deterministic_value": 39.8,
      "uncertainty_lower_p10": 38.1,
      "uncertainty_upper_p90": 41.5,
      "confidence_rating": "HIGH",
      "is_anomalous": true
    },
    {
      "lead_time_hours": 120,
      "valid_time": "2026-10-01T00:00:00Z",
      "deterministic_value": 43.2,
      "uncertainty_lower_p10": 39.5,
      "uncertainty_upper_p90": 46.8,
      "confidence_rating": "MODERATE",
      "is_anomalous": true
    }
  ]
}
```

---

### 3.4 `GET /api/v1/forecasts/{forecast_id}`

#### Purpose
Fetches metadata, grid resolution, and variable slices for a specific forecast cycle.

#### Path Parameters
* `forecast_id` (`string`): Unique model run identifier (e.g., `GFS-20260926-00Z`).

#### Response Status
* `200 OK`: Forecast run details found.
* `404 Not Found`: Forecast ID does not exist.

#### Response Body Example
```json
{
  "forecast_id": "GFS-20260926-00Z",
  "model_name": "NOAA-GFS-SIMULATED",
  "initialization_time": "2026-09-26T00:00:00Z",
  "spatial_resolution_deg": 0.25,
  "grid_dimensions": {
    "n_lat": 721,
    "n_lon": 1440
  },
  "available_lead_times_hours": [0, 6, 12, 24, 48, 72, 96, 120, 168, 240],
  "available_variables": ["t2m", "u10", "v10", "ws10", "mslp"],
  "format": "NetCDF4"
}
```

---

### 3.5 `GET /api/v1/anomalies`

#### Purpose
Returns a GeoJSON `FeatureCollection` containing vector polygons of all detected extreme weather footprints matching query criteria.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `step` | `int` | Optional | `48` | Forecast lead time in hours ($[0, 240]$). |
| `hazard_type` | `string` | Optional | `null` | Enum: `CYCLONIC_DEPRESSION`, `HEAT_DOME`, `COLD_WAVE`, `GALE_WIND`. |
| `severity` | `string` | Optional | `null` | Enum: `ADVISORY`, `MODERATE`, `SEVERE`, `EXTREME`. |
| `min_area_km2` | `float` | Optional | `2500.0` | Minimum surface area filter. |

#### Response Status
* `200 OK`: Valid GeoJSON FeatureCollection returned.

#### Response Body Example
```json
{
  "type": "FeatureCollection",
  "metadata": {
    "forecast_step_hours": 48,
    "valid_time": "2026-09-28T00:00:00Z",
    "total_features": 1,
    "data_provenance": "DEMO_SYNTHETIC"
  },
  "features": [
    {
      "type": "Feature",
      "id": "CYC-202410-001",
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [85.5, 17.5],
            [88.2, 17.8],
            [89.1, 19.5],
            [86.8, 20.4],
            [85.5, 17.5]
          ]
        ]
      },
      "properties": {
        "event_id": "CYC-202410-001",
        "hazard_type": "CYCLONIC_DEPRESSION",
        "severity": "EXTREME",
        "centroid": [87.4, 18.8],
        "area_km2": 52400.0,
        "peak_wind_speed_ms": 38.2,
        "min_mslp_hpa": 974.0,
        "confidence": "HIGH",
        "description": "Intense cyclonic vortex centered over the Bay of Bengal with central pressure deficit > 30 hPa."
      }
    }
  ]
}
```

---

### 3.6 `GET /api/v1/anomalies/{anomaly_id}`

#### Purpose
Delivers deep analytical telemetry for a single anomaly entity, including its temporal evolution and component metrics.

#### Path Parameters
* `anomaly_id` (`string`): Unique event identifier (e.g., `CYC-202410-001`).

#### Response Status
* `200 OK`: Event diagnostics found.
* `404 Not Found`: Event not recognized.

#### Response Body Example
```json
{
  "event_id": "CYC-202410-001",
  "hazard_type": "CYCLONIC_DEPRESSION",
  "severity": "EXTREME",
  "detection_timestamp": "2026-09-26T00:00:00Z",
  "target_forecast_step": 48,
  "valid_time": "2026-09-28T00:00:00Z",
  "geographic_metrics": {
    "centroid": {"lat": 18.8, "lon": 87.4},
    "bounding_box": [85.5, 17.5, 89.1, 20.4],
    "estimated_area_km2": 52400.0
  },
  "meteorological_metrics": {
    "minimum_mslp_hpa": 974.0,
    "climatological_mslp_normal_hpa": 1010.5,
    "pressure_deficit_hpa": -36.5,
    "maximum_sustained_wind_ms": 38.2,
    "wind_speed_z_score": 4.1
  },
  "evolution_trajectory": [
    {"step": 24, "centroid": [88.5, 16.2], "min_mslp": 992.0},
    {"step": 48, "centroid": [87.4, 18.8], "min_mslp": 974.0},
    {"step": 72, "centroid": [86.1, 20.5], "min_mslp": 980.0}
  ]
}
```

---

### 3.7 `GET /api/v1/map/layers`

#### Purpose
Returns the configuration registry of active weather scalar layers, styling ramps, units, and rendering limits for the Leaflet client.

#### Response Status
* `200 OK`: Layers list returned.

#### Response Body Example
```json
{
  "available_layers": [
    {
      "layer_id": "t2m",
      "display_name": "2m Air Temperature",
      "unit": "°C",
      "default_active": true,
      "color_scale": "turbo",
      "range": {"min": -20.0, "max": 50.0},
      "legend_stops": [
        {"value": -10, "color": "#3B82F6"},
        {"value": 15, "color": "#10B981"},
        {"value": 30, "color": "#FBBF24"},
        {"value": 45, "color": "#EF4444"}
      ]
    },
    {
      "layer_id": "ws10",
      "display_name": "10m Wind Speed",
      "unit": "m/s",
      "default_active": false,
      "color_scale": "plasma",
      "range": {"min": 0.0, "max": 50.0},
      "legend_stops": [
        {"value": 0, "color": "#0F172A"},
        {"value": 15, "color": "#38BDF8"},
        {"value": 30, "color": "#F59E0B"},
        {"value": 45, "color": "#EF4444"}
      ]
    },
    {
      "layer_id": "mslp",
      "display_name": "Mean Sea-Level Pressure",
      "unit": "hPa",
      "default_active": false,
      "color_scale": "coolwarm",
      "range": {"min": 960.0, "max": 1030.0},
      "legend_stops": [
        {"value": 970, "color": "#881337"},
        {"value": 1000, "color": "#E2E8F0"},
        {"value": 1025, "color": "#1E3A8A"}
      ]
    }
  ]
}
```

---

### 3.8 `GET /api/v1/regions`

#### Purpose
Lists predefined geographic monitoring sectors with their bounding coordinates.

#### Response Status
* `200 OK`: Regions list returned.

#### Response Body Example
```json
[
  {
    "region_id": "bay_of_bengal",
    "name": "Bay of Bengal & Odisha Coast",
    "bounds": [80.0, 10.0, 95.0, 22.5],
    "center": [16.5, 87.5],
    "monitored": true
  },
  {
    "region_id": "northern_plains",
    "name": "Northern & Central Plains (Heat Corridor)",
    "bounds": [72.0, 24.0, 84.0, 31.0],
    "center": [27.5, 78.0],
    "monitored": true
  },
  {
    "region_id": "arabian_sea",
    "name": "Arabian Sea & Western Coast",
    "bounds": [65.0, 8.0, 75.0, 24.0],
    "center": [16.0, 70.0],
    "monitored": true
  }
]
```

---

### 3.9 `GET /api/v1/metadata`

#### Purpose
Provides operational system metadata, active dataset provenance, and data dictionary descriptions.

#### Response Status
* `200 OK`: Metadata payload returned.

#### Response Body Example
```json
{
  "system_name": "AeroNex Meteorological Intelligence Engine",
  "version": "1.0.0",
  "active_dataset": {
    "source_type": "SYNTHETIC_SAMPLE_DATASET",
    "base_model": "NOAA-GFS-COMPATIBLE",
    "model_cycle": "2026-09-26T00:00:00Z",
    "grid_spacing_degrees": 0.25,
    "forecast_range_hours": 240,
    "timestep_interval_hours": 24
  },
  "methodology_reference": {
    "z_score_baseline": "ERA5 Climatology Normal (1991-2020)",
    "clustering_algorithm": "SciPy Morphological 8-Connectivity",
    "area_correction": "Cosine Latitude Spherical Metric"
  }
}
```

---

### 3.10 `POST /api/detection/run`

#### Purpose
Executes the end-to-end scientific anomaly detection and geospatial footprint extraction pipeline on multidimensional meteorological grids.

#### Request Body Schema (`DetectionRunRequest`)
| Field | Type | Default | Permissible Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| `lead_time_hours` | Integer | `24` | `0` to `240` | Forecast lead time offset in hours. |
| `min_area_km2` | Float | `2500.0` | $\ge 0.0$ | Minimum spatial footprint filter in square kilometers. |
| `connectivity` | Integer | `8` | `4` or `8` | Morphological connectivity structuring element. |
| `seed` | Integer | `42` | Any Int | Seed for deterministic reproducible synthetic datasets. |

#### Request Example
```json
{
  "lead_time_hours": 24,
  "min_area_km2": 2500.0,
  "connectivity": 8,
  "seed": 42
}
```

#### Response Status
* `200 OK`: Pipeline execution succeeded. Returns execution timing, detected anomaly events, vector footprints, and data provenance.
* `422 Unprocessable Entity`: Parameter validation error (e.g. invalid connectivity, negative area, lead time $>240$).
* `500 Internal Server Error`: Pipeline failure during execution.

#### Response Body Example (`PipelineExecutionResult`)
```json
{
  "execution_time_ms": 19.06,
  "lead_time_hours": 24,
  "valid_time": "2025-04-27T00:00:00Z",
  "grid_shape": [96, 161],
  "total_anomalies_detected": 5,
  "total_footprints_extracted": 6,
  "events": [
    {
      "id": "CYC-20250427-135_762",
      "name": "Tropical Cyclone Vortex",
      "type": "Cyclone",
      "category_key": "cyclone",
      "region": "Western Indian Ocean",
      "lat": -13.5,
      "lon": 76.2,
      "coordinates_display": "13.5°S, 76.2°E",
      "forecast_window": "Day 1 – Day 4",
      "forecast_days": [1, 2, 3],
      "severity": "High",
      "severity_level": 3,
      "estimated_area": "~ 420,635 km²",
      "estimated_area_km2": 420635.1,
      "max_wind": "107 - 126 km/h",
      "central_pressure": "958 - 973 hPa",
      "anomaly_score": "+15.0σ (Vortex Coupling)",
      "color": "#ef4444",
      "description": "Multi-variable cyclonic vortex detected with central pressure deficit of 54.5 hPa coupled with sustained gale winds exceeding 126 km/h.",
      "updated_ago": "Just now",
      "detection_timestamp": "2025-04-27T00:00:00Z",
      "is_simulated": true,
      "primary_variable": "mslp+wind_speed",
      "detection_method": "Multi-Variable Physical Vortex Coupling (Low Pressure + Gale Wind)",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[72.75, -16.5], [79.75, -16.5], [79.75, -10.5], [72.75, -10.5], [72.75, -16.5]]]
      },
      "data_source": "AERONEX_SYNTHETIC_EVAL_GENERATOR"
    }
  ],
  "footprints": [
    {
      "cluster_id": 1,
      "event_id": "ANOM-PRES-001",
      "name": "Deep Cyclonic Depression",
      "category": "pressure_anomaly",
      "hazard_type": "Pressure Anomaly",
      "severity": "High",
      "severity_level": 3,
      "primary_variable": "mslp",
      "canonical_unit": "hPa",
      "centroid_lat": -13.5,
      "centroid_lon": 76.2,
      "coordinates_display": "13.5°S, 76.2°E",
      "bounds": [72.75, -16.5, 79.75, -10.5],
      "estimated_area_km2": 420635.1,
      "cell_count": 63,
      "max_anomaly_score": 15.02,
      "mean_anomaly_score": 5.92,
      "peak_metric_value": 958.8,
      "polygon_coordinates": [[[72.75, -16.5], [79.75, -16.5], [79.75, -10.5], [72.75, -10.5], [72.75, -16.5]]],
      "detection_method": "Hybrid (Barometric Threshold & Negative Z-Score)",
      "is_simulated": true
    }
  ],
  "temporal_associations": [],
  "preprocessing_warnings": [],
  "data_provenance": "AERONEX_SYNTHETIC_EVAL_GENERATOR",
  "is_simulated": true
}
```

---

### 3.10 `GET /api/datasets`

#### Purpose
Enumerate all available local NWP forecast files (in `backend/data/nwp/`) and cached real-data subsets (in `backend/data/cache/`).

#### Query Parameters
*None.*

#### Response Status
* `200 OK`: Returns list of dataset summaries.

#### Response Body Example
```json
[
  {
    "dataset_id": "gfs_sample_0p25_south_asia",
    "filename": "gfs_sample_0p25_south_asia.nc",
    "provider": "NOAA GFS / Local CF-1.8 NetCDF4",
    "file_format": "netcdf4",
    "cycle_date": "20260926",
    "cycle_hour": "00",
    "lead_time_hours": 24,
    "spatial_resolution_deg": 0.25,
    "region_name": "South Asia",
    "geographic_bounds": [8.0, 38.0, 65.0, 95.0],
    "variables": ["t2m", "u10", "v10", "mslp", "tp"],
    "file_size_bytes": 313344,
    "is_cached": true,
    "is_real_data": true,
    "data_provenance": "LOCAL_NWP_NETCDF"
  }
]
```

---

### 3.11 `GET /api/datasets/{dataset_id}`

#### Purpose
Retrieves comprehensive metadata, spatial extents, variable definitions, and dimensions for a specific dataset.

#### Path Parameters
* `dataset_id` (string, required): Identifier of the dataset.

#### Response Status
* `200 OK`: Returns dataset detailed metadata.
* `404 Not Found`: Dataset ID does not exist in local repository or cache.

---

### 3.12 `POST /api/ingestion/validate`

#### Purpose
Performs a dry-run validation of an NWP dataset against meteorological quality checks without writing to database or altering server state.

#### Request Body
```json
{
  "dataset_id": "gfs_sample_0p25_south_asia",
  "source_mode": "local",
  "lead_time_hours": 24
}
```

#### Response Status
* `200 OK`: Validation completed with pass/fail telemetry.

#### Response Body Example
```json
{
  "dataset_id": "gfs_sample_0p25_south_asia",
  "is_valid": true,
  "passed_checks": [
    "Grid dimensions consistent: (121, 121)",
    "Latitude strictly within [-90.0, 90.0]",
    "Longitude strictly within [-180.0, 180.0]",
    "Coordinates strictly monotonic",
    "Valid forecast time: valid_time >= init_time (lead: 24h)",
    "Temperature values strictly physically valid (min=-33.9°C, max=45.2°C)",
    "MSLP values strictly physically valid (min=975.2 hPa, max=1021.0 hPa)",
    "Wind components physically valid (max speed=36.7 m/s)",
    "Missing value fraction acceptable: 0.00%"
  ],
  "warnings": [],
  "errors": [],
  "variables_detected": [
    {
      "variable_name": "t2m",
      "canonical_name": "temperature",
      "original_units": "K",
      "canonical_units": "degC",
      "min_val": -33.91,
      "max_val": 45.21,
      "mean_val": 25.12,
      "is_valid": true
    }
  ],
  "missing_fields": [],
  "processing_duration_ms": 14.2
}
```

---

### 3.13 `POST /api/ingestion/run`

#### Purpose
Executes the full NWP ingestion pipeline: file parsing, unit normalization, coordinate standardisation, physics validation, and (optionally) runs the extreme anomaly detection pipeline on the ingested fields.

#### Request Body
```json
{
  "dataset_id": "gfs_sample_0p25_south_asia",
  "source_mode": "local",
  "cycle_date": "20260926",
  "cycle_hour": "00",
  "lead_time_hours": 24,
  "region_id": "south_asia",
  "variables": ["temperature", "wind", "mslp"],
  "run_anomaly_detection": true,
  "min_area_km2": 2500.0
}
```

#### Response Status
* `200 OK`: Ingestion and detection succeeded.
* `400 Bad Request`: Validation failure or unsupported parameters.
* `502 Bad Gateway`: Remote provider (NOAA NOMADS) unreachable or returned error.

#### Response Body Example
```json
{
  "success": true,
  "message": "NWP dataset 'gfs_sample_0p25_south_asia' successfully ingested and processed.",
  "dataset_id": "gfs_sample_0p25_south_asia",
  "data_source": "gfs_sample_0p25_south_asia.nc",
  "is_real_data": true,
  "data_provenance": "LOCAL_NWP_NETCDF",
  "validation_report": {
    "dataset_id": "gfs_sample_0p25_south_asia",
    "is_valid": true,
    "passed_checks": ["..."],
    "warnings": [],
    "errors": [],
    "variables_detected": ["..."],
    "missing_fields": [],
    "processing_duration_ms": 12.5
  },
  "anomalies_detected_count": 3,
  "footprints_extracted_count": 4,
  "anomalies": [
    {
      "id": "ANOM-REAL-001",
      "name": "Bay of Bengal Tropical Depression",
      "category_key": "cyclone",
      "severity": "High",
      "lat": 16.5,
      "lon": 87.2,
      "estimated_area_km2": 14280.0
    }
  ],
  "execution_time_ms": 48.7
}
```

---

### 3.14 `GET /api/ingestion/status`

#### Purpose
Reports the current status of the ingestion subsystem, the active data source in memory, and cached dataset metrics.

#### Query Parameters
*None.*

#### Response Body Example
```json
{
  "status": "ready",
  "active_data_source": "gfs_sample_0p25_south_asia.nc",
  "active_data_mode": "REAL_DATA",
  "last_ingested_dataset": "gfs_sample_0p25_south_asia",
  "last_ingestion_time": "2026-09-26T14:35:10Z",
  "cached_datasets_count": 2,
  "available_providers": [
    "NOAA NCEP Global Forecast System (GFS 0.25°)",
    "Local NWP File Provider (NetCDF4 / GRIB2)"
  ]
}
```

---

### 3.15 `GET /api/events/tracks`

#### Purpose
Enumerate all multi-horizon tracked anomaly series across forecast frames, summarizing net displacement, translation speed, and peak severity.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `category` | `string` | Optional | `null` | Filter by category (e.g. `cyclone`, `heat_wave`). |
| `min_detections` | `integer` | Optional | `null` | Minimum count of detected frames. |
| `status` | `string` | Optional | `null` | Filter by track status (`ACTIVE`, `DISSIPATED`, `INTERMITTENT`). |

#### Response Status
* `200 OK`: Returns array of `EventTrackSummary` objects.

#### Response Body Example
```json
[
  {
    "track_id": "TRK-CYC-001",
    "name": "Tropical Cyclone Vortex",
    "category": "cyclone",
    "hazard_type": "Tropical Cyclone",
    "first_detection_lead_hours": 24,
    "latest_detection_lead_hours": 120,
    "total_detections": 5,
    "total_frames": 10,
    "initial_centroid": [-12.4, 78.6],
    "latest_centroid": [-18.5, 71.0],
    "cumulative_distance_km": 1042.5,
    "net_displacement_km": 1042.5,
    "mean_speed_kmh": 10.9,
    "peak_magnitude": 150.0,
    "magnitude_unit": "km/h",
    "peak_severity": "High",
    "max_area_km2": 420000.0,
    "status": "ACTIVE",
    "trajectory_line": [[-12.4, 78.6], [-13.8, 77.1], [-15.2, 75.4], [-16.8, 73.5], [-18.5, 71.0]],
    "color": "#FF4568",
    "data_provenance": "DEMO_SYNTHETIC_DATASET",
    "is_simulated": true
  }
]
```

---

### 3.16 `GET /api/events/tracks/{track_id}`

#### Purpose
Retrieves comprehensive trajectory coordinates, metric history, area evolution, and scientific caveats for a track.

#### Path Parameters
* `track_id` (string, required): Unique track identifier (e.g. `TRK-CYC-001`).

#### Response Status
* `200 OK`: Returns `EventTrackDetail` object.
* `404 Not Found`: Track ID not found.

#### Response Body Example
```json
{
  "track_id": "TRK-CYC-001",
  "name": "Tropical Cyclone Vortex",
  "category": "cyclone",
  "hazard_type": "Tropical Cyclone",
  "first_detection_lead_hours": 24,
  "latest_detection_lead_hours": 120,
  "total_detections": 5,
  "total_frames": 10,
  "initial_centroid": [-12.4, 78.6],
  "latest_centroid": [-18.5, 71.0],
  "cumulative_distance_km": 1042.5,
  "net_displacement_km": 1042.5,
  "mean_speed_kmh": 10.9,
  "peak_magnitude": 150.0,
  "magnitude_unit": "km/h",
  "peak_severity": "High",
  "max_area_km2": 420000.0,
  "status": "ACTIVE",
  "trajectory_line": [[-12.4, 78.6], [-13.8, 77.1], [-15.2, 75.4], [-16.8, 73.5], [-18.5, 71.0]],
  "color": "#FF4568",
  "data_provenance": "DEMO_SYNTHETIC_DATASET",
  "is_simulated": true,
  "points": [
    {
      "frame_index": 0,
      "step_hours": 24,
      "forecast_day": 1,
      "valid_time": "2026-09-27T00:00:00Z",
      "detection_status": "DETECTED",
      "event_id": "EVT-CYC-F024",
      "centroid_lat": -12.4,
      "centroid_lon": 78.6,
      "coordinates_display": "12.4°S, 78.6°E",
      "estimated_area_km2": 320000.0,
      "max_magnitude": 126.0,
      "magnitude_unit": "km/h",
      "severity": "High",
      "displacement_km": null,
      "bearing_deg": null,
      "bearing_cardinal": null,
      "speed_kmh": null,
      "area_change_km2": null,
      "area_change_pct": null,
      "magnitude_change": null
    }
  ],
  "movement_notes": "Derived movement represents displacement of detected forecast footprint centroids across successive forecast frames; it does not constitute a verified physical storm track."
}
```

---

### 3.17 `GET /api/events/tracks/{track_id}/history`

#### Purpose
Retrieves the sequential array of `TrackPoint` objects (from Day 1 to Day 10) for a given track.

#### Path Parameters
* `track_id` (string, required): Track identifier.

#### Response Status
* `200 OK`: Returns array of `TrackPoint` objects.
* `404 Not Found`: Track ID not found.

---

### 3.18 `GET /api/uncertainty`

#### Purpose
Reports active uncertainty capability, mode (`DETERMINISTIC_ONLY` vs `ENSEMBLE_MEMBERS`), ensemble member count, and the 10-day atmospheric predictability skill decay schedule.

#### Query Parameters
| Parameter | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `dataset_id` | `string` | Optional | `null` | Active dataset identifier. |
| `mode` | `string` | Optional | `null` | Force mode: `ensemble` or `deterministic`. |

#### Response Status
* `200 OK`: Returns `UncertaintySummaryResponse`.

#### Response Body Example
```json
{
  "uncertainty_mode": "DETERMINISTIC_ONLY",
  "is_available": false,
  "ensemble_members_count": 1,
  "primary_provider": "NOAA NCEP GFS 0.25° (Deterministic Operational Run)",
  "message": "Ensemble spread is unavailable for single-member deterministic NWP forecasts. Predictability inherently decays with forecast lead time; confidence is evaluated using standardized synoptic error growth bands rather than fabricated ensemble variance.",
  "lead_time_decay": [
    {
      "day": 1,
      "step_hours": 24,
      "confidence_pct": 94.5,
      "confidence_level": "HIGH",
      "description": "High synoptic skill; tight deterministic bounds."
    },
    {
      "day": 5,
      "step_hours": 120,
      "confidence_pct": 62.5,
      "confidence_level": "MODERATE",
      "description": "Moderate confidence; increasing track spread."
    },
    {
      "day": 10,
      "step_hours": 240,
      "confidence_pct": 22.0,
      "confidence_level": "LOW_TREND_ONLY",
      "description": "Chaotic limit; qualitative medium-range outlook only."
    }
  ],
  "known_limitations": [
    "Single-run deterministic forecasts produce an individual deterministic trajectory without ensemble variance.",
    "Fixed physical thresholds do not quantify probabilistic risk or climatological return periods.",
    "Atmospheric predictability decays rapidly beyond Day 5 (120h lead time) due to non-linear chaos."
  ]
}
```

---

### 3.19 `GET /api/uncertainty/{event_id}`

#### Purpose
Retrieves event-specific uncertainty metrics: multi-member ensemble spread (if available, e.g. for `evt-001`) or deterministic confidence decay guidelines.

#### Path Parameters
* `event_id` (string, required): Event or track identifier (e.g. `evt-001` or `TRK-CYC-001`).

#### Response Status
* `200 OK`: Returns `EventUncertaintyDetail`.

---

### 3.20 `GET /api/models`

#### Purpose
List all registered anomaly models in the model registry, including version, status, and feature schema.

#### Response Body Example
```json
{
  "models": [
    {
      "model_id": "deterministic_baseline",
      "model_name": "Deterministic Physical Threshold Baseline",
      "version": "1.0.0",
      "model_type": "DETERMINISTIC_RULES",
      "status": "OPERATIONAL_BASELINE",
      "feature_schema_version": "v1.0.0",
      "is_operational": true,
      "description": "Standard 3-sigma climatological departures and physical barometric deficit thresholds.",
      "limitations": ["Fixed physical thresholds do not capture non-linear multi-variable interactions."]
    },
    {
      "model_id": "isolation_forest_v1",
      "model_name": "Experimental Isolation Forest Baseline",
      "version": "1.0.0",
      "model_type": "ISOLATION_FOREST",
      "status": "EXPERIMENTAL_SYNTHETIC_BENCHMARK",
      "feature_schema_version": "v1.0.0",
      "is_operational": false,
      "description": "Unsupervised tree-based spatial anomaly partitioner on normalized 8-dimensional feature vectors.",
      "limitations": ["Trained on synthetic demonstration perturbation grids; not validated for operational forecasting."]
    }
  ],
  "active_model_id": "deterministic_baseline",
  "timestamp": "2026-09-27T00:00:00Z"
}
```

---

### 3.21 `GET /api/models/status`

#### Purpose
Retrieve active model runtime status, operational mode, and data provenance.

---

### 3.22 `GET /api/models/{model_id}`

#### Purpose
Retrieve granular hyperparameters, feature schema, and scientific limitations for a specific model ID.

---

### 3.23 `POST /api/models/select`

#### Purpose
Switch the active inference model (e.g. between `deterministic_baseline` and `isolation_forest_v1`).

---

### 3.24 `GET /api/anomalies/{anomaly_id}/score`

#### Purpose
Return the multi-component normalized anomaly score and explainability breakdown for a catalog event.

#### Response Body Example
```json
{
  "event_id": "evt-001",
  "composite_score": 0.824,
  "overall_score_100": 82.4,
  "severity_tier": "High",
  "is_probability": false,
  "primary_contributing_variables": ["Wind Speed", "Pressure Deficit"],
  "components": {
    "thermal_deviation": { "normalized_score": 0.42, "weight": 0.25, "contribution_percent": 12.8 },
    "wind_magnitude": { "normalized_score": 0.88, "weight": 0.20, "contribution_percent": 21.5 },
    "pressure_deficit": { "normalized_score": 0.84, "weight": 0.20, "contribution_percent": 20.5 },
    "spatial_extent": { "normalized_score": 0.76, "weight": 0.15, "contribution_percent": 13.9 },
    "temporal_persistence": { "normalized_score": 1.00, "weight": 0.10, "contribution_percent": 12.2 },
    "data_quality": { "normalized_score": 1.00, "weight": 0.10, "contribution_percent": 12.2 }
  },
  "detection_method": "NORMALIZED_MULTI_CRITERIA_SCORER_V1",
  "score_interpretation": "Anomaly index of 82.4/100 classifies as 'High' severity tier.",
  "score_limitations": [
    "Score represents an empirical multi-criteria departure index; it is NOT a calibrated probability of disaster."
  ]
}
```

---

### 3.25 `POST /api/scoring/compute`

#### Purpose
Compute normalized composite anomaly scores on arbitrary custom physical parameters and custom component weights.

---

### 3.26 `GET /api/evaluation`

#### Purpose
Return scientific benchmark metrics (Precision, Recall, F1, FPR, IoU, Latency, Confusion Matrix) evaluating models against synthetic ground-truth masks.

---

### 3.27 `GET /api/uncertainty/series`

#### Purpose
Retrieve multi-lead-time forecast uncertainty dispersion series (ensemble mean, std, p10–p90 quantiles) or deterministic unavailable empty state.



