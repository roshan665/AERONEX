# AeroNex — SIH Demo Runbook & Jury Walkthrough Guide

**Document Version:** 1.0.0  
**Phase:** Phase 7 End-to-End System Integration & SIH Demo Readiness  
**Target Duration:** 3–5 Minutes Presentation  
**Audience:** Smart India Hackathon (SIH) Evaluators, Meteorological Domain Experts, Technical Jury  

---

## 1. Executive Summary

AeroNex is an operational-grade extreme weather intelligence platform engineered to ingest, normalize, and detect high-impact meteorological anomalies from Numerical Weather Prediction (NWP) model outputs (NOAA GFS 0.25° grid).

This runbook provides a **click-by-click demonstration script**, **scientific talking points**, **presenter cues**, and **contingency fallbacks** to deliver a compelling presentation under strict time limits.

---

## 2. Pre-Flight Verification & Launch Sequence

Execute these commands prior to jury arrival:

### Step 2.1: Start FastAPI Backend Service
```powershell
cd d:\msi\SIH_26078\backend
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
*Health Probe Verification:* Open `http://localhost:8000/api/health` in a browser. Confirm `"status": "healthy"`.

### Step 2.2: Start React Frontend Application
```powershell
cd d:\msi\SIH_26078\frontend
npm run dev
```
*UI Probe Verification:* Open `http://localhost:5173`. Confirm the top-right pill shows **`API ONLINE`** (glowing emerald dot).

---

## 3. Step-by-Step 3–5 Minute Demonstration Script

### Minute 0:00 – 0:45 | Opening & System Overview
* **Action:** Direct attention to the Dashboard landing page at `http://localhost:5173`.
* **Presenter Script:**
  > *"Good morning, respected judges. Numerical Weather Prediction (NWP) models produce terabytes of gridded forecast data every 6 hours, making manual identification of localized extreme hazards impossible for disaster response teams. AeroNex solves this by bridging the gap between raw NWP grids and actionable early warnings.
  > Notice in our top navigation shell the live system status: our FastAPI API gateway is `ONLINE`, and we clearly flag data provenance as `SYNTHETIC DEMO` until real ingestion is triggered. We never obscure simulation status from the user."*
* **Key Visuals to Highlight:**
  1. Top-right **`API ONLINE`** status badge.
  2. Provenance tag indicating active operational mode.
  3. Executive KPI Stat Cards: **Active Anomalies**, **Regions Monitored**, **Peak Wind Threat**, and **Forecast Horizon (10 Days / 240 Hours)**.

---

### Minute 0:45 – 1:30 | Scenario Selection & Automated Anomaly Detection
* **Action:** Click **`Tropical Cyclone Vortex`** in the Scenario Toolbar at the top of the dashboard.
* **Presenter Script:**
  > *"To ensure a deterministic, reproducible evaluation, we have engineered dedicated scenario generators. When I click 'Tropical Cyclone Vortex', AeroNex executes the detection pipeline across the South Asia domain.
  > Within milliseconds, our algorithm isolates the deep cyclonic low in the Bay of Bengal, calculates spatial contour polygons, computes minimum central pressure (968 hPa), and estimates the impacted ground footprint area at 28,450 km²."*
* **Action:** Click **`Heat Dome Episode`**, then **`Cold Wave Blast`**.
* **Presenter Script:**
  > *"Here we switch to a continental heat dome over Central India with severe thermal deviations of +7.2°C above climatological normal, followed by a northern cold surge. In each case, geospatial boundaries and statistical departures are recalculated dynamically."*
* **Key Visuals to Highlight:**
  1. Real-time pipeline execution notification toast.
  2. Immediate map update with colored risk footprints (Red: Cyclone, Orange: Heat Wave, Cyan: Cold Wave).
  3. Dynamic update of the **Recent Alerts** sidebar list.

---

