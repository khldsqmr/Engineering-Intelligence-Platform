"""HTTP routes for deterministic engineering insights."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from backend.analytics.insights_service import (
    AnalyticsUnavailableError,
    InvalidReportingPeriodError,
    load_insights,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["Engineering Insights"],
)


@router.get("/insights")
def get_insights(
    period_start: Annotated[date | None, Query(alias="periodStart")] = None,
    period_end: Annotated[date | None, Query(alias="periodEndExclusive")] = None,
):
    """Return deterministic engineering insights for a UTC period."""

    try:
        return load_insights(period_start, period_end)

    except AnalyticsUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except InvalidReportingPeriodError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
