"""
CodePulse application entry point.

Initializes the FastAPI application and registers API routers.
Retrieves the application version from installed package metadata.
"""

from importlib.metadata import version

from fastapi import FastAPI

from backend.api.routes.health import router as health_router

app = FastAPI(
    title="CodePulse",
    description="AI-powered engineering intelligence platform.",
    version=version("codepulse"),
)

app.include_router(health_router)
