"""Pydantic schemas for the health check endpoint."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Accurate backend status response."""

    status: str = Field(default="healthy", description="Current system operational status")
    version: str = Field(..., description="Semantic version of SchemaSense AI backend")
    environment: str = Field(..., description="Running environment (e.g. development, production)")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of the health check")
    service: str = Field(default="SchemaSense AI API", description="Service name")
    uptime_seconds: float = Field(..., description="Seconds since application startup")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "environment": "development",
                "timestamp": "2026-10-27T05:30:00Z",
                "service": "SchemaSense AI API",
                "uptime_seconds": 12.34,
            }
        }
    }
