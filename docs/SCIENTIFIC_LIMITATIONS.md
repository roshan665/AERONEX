# AeroNex — Scientific Assumptions, Methodology Boundaries & Limitations

**Document Version:** 1.0.0  
**Phase:** Phase 8 Quality Assurance & Scientific Integrity  
**Target Audience:** Evaluators, Jury, Operational Meteorologists, Domain Scientists  

---

## 1. Meteorological Integrity Principle

AeroNex is designed with scientific honesty as a non-negotiable core principle. The platform does not attempt to replace operational Numerical Weather Prediction (NWP) physics engines (e.g. NOAA GFS, ECMWF IFS, NCMRWF Unified Model), nor does it claim to generate new physical weather forecasts. 

Instead, AeroNex operates as an **intelligent spatial pattern recognition, anomaly bounding, and explainability layer** that ingests gridded NWP forecasts and extracts actionable risk footprints.

This document explicitly defines the meteorological assumptions, mathematical bounds, and operational limitations governing the platform.

---

## 2. Data Coverage & Input Grid Boundaries

| Parameter | Current Implementation | Operational Reality & Limitation |
| :--- | :--- | :--- |
| **Geographic Domain** | South Asia: $[8.0^\circ\text{N} - 38.0^\circ\text{N},\; 65.0^\circ\text{E} - 95.0^\circ\text{E}]$ | Testing is focused on the Indian subcontinent and North Indian Ocean. Full global grid processing requires ingesting $721 \times 1440$ cell global files. |
| **Spatial Grid Resolution** | $0.25^\circ \times 0.25^\circ$ ($\approx 27\text{ km} \times 27\text{ km}$ at equator) | Suitable for synoptic and mesoscale phenomena (cyclones, heat domes, cold fronts). **Cannot resolve micro-scale phenomena** such as individual tornadoes, localized cloudbursts, or microbursts. |
| **Vertical Atmospheric Levels** | Single surface / near-surface levels (2m Temperature, 10m Wind, MSLP, Surface Precip) | Lacks vertical profile soundings (e.g. 850 hPa, 500 hPa, 200 hPa). Does not yet calculate vertical wind shear, CAPE/CIN convective instability, or mid-tropospheric steering currents. |
| **Temporal Granularity** | 24-hour forecast steps ($T+24\text{h}$ to $T+240\text{h}$) | Sub-daily diurnal temperature cycles (e.g. 3-hourly peak afternoon heat) are smoothed across 24-hour evaluation steps. |
| **Reference Archive** | Bundled NetCDF4 sample (`gfs_sample_0p25_south_asia.nc`) | Guarantees deterministic, reproducible offline testing. Live NOAA NOMADS GRIB filter polling is architected but kept standby in offline evaluations. |

---

## 3. Threshold-Based Detection vs. Climatological Anomalies

