"""API endpoints for System Analytics, Reliability Telemetry, and Performance Metrics."""

from typing import Optional
from fastapi import APIRouter, Query, status

from app.core.logging import get_logger
from app.schemas.analytics import (
    AnalyticsErrorsResponse,
    AnalyticsOverviewResponse,
    AnalyticsTimeseriesResponse,
)
from app.services.analytics_service import get_analytics_service

logger = get_logger("analytics_router")
router = APIRouter(prefix="/analytics", tags=["Analytics & Reliability Insights"])


@router.get(
    "/overview",
    response_model=AnalyticsOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Analytics Overview",
    description="Calculates real server-side aggregated metrics including success rates, average latencies, and correction statistics.",
)
async def get_analytics_overview(
    days: Optional[int] = Query(None, ge=1, le=365, description="Filter metrics by number of preceding days"),
) -> AnalyticsOverviewResponse:
    """Retrieve top-level KPI metrics derived truthfully from execution history."""
    analytics_service = get_analytics_service()
    return analytics_service.get_overview(days=days)


@router.get(
    "/timeseries",
    response_model=AnalyticsTimeseriesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Query Timeseries",
    description="Returns daily counts of total queries, first-attempt successes, corrected successes, and failures.",
)
async def get_analytics_timeseries(
    days: int = Query(14, ge=1, le=90, description="Number of daily buckets to aggregate"),
) -> AnalyticsTimeseriesResponse:
    """Retrieve daily query trend data over the requested range."""
    analytics_service = get_analytics_service()
    return analytics_service.get_timeseries(days=days)


@router.get(
    "/errors",
    response_model=AnalyticsErrorsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Error Category Taxonomy Distribution",
    description="Categorizes all recorded validation and execution failures by taxonomy frequency and percentage.",
)
async def get_analytics_errors(
    days: Optional[int] = Query(None, ge=1, le=365, description="Filter errors by preceding days"),
) -> AnalyticsErrorsResponse:
    """Retrieve frequency breakdown of diagnosed error categories."""
    analytics_service = get_analytics_service()
    return analytics_service.get_error_distribution(days=days)