### Minute 1:30 – 2:30 | Geospatial Map & Temporal Progression (10-Day Forecast)
* **Action:** Click on the Cyclone polygon or marker on the interactive Leaflet map.
* **Presenter Script:**
  > *"Looking at the map, our telemetry drawer immediately extracts the diagnostic vector for this anomaly: Centroid coordinates (14.2°N, 84.5°E), Anomaly Z-Score departure of +3.4σ, surface footprint area, and our automated meteorological synopsis.
  > Down below, our temporal timeline scrubber allows forecasters to navigate across lead times from Day 1 (T+24h) to Day 10 (T+240h). Watch as I press 'Play' or slide to Day 4."*
* **Action:** Slide the timeline scrubber to **`Day 3`** or **`Day 4`**.
* **Presenter Script:**
  > *"The centroid translates northwestward toward the Odisha/Andhra coast, accounting for Great-Circle geodesic distance, bearing angle, and translation speed. Polygons seamlessly update without client-side lag or coordinate inversion."*
* **Key Visuals to Highlight:**
  1. **Event Details Card** displaying Event ID, Centroid, Area (km²), Anomaly Score, Lead Window, and Methodology.
  2. Continuous color ramp legend on the map showing physical anomaly scales (°C, m/s, hPa).
  3. Temporal scrubber with animated transition.

---

### Minute 2:30 – 3:30 | Multi-Horizon Forecast Explorer
* **Action:** Navigate to **`Forecasts`** via the left sidebar.
* **Presenter Script:**
  > *"Forecasters need multi-variable physical insight. In the Forecast Explorer, we see the complete 10-day time-series trajectory. Notice our Forecast Run Metadata banner at the top: Model Run GFS-20250426-00Z, Valid Lead Hours T+24h to T+240h, and verified physical dimensions.
  > Let's switch variables from Temperature to Wind Speed, then Sea Level Pressure, and Precipitation Rate. Each variable is fetched directly from our backend API."*
* **Action:** Click tabs: `Wind`, `Pressure`, `Precipitation`.
* **Key Visuals to Highlight:**
  1. Forecast Run Metadata banner (Run ID, Init Time, Selected Day Valid Time, Lead Hours).
  2. Clean Recharts line graph displaying multi-horizon forecast evolution and variable-specific units.

---

### Minute 3:30 – 4:15 | AI Intelligence, Model Comparison & Honest Uncertainty
* **Action:** Click **`AI Models`** in the sidebar.
* **Presenter Script:**
  > *"Here lies the core algorithmic intelligence of AeroNex. 
  > First, Model Governance: We provide an operational Physical Baseline alongside an Experimental Isolation Forest ML model. Forecasters can switch candidate models in real time to assess detection sensitivity.
  > Second, Multi-Component Anomaly Attribution: Rather than treating AI as an opaque black box, our composite index breaks down physical magnitude, spatial scale, temporal persistence, and observational confidence into transparent radar and bar drivers. Notice we explicitly state: 'This is a physical departure index, not an uncalibrated probability.'
  > Third, Objective Scientific Benchmarking: We evaluate candidate models on Precision, Recall, F1, and Footprint IoU. We honestly document evaluation caveats—such as synthetic ground-truth biases—right on screen.
  > Fourth, Forecast Dispersion: In ensemble mode, we visualize multi-member standard deviation spread widening over lead time. If switched to deterministic mode, the platform transparently reports that multi-member dispersion is unavailable for single-run forecasts rather than fabricating fake spreads."*
* **Key Visuals to Highlight:**
  1. Active model activation card (`Deterministic Baseline` vs `Isolation Forest Baseline`).
  2. Multi-Component scoring gauge (Composite Score / 100, Tier, Driving Variables).
  3. Benchmark Comparison Table with IoU, F1, FPR, and Latency.
  4. Uncertainty dispersion toggle (`Ensemble Demo` vs `Deterministic Unavailable State`).

---

