# AeroNex: System Architecture & Engineering Blueprint

[![Architecture Layer](https://img.shields.io/badge/Architecture-Service--Oriented-blue.svg)]()
[![Backend](https://img.shields.io/badge/Backend-FastAPI-teal.svg)](https://fastapi.tiangolo.com)
[![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-purple.svg)](https://vitejs.dev)
[![Geospatial](https://img.shields.io/badge/Geospatial-Leaflet%20%2B%20GeoJSON-green.svg)](https://leafletjs.com)

This document provides a comprehensive architectural breakdown of the **AeroNex** platform, detailing its component hierarchy, communication contracts, geospatial processing pipelines, data storage models, and deployment topology.

---

## 1. Architectural Overview & Component Hierarchy

AeroNex is structured as a decoupled, service-oriented system designed to separate computationally intensive multidimensional scientific operations from interactive geospatial client rendering.

```mermaid
flowchart TD
    subgraph Client_Tier ["Client Tier (React 18 + Vite)"]
        UI_Dash["Dashboard & KPIs View"]
        UI_Map["Interactive Weather Map (Leaflet)"]
        UI_Chart["Forecast Explorer & Uncertainty Charts (Recharts)"]
        UI_Alerts["Alerts & Event Drawer"]
        State_Mgr["Client State & Filter Context"]
        API_Client["API Service Layer (Axios / Fetch)"]

        UI_Dash --> State_Mgr
        UI_Map --> State_Mgr
        UI_Chart --> State_Mgr
        UI_Alerts --> State_Mgr
        State_Mgr <--> API_Client
    end

    subgraph API_Gateway ["Application API Gateway (FastAPI)"]
        Router["FastAPI Router (/api/v1)"]
        Middleware["CORS / Error Handler / Logging Middleware"]
        Pydantic["Schema Serialization & Validation (Pydantic v2)"]

        Router --> Middleware
        Router --> Pydantic
    end

    subgraph Service_Tier ["Application Services Tier (Python 3.11)"]
        Overview_Svc["Overview & Summary Service"]
        Forecast_Svc["Forecast Query Service"]
        Anomaly_Svc["Anomaly Detection Orchestrator"]
        Footprint_Svc["Geospatial Footprint Engine"]
        Metadata_Svc["Metadata & Region Service"]
    end

    subgraph Processing_Engine ["Scientific Computing & Spatial Core"]
        Xarray_Engine["Gridded Array Processing (Xarray + NumPy)"]
        ZScore_Calc["Climatological Z-Score & Threshold Engine"]
        Spatial_Clust["Connected-Component Labeling (SciPy ndimage)"]
        Vector_Poly["Polygonization & Centroid Engine (Shapely)"]
    end

    subgraph Storage_Tier ["Storage & Data Persistence"]
        subgraph Stage_1 ["Stage 1: Prototype Storage"]
            NetCDF_Store["NetCDF-4 / Zarr Gridded Store"]
            JSON_Cache["Precomputed GeoJSON & Event Catalog"]
        end
        subgraph Stage_2 ["Stage 2: Target Operational Storage"]
            PostgreSQL["PostgreSQL 16 + PostGIS 3.4"]
            Tile_Cache["Vector / Raster Tile Server"]
        end
    end

    API_Client <== "HTTPS / JSON / GeoJSON" ==> Router
    Router --> Overview_Svc
    Router --> Forecast_Svc
    Router --> Anomaly_Svc
    Router --> Footprint_Svc
    Router --> Metadata_Svc

    Forecast_Svc --> Xarray_Engine
    Anomaly_Svc --> ZScore_Calc
    ZScore_Calc --> Xarray_Engine
    Anomaly_Svc --> Spatial_Clust
    Footprint_Svc --> Spatial_Clust
    Spatial_Clust --> Vector_Poly

    Xarray_Engine <--> NetCDF_Store
    Spatial_Clust <--> JSON_Cache
    Vector_Poly <--> JSON_Cache
    Stage_1 -.-> Stage_2
```

---

## 2. Component Responsibilities

### 2.1 Client Tier (React 18 + Vite)
* **Application Shell & Navigation**: Hosts the persistent sidebar, top status bar, and dynamic route routing via `React Router v6`.
* **Geospatial Map Rendering**: Powered by Leaflet/React-Leaflet, managing multiple map panes:
  * Base CartoDB Dark Matter / OpenStreetMap tiles.
  * Gridded raster or semi-transparent scalar contour layers.
  * Vector GeoJSON polygons representing anomaly footprints with dynamic styling based on hazard type and severity.
* **Forecast & Uncertainty Visualizer**: Interactive time-series visualizer powered by Recharts, plotting variable forecasts across 1-10 day horizons, with shaded confidence envelopes and baseline comparisons.
* **Client State & Cache**: Coordinates active timestep ($T+0h \dots T+240h$), selected region, active variables, and detection sensitivity thresholds across all views.

### 2.2 API Gateway & Router (FastAPI)
* **Request Validation**: Enforces strict typing on query parameters (e.g., bounding boxes, forecast lead times, variable names) via Pydantic v2 schemas.
* **Response Serialization**: Serializes analytical payloads into clean JSON and valid GeoJSON FeatureCollections (`RFC 7946`).
* **Error Handling**: Intercepts unhandled exceptions and validation errors, transforming them into RFC 7807 problem details.
* **CORS & Compression**: Manages cross-origin resource access for local frontend development and applies Gzip compression to large coordinate arrays.

### 2.3 Application Services Tier
* **Overview & Summary Service (`overview_service.py`)**: Computes real-time situational summaries: active anomaly count, severe alerts, monitored boundaries, and dataset metadata.
* **Forecast Service (`forecast_service.py`)**: Queries multidimensional slices for specific coordinates or bounding boxes across forecast lead times.
* **Anomaly Detection Service (`anomaly_service.py`)**: Coordinates the execution of threshold filtering and statistical z-score evaluation on ingested variable arrays.
* **Geospatial Footprint Service (`footprint_service.py`)**: Transforms 2D boolean anomaly matrices into continuous spatial polygons, calculates centroids, bounding boxes, and surface areas ($km^2$).
* **Metadata & Region Service (`metadata_service.py`)**: Supplies boundary definitions for administrative regions (e.g., Bay of Bengal, Arabian Sea, Northern Plains) and variable descriptions.

### 2.4 Scientific Processing Engine
* **Xarray & NumPy Core**: Slices, interpolates, and resamples 3D/4D arrays `(time, step, lat, lon)` with memory-efficient chunking.
* **SciPy ndimage**: Applies binary morphology and connected-component labeling (`scipy.ndimage.label`) to identify contiguous clusters of anomalous cells.
* **Shapely**: Handles geometric operations: polygon union, coordinate transformation, convex/concave hull wrapping, centroid computation, and area calculation using spherical approximations.

---

## 3. End-to-End Data Flow Sequence

The following sequence details how a user interaction triggers data retrieval, spatial processing, and vector rendering:

```mermaid
sequenceDiagram
    autonumber
    actor User as Disaster Analyst
    participant UI as React UI (Map View)
    participant API as FastAPI Router
    participant Svc as Anomaly / Footprint Svc
    participant Sci as SciPy / Shapely Engine
    participant Store as NetCDF / Cache Store

    User->>UI: Selects "Cyclonic Depression", Step = T+48h
    UI->>API: GET /api/v1/anomalies?variable=mslp&step=48&threshold=990
    API->>Svc: evaluate_anomalies(variable='mslp', step=48, threshold=990)
    Svc->>Store: load_slice(variable='mslp', step=48)
    Store-->>Svc: 2D Array [lat, lon]
    Svc->>Sci: compute_mask(array < 990 hPa)
    Sci-->>Svc: Binary Mask Matrix
    Svc->>Sci: label_connected_components(mask, min_cells=10)
    Sci->>Sci: polygonize_clusters(labeled_grid)
    Sci->>Sci: compute_centroids_and_areas(polygons)
    Sci-->>Svc: List of Georeferenced Footprints
    Svc-->>API: List[AnomalyEvent] + GeoJSON FeatureCollection
    API-->>UI: 200 OK (JSON Payload + GeoJSON)
    UI->>UI: Update Leaflet GeoJSON Pane
    UI->>UI: Recenter Map & Highlight Bounding Box
    UI-->>User: Visual Footprint Displayed with Severity Badge
```

---

## 4. Detailed Data Processing Stages

```mermaid
graph LR
    subgraph S1 ["1. Ingestion"]
        A1["Raw GRIB2 / NetCDF / Synthetic"] --> A2["Coordinate Harmonization (0-360 to -180..180)"]
    end

    subgraph S2 ["2. Standardization"]
        A2 --> B1["Unit Conversion (K to °C, Pa to hPa)"]
        B1 --> B2["Missing Value Interpolation / Masking"]
    end

    subgraph S3 ["3. Anomaly Analysis"]
        B2 --> C1["Z-Score against Climatology"]
        B2 --> C2["Physical Threshold Filter"]
        C1 & C2 --> C3["Composite Anomaly Binary Mask"]
    end

    subgraph S4 ["4. Spatial Vectorization"]
        C3 --> D1["Connected Component Labeling"]
        D1 --> D2["Noise Filtering (< Min Area)"]
        D2 --> D3["Vector Polygonization (GeoJSON)"]
    end

    subgraph S5 ["5. Delivery"]
        D3 --> E1["REST API Payload"]
        E1 --> E2["Client Leaflet Map Rendering"]
    end
```

### Stage 1: Ingestion & Spatial Alignment
* Standardizes coordinate axes to increasing latitude $[-90, 90]$ and standard longitude $[-180, 180]$.
* Aligns multi-variable grids to a common spatial reference resolution (e.g., $0.25^\circ \times 0.25^\circ$).

### Stage 2: Physical Standardization
* Normalizes thermodynamic units: Kelvin ($K$) converted to Celsius ($^\circ C$).
* Normalizes barometric units: Pascals ($Pa$) converted to hectopascals ($hPa$).
* Derives scalar wind speed from orthogonal components: $WS = \sqrt{u_{10}^2 + v_{10}^2}$.

### Stage 3: Anomaly Mask Generation
* Computes dual-criteria masks:
  1. *Statistical Criterion*: Standard deviation departure: $Z_{lat,lon} \ge Z_{crit}$.
  2. *Physical Criterion*: Hard meteorological limit: e.g., $MSLP \le 992\ hPa$.
* Merges masks using logical operations (`AND` or `OR` depending on hazard profile).

### Stage 4: Spatial Clustering & Vectorization
* Evaluates 8-neighbor connectivity to identify cohesive regional weather systems.
* Discards isolated noise cells with surface area $< 2,500\ km^2$.
* Computes bounding box $[minLon, minLat, maxLon, maxLat]$ and geometric centroid $(\bar{\lambda}, \bar{\phi})$.
* Encodes the spatial boundary into GeoJSON `Polygon` or `MultiPolygon` format.

---

## 5. Storage Architecture & Evolution

```mermaid
classDiagram
    class AnomalyEventRecord {
        +String event_id
        +String hazard_type
        +String severity
        +Float max_metric_value
        +Float mean_z_score
        +Int forecast_step_hours
        +DateTime valid_time_utc
        +Float centroid_lat
        +Float centroid_lon
        +Float area_km2
        +GeoJSON geometry
    }

    class ForecastSliceRecord {
        +String forecast_id
        +DateTime model_run_utc
        +Int step_hours
        +DateTime valid_time_utc
        +String variable_name
        +String unit
        +GridBounds bounds
        +List data_grid
    }

    class RegionCatalogRecord {
        +String region_id
        +String name
        +Float min_lat
        +Float max_lat
        +Float min_lon
        +Float max_lon
        +Boolean monitored
    }

    AnomalyEventRecord --> RegionCatalogRecord : falls_within
    ForecastSliceRecord --> AnomalyEventRecord : generated_from
```

### Stage 1: Prototype Implementation (Current Hackathon Scope)
* **File-Based Gridded Storage**: Structured NetCDF-4 (`.nc`) files or high-speed compressed JSON files stored in `backend/data/`.
* **In-Memory Cache**: Python in-memory dictionaries and LRU caching (`functools.lru_cache`) for pre-computed anomaly catalogs and GeoJSON footprints.
* **Benefits**: Zero database installation friction; instantaneous spin-up; 100% reproducible for evaluators without cloud infrastructure.

### Stage 2: Operational Target Architecture (Post-Hackathon Expansion)
* **Database Engine**: PostgreSQL 16 with the PostGIS 3.4 spatial extension.
* **Spatial Indexing**: GiST indices on geography columns for sub-millisecond bounding box queries and polygon clipping.
* **Tiling Engine**: Dynamic vector tile server (e.g., Martin or Tegola) delivering Mapbox Vector Tiles (`MVT`) for multi-million cell datasets.
* **Object Store**: AWS S3 or MinIO for raw GRIB2/Zarr meteorological archive.

---

## 6. Error Handling & System Resilience

1. **Input Range Guardrails**: If an incoming query specifies coordinates outside valid ranges (e.g., $Lat = 110^\circ$) or a forecast step exceeding model horizons, FastAPI raises a structured `422 Unprocessable Entity` with exact parameter paths.
2. **Missing Variable Fallback**: If an optional variable (e.g., vertical wind shear) is unavailable in the active dataset, the anomaly engine flags the result as `PARTIAL_EVALUATION` rather than aborting.
3. **Spatial Singularities**: Longitudinal transitions at $180^\circ$ and polar coordinate compression are handled gracefully by wrapping longitudes to the $[-180, 180]$ domain before spatial grouping.
4. **Client-Side Graceful Degradation**: If the backend API encounters an unhandled exception ($500$), the React UI renders an inline fallback card with a "Retry Analysis" button, keeping the rest of the dashboard functional.

---

## 7. Deployment Concept

```mermaid
graph TD
    subgraph Local_Dev ["Local Development Environment (Current)"]
        DEV_VITE["Vite Dev Server (Port 5173)"]
        DEV_UVICORN["Uvicorn ASGI Server (Port 8000)"]
        DEV_FILES["Local Data Directory (/backend/data)"]

        DEV_VITE <== "Proxy /api" ==> DEV_UVICORN
        DEV_UVICORN <--> DEV_FILES
    end

    subgraph Container_Target ["Target Production Containerization (Docker Compose)"]
        NGINX["Reverse Proxy (Nginx / Caddy)"]
        WEB_CONT["Frontend Static Container"]
        API_CONT["FastAPI ASGI Container (Gunicorn + Uvicorn Workers)"]
        VOL_DATA["Shared NWP Volume (/data/nwp)"]

        NGINX --> WEB_CONT
        NGINX --> API_CONT
        API_CONT <--> VOL_DATA
    end
```

* **Local Development**: Fast iteration with Vite HMR on `localhost:5173` proxying API requests to FastAPI/Uvicorn on `localhost:8000`.
* **Production Packaging**: Single-command execution via `docker-compose.yml` hosting multi-stage frontend builds served by Nginx alongside a containerized Python scientific runtime.
