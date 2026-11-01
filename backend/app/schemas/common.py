"""Common schema definitions for responses and error reporting."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Normalized error detail schema."""

    code: str = Field(..., description="Unique error code identifier")
    message: str = Field(..., description="Human-readable description of the error")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata or context")


class ErrorResponse(BaseModel):
    """Standardized error response payload."""

    error: ErrorDetail
