# AeroNex — System Capabilities, Known Limitations & Scientific Roadmap

**Document Version:** 1.0.0  
**Phase:** Phase 7 System Integration & SIH Demo Readiness  
**Target Audience:** Evaluators, Jury, Operational Meteorologists, System Architects  

---

## 1. System Taxonomy & Boundary Definitions

In accordance with meteorological standards and software verification protocols, this document provides an honest, rigorous catalog of the operational boundaries, experimental modules, and planned capabilities of AeroNex.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AERONEX CAPABILITY TIERS                        │
├───────────────────┬───────────────────┬────────────────────────────────┤
│ 1. IMPLEMENTED    │ 2. EXPERIMENTAL   │ 3. DEMO-ONLY                   │
│ Fully operational,│ Functional,       │ Curated simulations for        │
│ production-grade, │ undergoing domain │ deterministic evaluation       │
│ unit-tested.      │ tuning.           │ & presentation reliability.    │
├───────────────────┴───────────────────┴────────────────────────────────┤
│ 4. PLANNED ROADMAP & EXTENSIONS                                        │
│ Architectural roadmap for post-hackathon national deployment.           │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Implemented Capabilities (Fully Operational)

The following capabilities are fully implemented in the code, covered by automated unit/integration tests (156 passing tests), and connected to the user interface:

1. **Numerical Weather Prediction (NWP) NetCDF4 Ingestion:**
   - Ingestion of gridded NetCDF4 files (`.nc`, `.nc4`) containing multi-variable meteorological fields.
   - Spatial coordinate verification (monotonic latitudes and longitudes, uniform 0.25° grid resolution).
   - Automated physical unit normalization (Kelvin to Celsius, Pa to hPa, m/s to km/h).
   - Detection of missing data, invalid floating-point values (NaN/Inf), and coordinate discontinuities.
2. **Morphological Anomaly Footprint Extraction:**
   - 2D connected-component labeling and contour extraction on gridded anomaly fields.
   - Computation of geodesic footprint properties: Centroid coordinates (lat/lon), surface area ($km^2$), and peak anomaly magnitude.
   - Conversion of raster grid clusters into closed GeoJSON boundary polygons.
3. **Multi-Hazard Meteorological Detection:**
   - Cyclonic low-pressure vortex detection (central pressure deficit + gale-force sustained winds).
   - Continental heat dome detection (extreme positive thermal departure exceeding climatological threshold).
   - Cold wave surge detection (severe negative temperature departure + northerly wind advection).
   - Deep barometric pressure depression and gale-force wind speed anomalies.
4. **Temporal Trajectory Tracking & Geodesics:**
   - Great-Circle Haversine distance, forward azimuth bearing (degrees and 16-wind cardinal directions), and translation speed ($km/h$).
   - Multi-horizon footprint tracking across 10 forecast lead days (T+24h to T+240h).
   - Antimeridian wraparound protection for longitude math.
5. **Multi-Component Anomaly Attribution:**
   - Dimensionless fusion scoring combining physical magnitude, spatial scale (logarithmic surface area), temporal persistence across frames, and observational confidence.
   - Classification into 4 severity tiers: `Low`, `Medium`, `High`, `Critical`.
   - Clear non-probabilistic designation (departure index, not uncalibrated event probability).
6. **Decoupled System Health Probing & RFC 7807 Error Handling:**
   - Subsystem status separation (API Gateway, Anomaly Engine, Storage vs External Remote Providers).
   - Out-of-bounds parameter validation (lead times $> 240h$ or $< 0h$, unsupported variables) returning structured Problem Details.

---

## 3. Experimental Capabilities

These modules are implemented and integrated into the platform, but represent research prototypes undergoing active meteorological validation:

1. **Isolation Forest Unsupervised Anomaly Detector (`isolation_forest_v1`):**
   - *Status:* Experimental Candidate Model.
   - *Implementation:* 100-estimator isolation forest trained on an 8-dimensional normalized feature space (`temp_anomaly`, `wind_anomaly`, `pressure_anomaly`, `area_km2`, `magnitude`, `latitude`, `longitude`, `lead_day`).
   - *Limitation:* Trained on synthesized benchmark distributions rather than historical multi-decade ERA5 reanalysis datasets. May exhibit elevated false-positive rates along complex coastal or high-elevation boundary zones.
