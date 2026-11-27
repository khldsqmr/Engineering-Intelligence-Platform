"""
Application health endpoint.

Why?
- APIRouter allows us to organize endpoints by functionality.
- @router.get registers an HTTP GET endpoint.
- response_model defines the response contract.
- request.app retrieves the application's metadata.
Rather than putting all endpoints inside main.py, we are keeping the application modular.

"""

import os

from fastapi import APIRouter, Request

from backend.api.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def get_health(request: Request) -> HealthResponse:
    """Return the application's liveness status."""

    return HealthResponse(
        service=request.app.title,
        status="healthy",
        version=request.app.version,
        mode="demo" if os.getenv("APP_ENV") == "demo" else "live",
    )
