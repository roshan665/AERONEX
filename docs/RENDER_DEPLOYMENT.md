# AeroNex — Render Blueprint Deployment Guide

This guide describes how to deploy the **AeroNex Extreme Weather Intelligence Platform** (SIH-26078) to [Render](https://render.com) using Infrastructure-as-Code via **Render Blueprints** (`render.yaml`).

---

## 1. Architecture Overview on Render

AeroNex is configured to deploy via Render's official Blueprint specification:

```
                          ┌────────────────────────────────────────────────────────┐
                          │                      Render Cloud                      │
                          │                                                        │
┌──────────────────┐      │  ┌────────────────────────┐  ┌──────────────────────┐  │
│  User / Jury     │─────▶│  │    aeronex-frontend    │  │     aeronex-api      │  │
│  Web Browser     │      │  │   (Static Site CDN)    │  │  (Python Web Service)│  │
└──────────────────┘      │  │   React 18 + Vite SPA  │  │  FastAPI + Uvicorn   │  │
                          │  └───────────┬────────────┘  └──────────┬───────────┘  │
                          │              │                          │              │
                          │              │  REST API Calls (/api)   │              │
                          │              └─────────────────────────▶│              │
                          └────────────────────────────────────────────────────────┘
```

| Service Name | Render Service Type | Runtime | Free Tier Eligible | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`aeronex-api`** | `web` | `python` (3.11.9) | **Yes** (Free plan) | FastAPI backend serving 24 REST endpoints, anomaly detection, footprint extraction, and uncertainty modeling. |
| **`aeronex-frontend`** | `web` (`runtime: static`) | `static` | **Yes** (Free plan) | React 18 + Vite Single Page Application served globally over Render's high-speed CDN. |

---

## 2. One-Click Blueprint Deployment (Recommended)

### Step 1: Push Changes to GitHub
Ensure the latest code containing `render.yaml` is pushed to your GitHub repository:
```bash
git push origin main
```
Repository: [https://github.com/roshan665/AERONEX.git](https://github.com/roshan665/AERONEX.git)

### Step 2: Open Render Blueprints
1. Log in to [Render Dashboard](https://dashboard.render.com/).
2. In the top navigation bar, click **"New +"** and select **"Blueprint"** (or visit [dashboard.render.com/blueprints](https://dashboard.render.com/blueprints)).
3. Connect your GitHub account and select the **`roshan665/AERONEX`** repository.
4. Give your Blueprint instance a name (e.g., `aeronex-production`).

### Step 3: Review Resources & Click Apply
Render will automatically parse `render.yaml` from the repository root:
* **`aeronex-api`**: Python web service in `./backend`.
* **`aeronex-frontend`**: Static site in `./frontend`.

Click **"Apply"**. Render will create both services and trigger their initial builds simultaneously.

### Step 4: Synchronize API Base URL
Once the backend service has finished deploying:
1. Copy the backend service URL from Render (e.g., `https://aeronex-api.onrender.com`).
2. In the Render Dashboard, navigate to **`aeronex-frontend`** ➔ **Environment**.
3. Verify that `VITE_API_BASE_URL` matches your live API URL:
   ```env
   VITE_API_BASE_URL=https://aeronex-api.onrender.com/api
   ```
4. If changed, click **"Save Changes"** to trigger a quick static re-build.

---

## 3. Configuration Reference (`render.yaml`)

```yaml
services:
  # ---------------------------------------------------------------------------
  # 1. AeroNex FastAPI Backend REST Service
  # ---------------------------------------------------------------------------
  - type: web
    name: aeronex-api
    runtime: python
    plan: free
    region: oregon
    rootDir: backend
    buildCommand: pip install --upgrade pip && pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /api/health
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
      - key: CORS_ORIGIN_REGEX
        value: "^https?:\\/\\/(localhost|127\\.0\\.0\\.1|.*\\.onrender\\.com)(:\\d+)?$"
      - key: DATA_PROVENANCE
        value: "DEMO_SYNTHETIC_DATASET"

  # ---------------------------------------------------------------------------
  # 2. AeroNex React Frontend Static Site (Served via global CDN)
  # ---------------------------------------------------------------------------
  - type: web
    name: aeronex-frontend
    runtime: static
    rootDir: frontend
    buildCommand: npm install && npm run build
    staticPublishPath: dist
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
    envVars:
      - key: VITE_API_BASE_URL
        value: https://aeronex-api.onrender.com/api
```

### Key Blueprint Features
* **Automatic SPA Rewrites**: The `routes` block redirects all client routes (e.g. `/map`, `/anomalies`, `/reports`) to `/index.html`, eliminating 404 errors on direct navigation or page refreshes.
* **Dynamic CORS Regex**: `CORS_ORIGIN_REGEX` automatically permits all `*.onrender.com` subdomains, preventing cross-origin blocking when Render assigns dynamic domain names.
* **Health Check Probing**: Render polls `/api/health` to confirm zero-downtime deployment before routing traffic.

---

## 4. Alternative: Unified Full-Stack Single Service

If you wish to host both the frontend and backend on **a single Render Web Service** (ideal if saving on free service quotas), AeroNex supports unified serving:

1. **Build Command**:
   ```bash
   chmod +x build.sh && ./build.sh
   ```
2. **Start Command**:
   ```bash
   uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port $PORT
   ```
3. **How It Works**:
   [`backend/app/main.py`](file:///d:/msi/SIH_26078/backend/app/main.py) detects the compiled `frontend/dist` directory upon boot, mounts the production assets at `/assets`, and automatically serves the React SPA at `/` while retaining all `/api/*` endpoints under the same origin.

---

## 5. Post-Deployment Verification Checklist

Verify your live Render deployment with the following steps:

1. **Backend Health Probe**:
   ```bash
   curl -s https://<your-api-url>.onrender.com/api/health
   ```
   *Expected Response*: `{"status":"healthy","version":"1.0.0", ...}`

2. **Frontend UI**:
   * Open `https://<your-frontend-url>.onrender.com/` in your browser.
   * Confirm the top header displays the green pulse pill: **`API ONLINE`**.
   * Navigate to the **Interactive Map**, select **Severe Cyclone 01B**, and verify footprint rendering.
   * Play the **10-day Forecast Scrubber** to observe spatial track progression.

---

## 6. Troubleshooting & Operational Notes

### Free Tier Cold Starts
Render free-tier web services automatically spin down after 15 minutes of inactivity.
* When waking up, the first request may take 30–50 seconds while the container initializes.
* **AeroNex Resilience**: The frontend automatically detects API warm-up and falls back seamlessly to internal cached demo data so the jury never sees a blank screen. Once the backend responds, the header turns green (`API ONLINE`) with zero user interruption.

### Cross-Origin (CORS) Issues
If accessing the API from a custom domain outside of Render, add the domain to the backend's `CORS_ORIGINS` environment variable in the Render Dashboard:
```env
CORS_ORIGINS=https://my-custom-domain.gov.in,https://aeronex-frontend.onrender.com
```

### Static Asset Caching
Vite compiles all static assets with content hashes (e.g. `assets/index-BGCrYTAC.css`). Render's CDN caches these aggressively, ensuring sub-50ms asset delivery globally.
