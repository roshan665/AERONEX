"""
AeroNex Meteorological Intelligence Engine — FastAPI Application Entry Point
"""

import os
from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.logging import logger
from app.api.router import api_router, root_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure Cross-Origin Resource Sharing (CORS) for React development and Render deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global RFC 7807 Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP {exc.status_code} at {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": f"https://aeronex.gov.in/errors/http-{exc.status_code}",
            "title": "Application Error",
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": request.url.path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = "; ".join([f"{err['loc'][-1]}: {err['msg']}" for err in exc.errors()])
    logger.warning(f"Validation failure at {request.url.path}: {error_messages}")
    return JSONResponse(
        status_code=422,
        content={
            "type": "https://aeronex.gov.in/errors/validation-error",
            "title": "Unprocessable Entity",
            "status": 422,
            "detail": f"Request validation failed: {error_messages}",
            "instance": request.url.path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# Check for production frontend build artifacts (unified deployment mode)
_dist_candidates = [
    Path(os.getenv("STATIC_DIR", "")) if os.getenv("STATIC_DIR") else None,
    Path(__file__).resolve().parent.parent.parent / "frontend" / "dist",
    Path(__file__).resolve().parent.parent / "static",
]
FRONTEND_DIST = next((p for p in _dist_candidates if p and p.is_dir() and (p / "index.html").exists()), None)

# Mount Routers (API routes take precedence)
app.include_router(api_router)
app.include_router(root_router)


@app.get("/", tags=["Root"])
def root(request: Request):
    accept = request.headers.get("accept", "")
    # Serve SPA index.html to web browsers navigating to root when frontend is built
    if "text/html" in accept and FRONTEND_DIST:
        return FileResponse(FRONTEND_DIST / "index.html")
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "documentation": "/docs",
        "health_check": "/api/health",
        "overview": "/api/overview",
        "data_mode": settings.DATA_PROVENANCE,
        "disclaimer": settings.SCIENTIFIC_DISCLAIMER,
    }


# Optional: Mount production static files and SPA fallback for unified full-stack deployments
if FRONTEND_DIST:
    logger.info(f"Unified deployment mode: mounting frontend build from {FRONTEND_DIST}")
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa_fallback(full_path: str, request: Request):
        # Do not catch API routes or API documentation
        if full_path.startswith("api") or full_path in ("docs", "redoc", "openapi.json"):
            raise HTTPException(status_code=404, detail="API route not found")
        
        target = FRONTEND_DIST / full_path
        if target.is_file():
            return FileResponse(target)
        
        # Fallback to SPA index.html for client-side routing
        return FileResponse(FRONTEND_DIST / "index.html")