2. **Spatiotemporal Deep Learning Research Stub (`spatiotemporal_v2`):**
   - *Status:* Architecture Stub / Research Prototype.
   - *Implementation:* Documented interface with feature schema and parameter shapes for ConvLSTM/U-Net spatiotemporal forecasting.
   - *Limitation:* Does not execute heavy PyTorch/TensorFlow weights in the demo bundle to maintain lightweight, cross-platform CPU compatibility.

---

## 4. Demo-Only Features & Synthetic Data

To ensure reliable, deterministic jury presentations without dependence on live NOAA server latency or network outages, the following elements use curated simulations:

1. **Preset Scenario Generators:**
   - The presets (`Cyclone`, `Heat Wave`, `Cold Wave`) generate reproducible mathematical grids representing realistic meteorological hazards over South Asia.
   - Every synthetic event is explicitly marked with `is_simulated: true` and `data_source: "DEMO_SYNTHETIC_DATASET"`.
2. **5-Member Ensemble Uncertainty Spread:**
   - The ensemble spread displayed in the AI Uncertainty Console uses a 5-member Gaussian dispersion simulation to demonstrate how forecast spread widens with lead time ($T+24h \to T+240h$).
   - In single-run deterministic mode, the platform honestly displays an **Unavailable State** rather than fabricating false member spreads.
3. **Bundled NetCDF4 Sample (`gfs_sample_0p25_south_asia.nc`):**
   - A single-cycle 0.25° GFS grid slice over South Asia [8°N–38°N, 65°E–95°E] is packaged locally to guarantee offline ingestion testing.

---

## 5. Data & Validation Limitations

1. **Geographic Domain:**
   - The primary tested domain is South Asia ($8^\circ\text{N} - 38^\circ\text{N}$, $65^\circ\text{E} - 95^\circ\text{E}$). Global projection outside this bounding box requires ingesting full-resolution global GFS grids ($721 \times 1440$ cells).
2. **Vertical Atmospheric Levels:**
   - Current detection pipelines operate on single-level surface and near-surface fields: 2m Temperature, 10m U/V Wind Components, Mean Sea Level Pressure (MSLP), and Total Surface Precipitation Rate. Upper-tropospheric variables (500 hPa geopotential height, 200 hPa jet stream winds, 850 hPa vorticity) are planned for subsequent phases.
3. **Climatological Reference Baselines:**
   - Real-world anomaly detection utilizes 30-year climate normal datasets (e.g. 1991–2020 ERA5 or WMO normal). In the current demonstration version, climatological means and standard deviations are computed from empirical spatial domain distributions and calibrated seasonal baselines.
4. **Single-Run Deterministic NWP vs Ensemble Prediction Systems (EPS):**
   - NOAA GFS operational 0.25° is a single deterministic model run. True probabilistic ensemble spread requires ingesting 31-member GEFS (Global Ensemble Forecast System) or 51-member ECMWF EPS data streams.

---

## 6. Planned Engineering Roadmap (Post-Hackathon)

| Milestone | Target Horizon | Planned Engineering Deliverables |
| :--- | :---: | :--- |
| **Phase 8: Automated Live Ingestion Daemon** | Q3 2026 | Background cron worker polling NOAA NOMADS every 6 hours (00Z, 06Z, 12Z, 18Z), automated GRIB2 slicing via `wgrib2`, and Redis caching. |
| **Phase 9: Multi-Model Ensemble Ingestion** | Q4 2026 | Ingestion of 31-member GEFS and ECMWF EPS ensembles for genuine physical ensemble standard deviations and exceedance probability curves. |
| **Phase 10: 3D Atmospheric Soundings** | Q1 2027 | Multi-level vertical ingestion (850, 700, 500, 250 hPa) for vertical wind shear, CAPE/CIN convective instability, and tropical cyclone steering currents. |
| **Phase 11: Edge Alerting & CAP Protocol** | Q2 2027 | Common Alerting Protocol (CAP v1.2) XML export for direct integration into national disaster management authorities (NDMA/SDMA) and SMS/WhatsApp webhooks. |
