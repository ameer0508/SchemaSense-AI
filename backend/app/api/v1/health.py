"""Health check API router."""

import time
from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])

# Application start time for accurate uptime measurement
START_TIME = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Backend Health Status",
    description="Returns live operational status, version, uptime, and environment.",
)
async def get_health() -> HealthResponse:
    """Return live health status of SchemaSense AI backend."""
    current_time = time.time()
    uptime = round(current_time - START_TIME, 2)
    now_iso = datetime.now(timezone.utc).isoformat()

    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=now_iso,
        service="SchemaSense AI API",
        uptime_seconds=uptime,
    )