### Minute 4:15 – 5:00 | Real NWP Ingestion Pipeline & Closing Defense
* **Action:** Click the top-right provenance button (`SYNTHETIC DEMO` dropdown) and click **`Run Real NWP Ingestion Pipeline`**.
* **Presenter Script:**
  > *"Finally, let us demonstrate our end-to-end data pipeline on real Numerical Weather Prediction data. 
  > I trigger our ingestion pipeline on a locally cached 0.25° NOAA GFS NetCDF4 grid covering South Asia. 
  > The backend ingests the NetCDF4 dataset, validates array coordinate monotonicity and physical bounds, converts Kelvin to Celsius, and runs automated morphological footprint extraction.
  > The result is instantaneous: real anomalies extracted, footprints polygonized, and the platform transitions into `REAL NWP ACTIVE` mode.
  > In conclusion, AeroNex delivers an integrated, scientifically sound, and truthful weather intelligence solution ready for deployment. We are open for questions."*
* **Key Visuals to Highlight:**
  1. Ingestion success modal/toast reporting grid dimensions `[121, 121]`, anomalies detected, and footprints extracted.
  2. Provenance tag updating to **`REAL NWP ACTIVE`**.

---

## 4. Contingency & Fallback Guide

| Failure Scenario | Immediate Remedy | Talking Point |
| :--- | :--- | :--- |
| **Backend Crashes or Port 8000 Closes** | Click the **`Retry`** icon on the top `API OFFLINE` badge. If still down, restart the uvicorn process. The frontend remains fully functional with cached data. | *"AeroNex implements resilient offline-first caching. When network access is interrupted, the UI clearly alerts the operator without breaking client-side workflows."* |
| **Remote NOAA NOMADS Server Inaccessible** | Keep ingestion mode on `local` using the bundled `gfs_sample_0p25_south_asia.nc` sample. | *"Operational meteorological platforms require air-gapped continuity. We prioritize verified local NWP archives over brittle remote HTTP dependencies."* |
| **Evaluator Asks for Extreme or Out-of-Bounds Query** | Trigger detection with lead time > 240h or min area > 10,000,000 km². Show graceful RFC 7807 problem detail response. | *"AeroNex strictly validates meteorological bounds (0–240 hours) and handles empty results gracefully rather than returning 500 errors."* |

---

## 5. Anticipated Jury Questions & Winning Answers

### Q1: *"Is the AI model replacing traditional Numerical Weather Prediction (GFS/ECMWF)?"*
* **Answer:** *"No. AeroNex does not replace numerical physics engines; it augments them. Solving the Navier-Stokes equations requires massive supercomputing clusters. AeroNex is an intelligent post-processing, pattern recognition, and early-warning layer that analyzes NWP output grids in milliseconds to flag hazards that human forecasters might overlook."*

### Q2: *"How do you calculate the anomaly score without historical reanalysis climo on every node?"*
* **Answer:** *"Our baseline uses empirical standard deviation (Z-score) departure from the spatial domain mean combined with climatological seasonal baselines. In Phase 6, we synthesize physical magnitude, spatial footprint extent (logarithmic scaling), temporal persistence across lead frames, and observational confidence into a standardized 0–100 index."*

### Q3: *"How does the system ensure Leaflet doesn't crash on invalid polygon geometries?"*
* **Answer:** *"All geospatial polygons pass through defensive coordinate validation. The backend provides GeoJSON `[lon, lat]` which our frontend maps to Leaflet's `[lat, lon]`. Any polygon with fewer than 3 vertices or non-finite coordinates is filtered prior to SVG rendering."*

### Q4: *"Why do you show 'Uncertainty Unavailable' in deterministic mode?"*
* **Answer:** *"True scientific integrity requires acknowledging when information does not exist. A single deterministic forecast run has zero member variance. Inventing an artificial spread would be scientifically misleading to emergency managers. When ensemble members (e.g. GEFS) are connected, dispersion is calculated honestly."*