A critical meteorological distinction exists between a **physical threshold exceedance** and a **climatological anomaly**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   METEOROLOGICAL DISTINCTION                           │
├───────────────────────────────────┬────────────────────────────────────┤
│ PHYSICAL THRESHOLD EXCEEDANCE     │ CLIMATOLOGICAL ANOMALY             │
│ • Absolute value exceeds physical │ • Value deviates from historical   │
│   danger criteria (e.g., wind     │   30-year normal mean for that     │
│   speed ≥ 17.5 m/s / gale-force). │   specific day of year and location│
│ • Evaluated from single forecast. │ • Requires multi-decade reanalysis │
│                                   │   (e.g., ERA5 1991–2020 normal).   │
└───────────────────────────────────┴────────────────────────────────────┘
```

### AeroNex Implementation Detail:
1. **Physical Thresholds (Primary Operational Baseline):**
   - Extreme Heat: $T_{2m} \ge 40.0^\circ\text{C}$ (Severe), $\ge 44.0^\circ\text{C}$ (Extreme).
   - Severe Cold: $T_{2m} \le 4.0^\circ\text{C}$ (Severe), $\le 0.0^\circ\text{C}$ (Extreme Freezing).
   - Gale-Force Winds: Sustained 10m wind $\ge 17.5\text{ m/s}$ ($\approx 63\text{ km/h}$).
   - Cyclonic Pressure Deficit: Central MSLP $\le 990.0\text{ hPa}$ coupled with cyclonic wind vorticity.
2. **Spatial Baseline Standard Deviations:**
   - In the absence of a bundled 30-year multi-decade ERA5 gridded climatology, the baseline detector calculates empirical standard deviation departure ($Z$-score) relative to the **spatial domain distribution** of the forecast grid.
   - True multi-decade local climatological means ($Z = \frac{x - \mu_{\text{clim}}}{\sigma_{\text{clim}}}$) are architected as an optional input grid (`temp_clim_mean`, `temp_clim_std`), and the code automatically switches to hybrid mode when provided.

---

## 4. Machine Learning & Model Evaluation Status

| Model Identifier | Classification | Validation Status & Scientific Caveat |
| :--- | :---: | :--- |
| **`deterministic_baseline`** | Operational Production Baseline | **Scientifically Verified.** Directly applies physical conservation rules, threshold gates, and morphological clustering. Zero false-positive hallucination risk. |
| **`isolation_forest_v1`** | Experimental Candidate | **Experimental Demonstration Only.** 100-tree unsupervised isolation forest partitioning an 8-dimensional normalized feature space. Trained on synthetic perturbation fields. Not yet validated against multi-decade historical storm tracks. Exhibits higher false-positive rates along coastal terrain boundaries. |
| **`spatiotemporal_v2`** | Research Prototype Stub | **Design Stub.** Exposes the feature schema and dimensional shapes for future ConvLSTM / U-Net architectures. Heavy deep-learning model weights are intentionally omitted from the hackathon distribution to maintain lightweight, cross-platform CPU compatibility. |

---

## 5. Forecast Uncertainty & Dispersion Boundaries

1. **Deterministic Single-Run Forecasts (NOAA GFS):**
   - Operational GFS is a deterministic simulation. A single model run produces exactly one trajectory with zero ensemble variance.
   - **Honest Behavior:** When in deterministic mode, AeroNex reports `is_available: false` with the explicit explanation: *"Deterministic single-run forecasts do not contain multi-member dispersion. Multi-member uncertainty requires an ensemble provider (e.g. GEFS/EPS)."* It applies Lyapunov-inspired confidence decay curves rather than inventing fake ensemble spreads.
2. **Ensemble Demonstration Mode:**
   - The 5-member ensemble view demonstrates how forecast spread widens with lead time ($T+24\text{h} \to T+240\text{h}$) using a controlled Gaussian dispersion simulation.
   - Evaluators and jury members must understand that this is an architectural demonstration of ensemble ingestion capability, not live 31-member GEFS data.

---

## 6. Multi-Component Scoring: Non-Probabilistic Guarantee

The AeroNex **Composite Anomaly Index** [0–100] combines:
- Thermal deviation (25% weight)
- Wind velocity magnitude (20% weight)
- Barometric pressure deficit (20% weight)
- Spatial footprint extent (15% weight)
- Multi-horizon temporal persistence (10% weight)
- Grid data completeness & quality (10% weight)

> [!IMPORTANT]
> **Non-Probabilistic Guarantee:**  
> The resulting composite score is a **normalized dimensionless departure index**, NOT a probability of disaster occurrence or risk percentage. It is explicitly labeled `is_probability: false` in all API schemas and user interfaces.

---

## 7. Morphological Footprint Polygonization

1. **Cell Grouping:** Contiguous clusters of anomalous grid cells are grouped using 8-connectivity morphological labeling (`scipy.ndimage.label`).
2. **Surface Area Calculation:** Ground surface area is integrated using spherical cosine-latitude weighting:
   $$\Delta A = (R_{\text{earth}} \Delta \phi) \cdot (R_{\text{earth}} \cos(\phi) \Delta \lambda)$$
   accounting for meridian convergence toward the poles.
3. **Polygon Simplification:** Raster cluster boundaries are converted to closed polygon rings via Shapely. Minimum cluster size filtering ($\ge 2500\text{ km}^2$) suppresses isolated single-cell numerical noise.
