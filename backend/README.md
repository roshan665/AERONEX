# AeroNex Backend Services (FastAPI)

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141.1-teal.svg)](https://fastapi.tiangolo.com)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2.13-red.svg)](https://docs.pydantic.dev)
[![Tests](https://img.shields.io/badge/Pytest-27%20Passed-brightgreen.svg)]()

The backend engine for **AeroNex** provides high-performance REST APIs delivering Numerical Weather Prediction (NWP) anomaly records, geographic footprints, and 10-day forecast uncertainty envelopes.

> [!IMPORTANT]
> **Demonstration Data Notice**: All weather anomalies, cyclone footprints, and time-series forecasts served by this backend are simulated demonstration data generated for the Smart India Hackathon prototype. They do NOT represent live operational weather alerts or official government predictions.

---

## 1. Directory Structure

```text
backend/
├── app/
│   ├── main.py                     # FastAPI application entry point, CORS & RFC 7807 handlers
│   ├── core/
│   │   ├── config.py               # Global settings, CORS origins & provenance flags
│   │   └── logging.py              # Structured logging configuration
│   ├── api/
│   │   ├── router.py               # API router prefixing /api
│   │   └── routes/
│   │       ├── health.py           # GET /api/health
│   │       ├── overview.py         # GET /api/overview
│   │       ├── forecasts.py        # GET /api/forecasts, GET /api/forecasts/{id}
│   │       ├── anomalies.py        # GET /api/anomalies, GET /api/anomalies/{id}
│   │       ├── map.py              # GET /api/map/layers
│   │       ├── regions.py          # GET /api/regions, GET /api/regions/{id}
│   │       └── metadata.py         # GET /api/metadata
│   ├── models/
│   │   ├── common.py               # Coordinates, BoundingBox & ErrorResponse (RFC 7807)
│   │   ├── overview.py             # DashboardCard, CriticalAlertItem, OverviewResponse
│   │   ├── anomaly.py              # AnomalyEvent, AnomalyDetailResponse, TrajectoryStep
│   │   ├── forecast.py             # ForecastTimelineItem, ForecastResponse, RunMetadata
│   │   └── map.py                  # MapLayerDescriptor, GeoJsonFeatureCollection
│   ├── services/
│   │   ├── overview_service.py     # Aggregates KPI cards and severity distributions
│   │   ├── anomaly_service.py      # Filters and retrieves anomaly events
│   │   ├── forecast_service.py     # Multi-variable time-series slicing
│   │   ├── map_service.py          # RFC 7946 GeoJSON vector polygon builder
│   │   └── region_service.py       # Monitored spatial sector registry
│   └── data/
│       └── demo_data.py            # Centralized single source of truth for demo data
├── tests/                          # 27 automated Pytest unit and consistency tests
├── requirements.txt                # Production and development dependencies
└── README.md                       # Backend documentation and running instructions
```

---

## 2. API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Root service info, status, and API documentation links |
| `GET` | `/api/health` | Liveness probe, uptime, and subsystem health status |
| `GET` | `/api/overview` | Executive KPI cards, active anomaly count, severity distribution, and critical alerts |
| `GET` | `/api/forecasts` | 10-day time-series and ensemble spread for temperature, wind, pressure, precipitation |
| `GET` | `/api/forecasts/{forecast_id}` | Detailed NWP grid resolution and lead time descriptors |
| `GET` | `/api/anomalies` | Filterable catalog of extreme weather anomalies (category, severity, region, lead day) |
| `GET` | `/api/anomalies/{anomaly_id}` | Granular diagnostic metrics, closed boundary contours, and forecast tracks |
| `GET` | `/api/map/layers` | Leaflet layer configurations and RFC 7946 GeoJSON FeatureCollections |
| `GET` | `/api/regions` | Predefined demonstration monitoring sectors and bounding boxes |
| `GET` | `/api/regions/{region_id}` | Geographic bounding box and center coordinates for a single sector |
| `GET` | `/api/metadata` | Dataset provenance, spatial resolution, and scientific methodology references |

Interactive Swagger documentation is available at: **`http://localhost:8000/docs`**  
ReDoc documentation is available at: **`http://localhost:8000/redoc`**

---

## 3. Setup and Running Instructions

### 3.1 Prerequisites
* Python 3.11 or 3.12 (CPython)
* `uv` or standard Python `venv`

### 3.2 Installation
```powershell
# Navigate to backend directory
cd backend

# Create virtual environment (using Python 3.12)
uv venv .venv --python 3.12
# Or: py -3.12 -m venv .venv

# Install dependencies
.\.venv\Scripts\pip install -r requirements.txt
# Or with uv:
uv pip install -r requirements.txt --python .venv/Scripts/python.exe
```

### 3.3 Start Development Server
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The server will boot on `http://localhost:8000`.

### 3.4 Running the Test Suite
```powershell
.\.venv\Scripts\pytest.exe tests/ -v
```
All 27 automated tests covering health, overview, forecasts, anomalies, GeoJSON coordinates, regions, error handling, and cross-endpoint consistency will execute.
