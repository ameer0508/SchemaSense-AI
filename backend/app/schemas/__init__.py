"""Schemas package exports."""

from app.schemas.common import ErrorDetail, ErrorResponse
from app.schemas.health import HealthResponse
from app.schemas.capabilities import CapabilityFlags, CapabilitiesResponse
from app.schemas.database import (
    ColumnMetadata,
    DatabaseInfo,
    DatabaseSchemaResponse,
    DatabaseUploadResponse,
    ForeignKeyMetadata,
    IndexMetadata,
    RelationshipMetadata,
    SchemaContextResponse,
    TableMetadata,
    TablePreviewResponse,
)

__all__ = [
    "ErrorDetail",
    "ErrorResponse",
    "HealthResponse",
    "CapabilityFlags",
    "CapabilitiesResponse",
    "ColumnMetadata",
    "DatabaseInfo",
    "DatabaseSchemaResponse",
    "DatabaseUploadResponse",
    "ForeignKeyMetadata",
    "IndexMetadata",
    "RelationshipMetadata",
    "SchemaContextResponse",
    "TableMetadata",
    "TablePreviewResponse",
]
