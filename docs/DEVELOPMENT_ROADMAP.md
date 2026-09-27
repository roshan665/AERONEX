# AeroNex: Development Roadmap & Milestone Execution Plan

[![Roadmap Stage](https://img.shields.io/badge/Roadmap-9--Phase%20Milestones-blue.svg)]()
[![Hackathon Focus](https://img.shields.io/badge/SIH-Ready%20Sprint-orange.svg)]()
[![Current Status](https://img.shields.io/badge/Current-Phase%201%20Complete-green.svg)]()

This document outlines the structured 9-phase development schedule for **AeroNex**, designed for execution during the Smart India Hackathon. It details objectives, deliverables, dependencies, acceptance criteria, and risk mitigations for each milestone.

---

## 1. High-Level Milestone Roadmap

```mermaid
gantt
    title AeroNex Implementation Schedule (Phases 1 to 9)
    dateFormat  X
    axisFormat  Day %d

    section Foundations
    Phase 1: Architecture & Technical Specs   :done, p1, 0, 1
    Phase 2: UI Foundation & Dashboard Shell   :active, p2, 1, 3
    Phase 3: FastAPI Backend & Schemas         :p3, 2, 4

    section Scientific Pipeline
    Phase 4: Synthetic Data Pipeline           :p4, 3, 5
    Phase 5: Anomaly Detection Baseline        :p5, 4, 6
    Phase 6: Footprint Extraction & GeoJSON    :p6, 5, 7

    section Integration & Delivery
    Phase 7: Full System Integration           :p7, 6, 8
    Phase 8: Testing & Scientific Validation   :p8, 7, 9
    Phase 9: Demo Polishing & SIH Presentation :p9, 8, 10
```

---

## 2. Phase-by-Phase Implementation Blueprint

---

### Phase 1: Documentation & System Architecture
* **Status**: **COMPLETED**
* **Primary Objective**: Establish the complete engineering blueprint, scientific methodology, API contract, and requirements baseline prior to writing source code.
* **Key Deliverables**:
  * [README.md](file:///d:/msi/SIH_26078/README.md)
  * [docs/PROJECT_REQUIREMENTS.md](file:///d:/msi/SIH_26078/docs/PROJECT_REQUIREMENTS.md)
  * [docs/SYSTEM_ARCHITECTURE.md](file:///d:/msi/SIH_26078/docs/SYSTEM_ARCHITECTURE.md)
  * [docs/DATA_STRATEGY.md](file:///d:/msi/SIH_26078/docs/DATA_STRATEGY.md)
  * [docs/ANOMALY_DETECTION.md](file:///d:/msi/SIH_26078/docs/ANOMALY_DETECTION.md)
  * [docs/API_SPECIFICATION.md](file:///d:/msi/SIH_26078/docs/API_SPECIFICATION.md)
  * [docs/UI_UX_SPECIFICATION.md](file:///d:/msi/SIH_26078/docs/UI_UX_SPECIFICATION.md)
  * [docs/TESTING_AND_VALIDATION.md](file:///d:/msi/SIH_26078/docs/TESTING_AND_VALIDATION.md)
  * [docs/DEVELOPMENT_ROADMAP.md](file:///d:/msi/SIH_26078/docs/DEVELOPMENT_ROADMAP.md)
* **Acceptance Criteria**: All 9 documents written, peer-consistent, adhering to scientific transparency and zero-fabrication rules.

---

### Phase 2: UI Foundation & Dashboard Shell
* **Status**: **NEXT UP (Planned)**
* **Primary Objective**: Initialize the React + Vite frontend workspace, configure Tailwind CSS design tokens, build the application shell, and mount the Leaflet map viewport.
* **Key Deliverables**:
  * Initialized `frontend/` directory with Vite, React 18, and Tailwind CSS.
  * Dark navy scientific theme configured in `tailwind.config.js` and `index.css`.
  * Top navigation bar with region selector, provenance indicator, and live UTC clock.
  * Persistent left sidebar navigation dock with route transitions.
  * Base Leaflet map canvas rendering CartoDB Dark Matter tiles.
  * Responsive layout breakpoints ($<768px, 1024px, \ge 1280px$).
* **Dependencies**: Completion of Phase 1 specifications.
* **Acceptance Criteria**: Clean UI build with zero console warnings; map pans and zooms smoothly; sidebar and layout adapt across desktop and mobile.
* **Risk & Mitigation**: Leaflet CSS asset loading issues in Vite $\rightarrow$ Explicitly import `leaflet/dist/leaflet.css` in `main.jsx` and configure base tile fallback.

---

### Phase 3: FastAPI Backend & Data Schemas
* **Status**: **Planned**
* **Primary Objective**: Initialize the Python FastAPI application, configure CORS and routing middleware, and implement strict Pydantic v2 schemas for all API payloads.
* **Key Deliverables**:
  * Initialized `backend/` directory with `requirements.txt` (`fastapi`, `uvicorn`, `pydantic`, `numpy`, `xarray`, `scipy`, `shapely`).
  * Pydantic schemas for `AnomalyEvent`, `GeoJsonFeatureCollection`, `ForecastSlice`, `OverviewSummary`, and RFC 7807 error envelopes.
  * Modular router scaffolding for `/health`, `/overview`, `/forecasts`, `/anomalies`, `/map/layers`, `/regions`, and `/metadata`.
* **Dependencies**: `docs/API_SPECIFICATION.md`.
* **Acceptance Criteria**: `uvicorn` boots up cleanly on port 8000; `/docs` renders Swagger UI with all schemas; mock responses validate against Pydantic models.
* **Risk & Mitigation**: Incompatible Pydantic v1 vs v2 methods $\rightarrow$ Standardize strictly on Pydantic v2 (`model_validate`, `field_validator`).

---

### Phase 4: Synthetic Weather-Data Pipeline & Mock Engine
* **Status**: **Planned**
* **Primary Objective**: Build a deterministic synthetic data generator producing multi-variable, multi-timestep gridded NetCDF4 and JSON datasets with realistic extreme weather events.
* **Key Deliverables**:
  * Script `backend/app/services/data_generator.py` generating $0.25^\circ$ resolution grids.
  * Synthetic scenarios:
    1. Bay of Bengal Severe Tropical Cyclone ($T+0h$ to $T+120h$ northwest track).
    2. Northern Plains Severe Heat Dome ($T+24h$ to $T+168h$).
    3. Himalayan Cold Wave plunge.
  * Pre-computed 30-year daily climatological normal baselines ($\mu_{clim}, \sigma_{clim}$).
  * Unit tests validating physical sanity of synthetic fields.
* **Dependencies**: Phase 3 schemas.
* **Acceptance Criteria**: Generator creates valid NetCDF4/JSON files within $< 5\ s$; values conform to physical bounds ($MSLP \in [950, 1030]\ hPa$, $T_{2m} \in [-15, 48]^\circ C$).
* **Risk & Mitigation**: Gridded array sizes too large for memory $\rightarrow$ Restrict prototype grid to South Asia bounding box ($[5^\circ N, 40^\circ N] \times [60^\circ E, 100^\circ E]$) at $0.25^\circ$ spacing.

---

### Phase 5: Anomaly Detection Baseline
* **Status**: **Planned**
* **Primary Objective**: Implement the core statistical and physical anomaly detection algorithms in the Python backend.
* **Key Deliverables**:
  * `anomaly_service.py` implementing:
    * Climatological $Z$-score calculation: $Z = (X - \mu) / \sigma$.
    * Configurable physical threshold evaluation.
    * Composite binary anomaly mask generation.
  * Unit test suite verifying threshold edge cases and zero-division handling.
* **Dependencies**: Phase 4 gridded data.
* **Acceptance Criteria**: Script accurately isolates the cyclone center and heatwave core as boolean masks across all timesteps.
* **Risk & Mitigation**: False positives over elevated terrain $\rightarrow$ Apply sea-level pressure correction or elevation mask.

---

### Phase 6: Geographic Footprint Extraction & GeoJSON Integration
* **Status**: **Planned**
* **Primary Objective**: Implement spatial connected-component labeling and polygonization to transform boolean matrices into Leaflet-ready GeoJSON polygons.
* **Key Deliverables**:
  * `footprint_service.py` using `scipy.ndimage.label` (8-connectivity) and `shapely.geometry.Polygon`.
  * Cosine-latitude area integration ($km^2$).
  * Centroid and bounding-box computation.
  * Douglas-Peucker polygon simplification ($\epsilon = 0.05^\circ$).
  * Severity classification tagger (`ADVISORY`, `MODERATE`, `SEVERE`, `EXTREME`).
* **Dependencies**: Phase 5 anomaly masks.
* **Acceptance Criteria**: GeoJSON FeatureCollection serializes cleanly, passes RFC 7946 validation, and renders closed polygons with accurate surface areas.
* **Risk & Mitigation**: Complex multi-part polygons causing Leaflet render artifacts $\rightarrow$ Explicitly decompose into `MultiPolygon` or separate `Polygon` features.

---

### Phase 7: Frontend/Backend Integration & End-to-End Flow
* **Status**: **Planned**
* **Primary Objective**: Connect the React frontend to the live FastAPI backend, enabling dynamic time scrubbing, interactive polygon inspection, and uncertainty charting.
* **Key Deliverables**:
  * API service layer (`frontend/src/services/api.js`) communicating with backend endpoints.
  * Time scrubber component driving synchronous map and chart updates across $T+0h \dots T+240h$.
  * Click-to-inspect popovers on the Leaflet map displaying live variable values.
  * Recharts forecast explorer graphing 10-day trends with shaded uncertainty bands.
  * Telemetry drawer displaying selected anomaly diagnostics.
* **Dependencies**: Phases 2, 3, 5, 6.
* **Acceptance Criteria**: Adjusting the time slider updates the map polygon locations, KPIs, and chart curves in under $< 300\ ms$ without page refresh.
* **Risk & Mitigation**: CORS or network latency lag during slider scrubbing $\rightarrow$ Debounce slider inputs (100ms) and cache active timestep data in client memory.

---

### Phase 8: Testing & Scientific Validation
* **Status**: **Planned**
* **Primary Objective**: Execute the comprehensive test plan specified in `docs/TESTING_AND_VALIDATION.md`, verifying numerical accuracy, physical sanity, and API contract compliance.
* **Key Deliverables**:
  * Automated `pytest` suite covering unit and integration tests.
  * Vitest suite testing frontend state and UI component interactions.
  * Benchmark evaluation recording IoU overlap, precision, recall, and detection latency against synthetic ground truth.
  * Test results summary artifact.
* **Dependencies**: Phase 7 completed system.
* **Acceptance Criteria**: $100\%$ pass rate on API contract tests; target IoU $\ge 0.75$; zero unhandled runtime exceptions.

---

### Phase 9: Demo Preparation & SIH Presentation
* **Status**: **Planned**
* **Primary Objective**: Prepare an irresistible, high-impact demonstration package for the Smart India Hackathon jury.
* **Key Deliverables**:
  * Fully self-contained offline demo bundle (operable without live internet).
  * 3-minute executive elevator pitch script highlighting the problem statement, scientific rigor, and operational utility for disaster management.
  * Demonstration script walking evaluators through the 3 simulated disaster scenarios (Cyclone, Heatwave, Coldwave).
  * High-resolution architecture slides and interactive walkthrough video.
* **Dependencies**: Phase 8 validated application.
* **Acceptance Criteria**: The demonstration runs flawlessly in under 5 minutes, clearly highlighting the distinction between baseline anomaly detection, forecast exploration, and uncertainty communication.
