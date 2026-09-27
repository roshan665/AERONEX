# AeroNex: Project Requirements & System Specification

[![Document Version](https://img.shields.io/badge/Version-1.0.0-blue.svg)]()
[![Status](https://img.shields.io/badge/Status-Implementation--Ready-green.svg)]()
[![Related Architecture](https://img.shields.io/badge/Architecture-docs%2FSYSTEM__ARCHITECTURE.md-informational.svg)](file:///d:/msi/SIH_26078/docs/SYSTEM_ARCHITECTURE.md)

This document establishes the formal requirements baseline for the **AeroNex** meteorological intelligence platform. It outlines functional capabilities, non-functional constraints, user roles, operational risks, and formal acceptance criteria for the Smart India Hackathon implementation.

---

## 1. User Roles & Personas

The platform serves four primary stakeholder profiles, each with distinct operational workflows and data consumption requirements:

| Persona | Role Description | Primary Goal in AeroNex | Critical Platform Needs |
| :--- | :--- | :--- | :--- |
| **Disaster Management Analyst** (e.g., NDRF, SDMA) | Emergency operational planner responsible for issuing early warnings and resource pre-positioning. | Rapidly identify geographic zones at risk of extreme cyclones, flash floods, or deadly heatwaves over a 3-7 day horizon. | High-contrast polygon footprint overlays, administrative boundary clipping, severity categories, clear alert feeds. |
| **Meteorological Data Analyst / Researcher** | Atmospheric scientist studying mesoscale weather systems and climate extremes. | Investigate physical anomalies across multiple variable fields (MSLP, Wind, Temperature) and evaluate forecast consistency. | Numerical readouts, multi-lead time stepping, z-score thresholds, climatological reference context, raw data export. |
| **Hackathon Evaluator / Academic Reviewer** | Technical jury assessing scientific validity, engineering rigor, code quality, and UX clarity. | Validate that the end-to-end pipeline operates reliably, communicates uncertainty honestly, and solves the problem statement. | Fast interactive demo, clear scientific explanation, transparent uncertainty boundaries, well-documented architecture. |
| **General Spatial Explorer / Student** | Learner or enthusiast exploring regional meteorology. | Understand how weather forecasts evolve over time and visualize atmospheric disturbances interactively. | Intuitive map controls, accessible color palettes, responsive web design, explanatory tooltips. |

---

## 2. Functional Requirements (FR)

### Module A: Overview Dashboard
* **FR-A1 (Global Summary KPIs)**: The system shall display aggregated key metrics including Total Active Anomalies, Monitored Geographic Regions, Maximum Forecast Horizon (e.g., Day 1 to Day 10), and the Latest NWP Ingestion Timestamp.
* **FR-A2 (Recent Alerts Feed)**: The system shall provide an alert feed highlighting recently detected high-severity anomalies, ordered chronologically or by severity.
* **FR-A3 (Dataset Provenance Banner)**: The system shall clearly indicate the active data mode (e.g., `DEMO_SYNTHETIC` vs. `LIVE_NWP_GFS`) to maintain scientific transparency.
* **FR-A4 (Quick Navigation)**: Users shall be able to click any alert card or regional summary to immediately navigate to that event's coordinates in the Interactive Weather Map.

### Module B: Interactive Weather Map
* **FR-B1 (Geospatial Base Canvas)**: The platform shall render a high-performance Leaflet-based map with smooth pan, zoom, and bounding-box constraints.
* **FR-B2 (Continuous Weather Layers)**: The map shall support toggling raster/contour overlay layers for primary meteorological variables:
  * 2m Temperature ($T_{2m}$, in °C)
  * 10m Wind Speed ($WS_{10}$, in $m/s$ or $km/h$)
  * Mean Sea-Level Pressure ($MSLP$, in $hPa$)
* **FR-B3 (Anomaly Footprint Overlays)**: The system shall render discrete GeoJSON polygons representing detected anomalies, with border and fill colors mapped to event severity (e.g., Yellow = Watch, Orange = Warning, Red/Crimson = Extreme Emergency).
* **FR-B4 (Interactive Coordinate Inspection)**: Clicking anywhere on the map shall reveal a point-inspection tooltip showing exact latitude, longitude, interpolated variable values, and anomaly scores.
* **FR-B5 (Forecast-Time Controls)**: The map interface shall feature a scrubbable time-slider allowing users to step through forecast timesteps (from $T+0h$ up to $T+240h$ at configurable step intervals).
* **FR-B6 (Dynamic Legend)**: The map shall display dynamic scientific color ramps calibrated to the active layer (e.g., standard meteorological color scales for temperature and pressure).

### Module C: Anomaly Detection Engine
* **FR-C1 (Multi-Variable Anomaly Computation)**: The system shall compute anomalies across three meteorological channels:
  1. *Thermal Anomalies*: Heat domes, extreme heatwaves, and cold air outbreaks.
  2. *Kinematic Anomalies*: Gale-force winds, squall lines, and cyclonic wind shear.
  3. *Barometric Anomalies*: Deep low-pressure depressions, cyclogenesis centers, and blocking highs.
* **FR-C2 (Configurable Detection Thresholds)**: Users or system administrators shall be able to adjust anomaly sensitivity using:
  * Standard deviation ($Z$-score) offsets against climatology (e.g., $Z > 2.0\sigma$ or $Z > 3.0\sigma$).
  * Absolute physical thresholds (e.g., $MSLP < 990\ hPa$, $T_{2m} > 42^\circ C$, $WS_{10} > 17.5\ m/s$).
* **FR-C3 (Spatial Clustering & Connected Components)**: The engine shall cluster adjacent anomalous grid cells (8-connectivity) into unified spatial entities, filtering out single-cell noise below a configurable minimum area threshold (e.g., $< 2,500\ km^2$).
* **FR-C4 (Severity Categorization)**: Each detected anomaly entity shall be classified into standard severity tiers (`Advisory`, `Moderate`, `Severe`, `Extreme`) based on composite anomaly intensity and geographic extent.

### Module D: Forecast Explorer
* **FR-D1 (Timeline Navigation)**: The system shall support exploratory time stepping across the entire forecast horizon (Day 1 through Day 10).
* **FR-D2 (Trajectory & Evolution Tracking)**: When tracking a recognized anomaly across time, the system shall display its path vector (centroid shift) and rate of intensification or dissipation.
* **FR-D3 (Regional Comparisons)**: Users shall be able to compare forecast trends between two distinct geographic locations or administrative districts side-by-side using time-series charts.
* **FR-D4 (Climatological Context)**: Time-series graphs shall plot the forecast curve alongside historical 30-year climatological baseline bounds (mean $\pm 1\sigma, \pm 2\sigma$) where baseline data is available.

### Module E: Uncertainty Visualization
* **FR-E1 (Confidence & Spread Representation)**: The system shall visualize forecast uncertainty using confidence intervals or ensemble spread envelopes (e.g., 10th-90th percentile bands).
* **FR-E2 (Temporal Uncertainty Degradation)**: The interface shall explicitly display how forecast confidence diminishes as lead time increases (e.g., High Confidence at 24-48h, Moderate at 72-120h, Low/Speculative at 144-240h).
* **FR-E3 (Missing & Corrupted Data Handling)**: Grid cells with missing or masked values shall be rendered with distinct hatching patterns rather than being interpolated silently.
* **FR-E4 (Epistemic Disclaimers)**: The uncertainty module shall present plain-language explanations of model limitations to discourage over-reliance on medium-range deterministic runs.

### Module F: Alerts & Event Metadata Panel
* **FR-F1 (Structured Event Registry)**: The system shall maintain a structured table and detail view for every detected anomaly event containing:
  * Unique Event ID
  * Hazard Type (e.g., `CYCLONIC_DEPRESSION`, `HEAT_DOME`, `COLD_WAVE`, `GALE_WIND`)
  * Centroid Coordinates (Latitude, Longitude) & Bounding Box
  * First Detection Time & Target Valid Forecast Window
  * Maximum Anomaly Metric (e.g., Min MSLP: $978\ hPa$, Max Wind: $34\ m/s$)
  * Estimated Surface Area Footprint ($km^2$)
  * Impacted Regional / Administrative Districts (where geometry overlay exists)
* **FR-F2 (Export Capabilities)**: Users shall be able to export event metadata as JSON or GeoJSON for downstream integration with GIS tools (e.g., QGIS, ArcGIS).

---

## 3. Non-Functional Requirements (NFR)

### NFR-1: Performance Targets (Proposed Engineering Goals)
* **API Response Time**: Endpoint queries for pre-processed overview data and anomaly catalogs shall respond within $< 200\ ms$ under local development loads.
* **Map Layer Tile/GeoJSON Latency**: Map vector footprint payloads ($< 2\ MB$) shall render in the browser within $< 400\ ms$ upon receiving the API response.
* **Memory Footprint**: The backend Python runtime handling sample multidimensional grids shall remain within $< 1.5\ GB$ RSS during detection runs.
* **Initial Page Load**: Frontend bundle load and initial DOM paint shall complete within $< 2.0\ s$ on standard broadband connections.

### NFR-2: Responsive Design & Cross-Device Compatibility
* **Breakpoints**: The web interface shall deliver fluid responsiveness across desktop displays ($\ge 1280\ px$), tablets ($768\ px - 1024\ px$), and mobile devices ($< 768\ px$).
* **Touch-Friendly Controls**: Time sliders and map pan/zoom gestures shall support touch events for tablet-based field operations.
* **Layout Adaptation**: On narrow viewports, the side-by-side split view shall collapse into a collapsible tabbed layout (Map View vs. Analytics Panel).

### NFR-3: Accessibility (a11y)
* **Contrast Compliance**: Interface text and UI icons shall adhere to WCAG 2.1 AA contrast ratios ($\ge 4.5:1$ for normal text, $\ge 3:0:1$ for large text).
* **Colorblind-Safe Palettes**: Warning and anomaly heatmaps shall provide color ramps (e.g., Viridis, Cividis, or custom high-contrast categorical palettes) that remain distinguishable to users with deuteranopia or protanopia.
* **Keyboard Navigation**: All interactive controls (time slider, layer selectors, alert cards) shall be focusable and operable via standard keyboard navigation (`Tab`, `Enter`, Arrow keys).

### NFR-4: Maintainability & Code Quality
* **Modular Separation**: The codebase shall strictly decouple data ingestion, mathematical detection, API delivery, and UI rendering.
* **Type Safety**: The backend shall enforce 100% Pydantic v2 schemas and Python type hints (`typing`). The frontend shall maintain clean component prop validation and clean utility modularization.
* **Documentation**: Every service module and public API route shall include standardized docstrings and OpenAPI summary annotations.

### NFR-5: Data Validation & Integrity
* **Input Bounds Checking**: All API query parameters (latitude: $[-90, 90]$, longitude: $[-180, 180]$, forecast step: $[0, 240]$) shall be strictly validated prior to service execution.
* **Physical Sanity Checks**: Numerical weather arrays shall be validated against physical limits (e.g., Temperature $> -100^\circ C$ and $< 70^\circ C$; MSLP $> 850\ hPa$ and $< 1090\ hPa$) to catch processing corruption early.

### NFR-6: Logging & Observability
* **Structured Logging**: The backend shall emit structured JSON or formatted logs capturing request method, endpoint path, client IP, execution duration, and exception stack traces.
* **Auditability**: Every generated anomaly alert shall log the exact detection parameters (threshold, climatology version) used during its computation.

### NFR-7: API Error Handling & Standards
* **Standard Error Responses**: All API errors shall return standard HTTP status codes (`400 Bad Request`, `404 Not Found`, `422 Unprocessable Entity`, `500 Internal Error`) with an RFC 7807-compliant problem payload containing `error_code`, `message`, and `timestamp`.
* **Graceful Degradation**: If an optional layer or forecast step fails to compute, the client shall display a non-fatal warning toast rather than crashing the map interface.

### NFR-8: Security & Safe Execution
* **CORS Policy**: The FastAPI backend shall implement a configurable Cross-Origin Resource Sharing (CORS) policy restricting unauthorized domain requests.
* **Safe Deserialization**: Ingestion of external weather files shall strictly avoid unvetted pickling or dangerous dynamic evaluation.

### NFR-9: Scientific Transparency
* **Explicit Assumptions**: All anomaly indicators must state whether they are based on a physical threshold or a statistical deviation.
* **No "Black-Box" Pretenses**: Baseline threshold calculations shall never be falsely labeled as "Deep Learning" or "AI Predictions" in the UI.

---

## 4. Operational Limitations & Risks

1. **Synthetic vs. Operational Data Discrepancy**: The Phase 1/Stage 1 prototype relies on curated or synthetic sample grids. Synthetic data demonstrates geometric parsing and UI interactions but cannot be used for actual real-world emergency decision-making.
2. **Forecast Uncertainty Growth**: NWP skill drops non-linearly past Day 5 due to atmospheric butterfly effects. Communicating this reality is essential to prevent users from treating Day 8 cyclone tracks as deterministic truth.
3. **Bandwidth & Compute Bottlenecks**: High-resolution global NWP grids (e.g., $0.25^\circ \approx 25\ km$ resolution) generate $\sim 10^6$ grid points per variable per timestep. Transferring full grids to the client browser will cause memory starvation; server-side downsampling and polygon vectorization are required.
4. **Edge Artifacts & Longitude Wrapping**: Grouping connected components across the International Date Line ($180^\circ E / -180^\circ W$) or near the poles can cause geometric distortion or polygon tear if not explicitly handled in spherical coordinates.
5. **False Positives / False Negatives**: Fixed thresholding can misclassify localized topography (e.g., high elevation mountain passes having naturally low pressure) as meteorological anomalies unless corrected for geopotential height.

---

## 5. Formal Acceptance Criteria

To achieve sign-off for the prototype milestone, the system must satisfy the following verification criteria:

* [ ] **AC-1 (Zero-Configuration Demo)**: The platform boots up cleanly in local development without requiring immediate external credentials or high-bandwidth live downloads.
* [ ] **AC-2 (Map & Layer Toggling)**: Users can toggle between Temperature, Wind Speed, and MSLP layers on the map, with layer rendering completing smoothly within $< 500\ ms$.
* [ ] **AC-3 (Anomaly Vector Rendering)**: At least three distinct types of extreme anomalies (e.g., Cyclone, Heatwave, Coldwave) are correctly detected, clustered into GeoJSON polygons, and rendered on the map with appropriate severity styling.
* [ ] **AC-4 (Timeline Scrubber Execution)**: Moving the time slider from Day 1 to Day 10 updates the map layers, anomaly locations, and dashboard metrics synchronously.
* [ ] **AC-5 (API Contract Compliance)**: All documented REST endpoints return valid responses matching the Pydantic schemas specified in `docs/API_SPECIFICATION.md`.
* [ ] **AC-6 (Uncertainty Explanation)**: Every forecast chart displays an explicit uncertainty band and an accompanying scientific disclaimer explaining forecast horizon limitations.
* [ ] **AC-7 (Responsive Layout Fidelity)**: The user interface adapts cleanly without overlapping text, broken flex containers, or unscrollable modals on viewports from $768\ px$ to $1920\ px$.
