"""
Response schema for the application health endpoint.

Defines the API response contract using Pydantic validation.
Restricts the status field to permitted values.
"""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Application liveness response."""

    service: str
    status: Literal["healthy"]
    version: str
