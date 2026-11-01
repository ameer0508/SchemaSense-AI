"""Pydantic schemas for database management and schema intelligence."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ColumnMetadata(BaseModel):
    """Metadata describing a single column in a database table."""

    name: str = Field(..., description="Column identifier")
    data_type: str = Field(..., description="Declared SQLite data type")
    nullable: bool = Field(..., description="Whether the column allows NULL values")
    primary_key: bool = Field(..., description="Whether the column is part of the primary key")
    pk_position: Optional[int] = Field(
        None, description="1-indexed position in composite primary key, if applicable"
    )
    default_value: Optional[str] = Field(None, description="Default value expression, if defined")
    is_foreign_key: bool = Field(False, description="Whether this column references another table")
    fk_target_table: Optional[str] = Field(None, description="Referenced table name")
    fk_target_column: Optional[str] = Field(None, description="Referenced column name")
    check_constraint: Optional[str] = Field(None, description="Parsed CHECK constraint expression if defined")
    min_value: Optional[float] = Field(None, description="Known minimum bound (declared constraint or observed)")
    max_value: Optional[float] = Field(None, description="Known maximum bound (declared constraint or observed)")
    value_bound_type: Optional[str] = Field(None, description="Source of bound: 'declared' or 'observed'")


class ForeignKeyMetadata(BaseModel):
    """Metadata describing a foreign key constraint."""

    constraint_id: Optional[int] = Field(None, description="Internal constraint sequence identifier")
    from_column: str = Field(..., description="Column in source table")
    to_table: str = Field(..., description="Referenced table")
    to_column: str = Field(..., description="Referenced column in target table")
    on_update: Optional[str] = Field("NO ACTION", description="ON UPDATE referential action")
    on_delete: Optional[str] = Field("NO ACTION", description="ON DELETE referential action")


class IndexMetadata(BaseModel):
    """Metadata describing a database index."""

    name: str = Field(..., description="Index name")
    columns: List[str] = Field(default_factory=list, description="Indexed column names")
    unique: bool = Field(False, description="Whether the index enforces uniqueness")


class TableMetadata(BaseModel):
    """Metadata describing a database table or view."""

    name: str = Field(..., description="Table or view identifier")
    type: str = Field("table", description="Object type: 'table' or 'view'")
    column_count: int = Field(..., description="Number of columns")
    row_count: int = Field(0, description="Row count in table")
    columns: List[ColumnMetadata] = Field(default_factory=list, description="Column definitions")
    primary_keys: List[str] = Field(default_factory=list, description="Primary key column names")
    foreign_keys: List[ForeignKeyMetadata] = Field(
        default_factory=list, description="Foreign key relationships"
    )
    indices: List[IndexMetadata] = Field(default_factory=list, description="Associated indices")


class RelationshipMetadata(BaseModel):
    """Declared relationship between two tables derived from foreign key constraints."""

    id: str = Field(..., description="Deterministic relationship identifier")
    source_table: str = Field(..., description="Source/child table containing foreign key")
    source_column: str = Field(..., description="Source column containing foreign key")
    target_table: str = Field(..., description="Referenced/parent table")
    target_column: str = Field(..., description="Referenced primary key column")
    is_composite: bool = Field(False, description="Whether foreign key is composite")
    composite_pairs: Optional[List[Dict[str, str]]] = Field(
        None, description="List of (source_col, target_col) mappings for composite keys"
    )


class DatabaseInfo(BaseModel):
    """Summary metadata for a registered SQLite database."""

    id: str = Field(..., description="Stable unique identifier for the database")
    name: str = Field(..., description="Human-readable display name")
    filename: str = Field(..., description="Server-side storage filename")
    file_size_bytes: int = Field(..., description="Database file size in bytes")
    created_at: str = Field(..., description="ISO 8601 registration timestamp")
    is_active: bool = Field(False, description="Whether this database is currently active")
    is_protected: bool = Field(
        False, description="Whether this database is protected from deletion (e.g. demo DB)"
    )
    table_count: int = Field(0, description="Number of tables in the database")
    view_count: int = Field(0, description="Number of views in the database")
    description: Optional[str] = Field(None, description="Optional description of the database")


class DatabaseSchemaResponse(BaseModel):
    """Full introspected database schema response."""

    database: DatabaseInfo = Field(..., description="Summary of the database")
    dialect: str = Field("sqlite", description="Database dialect")
    tables: List[TableMetadata] = Field(default_factory=list, description="List of table metadata")
    relationships: List[RelationshipMetadata] = Field(
        default_factory=list, description="List of discovered relationships"
    )
    total_tables: int = Field(..., description="Total tables count")
    total_columns: int = Field(..., description="Total columns count across all tables")
    total_relationships: int = Field(..., description="Total foreign key relationships")


class TablePreviewResponse(BaseModel):
    """Bounded tabular records preview for a single table."""

    database_id: str = Field(..., description="Database identifier")
    table_name: str = Field(..., description="Table name")
    columns: List[str] = Field(default_factory=list, description="Column names in order")
    column_types: Dict[str, str] = Field(
        default_factory=dict, description="Mapping of column names to SQLite types"
    )
    rows: List[Dict[str, Any]] = Field(default_factory=list, description="List of row records")
    total_rows: int = Field(..., description="Total rows in table")
    limit: int = Field(..., description="Requested rows limit")
    offset: int = Field(..., description="Requested offset")
    is_truncated: bool = Field(
        False, description="Whether results are truncated by limit/pagination"
    )


class SchemaContextResponse(BaseModel):
    """Deterministic, LLM-ready schema serialization format."""

    database_id: str = Field(..., description="Database identifier")
    database_name: str = Field(..., description="Database display name")
    dialect: str = Field("sqlite", description="Database dialect")
    prompt_schema_context: str = Field(
        ..., description="Deterministic schema prompt context formatted for LLM generation"
    )
    token_estimate: int = Field(..., description="Approximate token count for the schema context")


class DatabaseUploadResponse(BaseModel):
    """Response returned upon successful database upload and registration."""

    database: DatabaseInfo = Field(..., description="Registered database metadata")
    message: str = Field(..., description="Success message")
