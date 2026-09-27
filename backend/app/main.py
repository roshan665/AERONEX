"""
AeroNex Meteorological Intelligence Engine — FastAPI Application Entry Point
"""

from datetime import datetime, timezone
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
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

# Configure Cross-Origin Resource Sharing (CORS) for React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
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


# Mount Router
app.include_router(api_router)
app.include_router(root_router)


@app.get("/", tags=["Root"])
def root():
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
