"""
Engineering Intelligence Platform application entry point.

Initializes the FastAPI application and registers API routers.
Retrieves the application version from installed package metadata.
"""

from importlib.metadata import version

from fastapi import FastAPI

from backend.api.routes.health import router as health_router
from backend.api.routes.insights import router as insights_router
from backend.api.routes.intelligence import router as intelligence_router

# ---------------------------------------------------------------------
# 01. Application initialization
# ---------------------------------------------------------------------

app = FastAPI(
    title="Engineering Intelligence Platform",
    description="AI-powered engineering intelligence platform.",
    version=version("engineering-intelligence-platform"),
)


# ---------------------------------------------------------------------
# 02. API router registration
# ---------------------------------------------------------------------

app.include_router(health_router)
app.include_router(insights_router)

app.include_router(intelligence_router)
