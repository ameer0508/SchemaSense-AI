"""Secure SQL execution API endpoint.

Provides standalone read-only SQLite execution with full defense-in-depth:
- Validation against database schema and read-only policies
- SQLite authorizer enforcement
- Bounded row fetching and execution timeouts
- Semantic quality analysis
"""

from fastapi import APIRouter, HTTPException, status

from app.core.logging import get_logger
from app.schemas.execution import ExecuteSQLRequest, ExecuteSQLResponse
from app.services.execution_service import get_execution_service

logger = get_logger("sql_api")

router = APIRouter(prefix="/sql", tags=["SQL Execution"])


@router.post(
    "/execute",
    response_model=ExecuteSQLResponse,
    summary="Execute Read-Only SQL Query",
    description="Validate, secure, and execute a read-only SQL query against a registered SQLite database.",
)
async def execute_sql(payload: ExecuteSQLRequest) -> ExecuteSQLResponse:
    """Execute a read-only SQL query with security controls."""
    execution_service = get_execution_service()

    result = execution_service.execute_query(
        database_id=payload.database_id,
        sql=payload.sql,
        max_rows=payload.max_rows or 100,
        timeout_seconds=payload.timeout_seconds or 5.0,
    )

    if result.status == "rejected":
        # 400 Bad Request with structured rejection details
        logger.warning(f"Query rejected on database '{payload.database_id}': {result.error_message}")
    elif result.status == "error" and result.error_code == "DATABASE_NOT_FOUND":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.error_message,
        )

    return result
