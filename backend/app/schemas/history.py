"""Pydantic schemas for Persistent Query History and History Settings."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QueryHistoryRecord(BaseModel):
    """Represents a single persisted query execution event."""

    request_id: str = Field(..., description="Unique request UUID")
    created_at: str = Field(..., description="ISO 8601 UTC timestamp")
    database_id: str = Field(..., description="Target database identifier")
    database_name: str = Field(..., description="Display name of target database")
    question: str = Field(..., description="Natural language question")
    generation_mode: str = Field(..., description="AI generation mode or provider")
    model_id: Optional[str] = Field(None, description="Transformer model identifier")
    initial_sql: str = Field(..., description="First-attempt generated SQL query")
    final_sql: str = Field(..., description="Final validated / corrected SQL query")
    final_status: str = Field(
        ...,
        description="Overall workflow status: 'success', 'failed_validation', 'execution_error', 'timeout', 'unsafe_rejected', 'correction_exhausted'",
    )
    validation_status: str = Field(..., description="Validation status of final SQL")
    execution_status: str = Field(..., description="Execution status: 'success', 'error', 'timeout', 'not_executed'")
    row_count: Optional[int] = Field(None, description="Count of returned records (result rows are not stored)")
    correction_count: int = Field(0, description="Number of self-correction attempts made")
    generation_duration_ms: float = Field(0.0, description="Time spent on AI inference in milliseconds")
    execution_duration_ms: float = Field(0.0, description="Time spent on database execution in milliseconds")
    total_duration_ms: float = Field(0.0, description="Total workflow duration in milliseconds")
    semantic_warning_count: int = Field(0, description="Count of semantic warnings flagged")
    error_category: Optional[str] = Field(None, description="Sanitized diagnostic error category if query failed")
    correction_trace_summary: Optional[str] = Field(None, description="JSON summary of correction attempts")
    semantic_warnings_summary: Optional[str] = Field(None, description="JSON summary of semantic warnings")


class QueryHistoryListResponse(BaseModel):
    """Paginated response containing historical query executions."""

    items: List[QueryHistoryRecord]
    total: int
    page: int
    page_size: int
    total_pages: int


class HistorySettingsResponse(BaseModel):
    """Current history recording status and storage statistics."""

    is_enabled: bool = Field(True, description="Whether query history recording is enabled")
    total_saved_queries: int = Field(0, description="Total count of persisted query records")
    history_db_size_bytes: int = Field(0, description="Size of history.db file on disk")


class UpdateHistorySettingsRequest(BaseModel):
    """Payload to update history recording settings."""

    is_enabled: bool = Field(..., description="Enable or disable query history recording")
