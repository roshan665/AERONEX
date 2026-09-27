"""
AeroNex Backend Configuration Settings
"""

import os
from typing import List


class Settings:
    PROJECT_NAME: str = "AeroNex Extreme Weather Intelligence API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    DESCRIPTION: str = (
        "AI-Powered Weather Intelligence & Extreme Weather Anomaly Detection API. "
        "Provides Numerical Weather Prediction (NWP) anomaly records, geographic footprints, "
        "and 10-day forecast uncertainty metrics for the Smart India Hackathon prototype."
    )
    
    # CORS Configuration
    _cors_env: str = os.getenv("CORS_ORIGINS", "")
    CORS_ORIGINS: List[str] = (
        [origin.strip() for origin in _cors_env.split(",") if origin.strip()]
        if _cors_env
        else [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )
    CORS_ORIGIN_REGEX: str = os.getenv(
        "CORS_ORIGIN_REGEX",
        r"^https?:\/\/(localhost|127\.0\.0\.1|.*\.onrender\.com)(:\d+)?$",
    )
    
    # Provenance and Data Strategy Flags
    DATA_PROVENANCE: str = "DEMO_SYNTHETIC_DATASET"
    IS_SIMULATED: bool = True
    SCIENTIFIC_DISCLAIMER: str = (
        "DEMO NOTICE: All weather anomalies, cyclone footprints, and time-series forecasts "
        "are simulated demonstration data generated for the Smart India Hackathon evaluation. "
        "Do NOT use for operational emergency response or maritime navigation."
    )
    
    # Grid Defaults
    DEFAULT_RESOLUTION_DEG: float = 0.25
    MAX_FORECAST_DAYS: int = 10
    MAX_LEAD_TIME_HOURS: int = 240


settings = Settings()
