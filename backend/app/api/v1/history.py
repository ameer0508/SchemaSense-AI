"""API endpoints for Persistent Query History and User Privacy Settings."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.core.logging import get_logger
from app.schemas.history import (
    HistorySettingsResponse,
    QueryHistoryListResponse,
    QueryHistoryRecord,
    UpdateHistorySettingsRequest,
)
from app.services.history_service import get_history_service

logger = get_logger("history_router")
router = APIRouter(prefix="/history", tags=["Query History & Auditing"])


@router.get(
    "",
    response_model=QueryHistoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Query History",
    description="Retrieve paginated query execution records with parameterized search and filtering.",
)
async def list_history(
    page: int = Query(1, ge=1, description="Page number starting from 1"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    search: Optional[str] = Query(None, max_length=200, description="Search question text or SQL"),
    database_id: Optional[str] = Query(None, description="Filter by target database ID"),
    status: Optional[str] = Query(None, description="Filter by final execution status"),
    sort_desc: bool = Query(True, description="Sort descending by creation time"),
) -> QueryHistoryListResponse:
    """List historical queries with bounded pagination and parameterized search."""
    history_service = get_history_service()
    return history_service.list_history(
        page=page,
        page_size=page_size,
        search=search,
        database_id=database_id,
        status=status,
        sort_desc=sort_desc,
    )


@router.get(
    "/settings",
    response_model=HistorySettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get History Settings",
    description="Retrieve query history recording toggle state and local storage statistics.",
)
async def get_history_settings() -> HistorySettingsResponse:
    """Retrieve history recording configuration and database storage stats."""
    history_service = get_history_service()
    return history_service.get_settings()


@router.put(
    "/settings",
    response_model=HistorySettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Update History Settings",
    description="Toggle local query history recording on or off for privacy control.",
)
async def update_history_settings(
    payload: UpdateHistorySettingsRequest,
) -> HistorySettingsResponse:
    """Update history recording configuration."""
    history_service = get_history_service()
    history_service.set_history_enabled(payload.is_enabled)
    return history_service.get_settings()


@router.get(
    "/{request_id}",
    response_model=QueryHistoryRecord,
    status_code=status.HTTP_200_OK,
    summary="Get Single History Record",
    description="Fetch full details, telemetry, and diagnostics for an individual historical query.",
)
async def get_history_record(request_id: str) -> QueryHistoryRecord:
    """Retrieve an individual query history record by its UUID."""
    history_service = get_history_service()
    record = history_service.get_history_item(request_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"History record '{request_id}' not found.",
        )
    return record


@router.delete(
    "/{request_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Single History Record",
    description="Permanently delete a specific historical query record.",
)
async def delete_history_record(request_id: str) -> dict:
    """Delete an individual query record."""
    history_service = get_history_service()
    deleted = history_service.delete_history_item(request_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"History record '{request_id}' not found or already deleted.",
        )
    return {"status": "deleted", "request_id": request_id}


@router.delete(
    "",
    status_code=status.HTTP_200_OK,
    summary="Clear Entire Query History",
    description="Permanently clear all historical query records and reclaim disk storage.",
)
async def clear_all_history() -> dict:
    """Wipe all query history records upon explicit user confirmation."""
    history_service = get_history_service()
    deleted_count = history_service.clear_history()
    return {"status": "cleared", "deleted_count": deleted_count}
