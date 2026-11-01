"""Database management and schema intelligence API router.

Exposes endpoints for:
- Listing registered databases
- Uploading and validating SQLite databases
- Setting and retrieving the active database
- Unregistering databases
- Full schema introspection
- Discovered relationship graphs
- Safe, paginated table previews
- Deterministic LLM schema context serialization
"""

from typing import List, Optional
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.database import (
    DatabaseInfo,
    DatabaseSchemaResponse,
    DatabaseUploadResponse,
    RelationshipMetadata,
    SchemaContextResponse,
    TablePreviewResponse,
)
from app.services.database_manager import get_database_manager
from app.services.sqlite_inspector import (
    generate_deterministic_schema_context,
    introspect_sqlite_database,
)
from app.services.table_preview import preview_sqlite_table

logger = get_logger("databases_api")

router = APIRouter(prefix="/databases", tags=["Databases & Schema"])


@router.get(
    "",
    response_model=List[DatabaseInfo],
    summary="List Registered Databases",
    description="Retrieve all registered SQLite databases with current active status, table count, and file size.",
)
async def list_databases() -> List[DatabaseInfo]:
    """Return all registered databases."""
    manager = get_database_manager()
    return manager.list_databases()


@router.get(
    "/active",
    response_model=DatabaseInfo,
    summary="Get Active Database",
    description="Retrieve metadata for the currently active database.",
)
async def get_active_database() -> DatabaseInfo:
    """Return active database metadata."""
    manager = get_database_manager()
    active_db = manager.get_active_database()
    if not active_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No database is currently active. Connect or activate a database to proceed.",
        )
    return active_db


@router.post(
    "/upload",
    response_model=DatabaseUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload SQLite Database",
    description="Upload, validate, and register a SQLite database file (.db, .sqlite, .sqlite3).",
)
async def upload_database(
    file: UploadFile = File(..., description="SQLite database file"),
    name: Optional[str] = Form(None, description="Optional custom display name"),
) -> DatabaseUploadResponse:
    """Upload and validate a SQLite database file."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    manager = get_database_manager()

    try:
        db_info = manager.upload_and_register_database(
            file_stream=file.file,
            original_filename=file.filename,
            display_name=name,
        )
        return DatabaseUploadResponse(
            database=db_info,
            message=f"Database '{db_info.name}' uploaded and registered successfully.",
        )
    except ValueError as e:
        error_msg = str(e)
        if "exceeds maximum allowed size" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=error_msg,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the database file: {str(e)}",
        )


@router.post(
    "/{database_id}/activate",
    response_model=DatabaseInfo,
    summary="Activate Database",
    description="Set a registered database as the active database for the workspace.",
)
async def activate_database(database_id: str) -> DatabaseInfo:
    """Activate a database by ID."""
    manager = get_database_manager()
    try:
        return manager.set_active_database(database_id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete(
    "/{database_id}",
    summary="Unregister Database",
    description="Unregister a database. Protected databases (such as Campus Intelligence) cannot be unregistered.",
)
async def unregister_database(
    database_id: str,
    delete_file: bool = Query(
        False, description="Whether to also delete the physical database file from disk"
    ),
):
    """Unregister a database by ID."""
    manager = get_database_manager()
    try:
        manager.unregister_database(database_id, delete_file=delete_file)
        return {
            "status": "success",
            "message": f"Database '{database_id}' unregistered successfully.",
        }
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/{database_id}/schema",
    response_model=DatabaseSchemaResponse,
    summary="Get Database Schema",
    description="Introspect all tables, columns, primary keys, foreign keys, and indices for the given database.",
)
async def get_database_schema(database_id: str) -> DatabaseSchemaResponse:
    """Introspect full database schema."""
    manager = get_database_manager()
    db_info = manager.get_database(database_id)
    if not db_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{database_id}' is not registered.",
        )

    try:
        db_path = manager.get_database_path(database_id)
        return introspect_sqlite_database(db_path, db_info)
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Schema introspection error for {database_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema introspection failed: {str(e)}",
        )


@router.get(
    "/{database_id}/relationships",
    response_model=List[RelationshipMetadata],
    summary="Get Database Relationships",
    description="Extract all foreign key relationships between tables for the given database.",
)
async def get_database_relationships(database_id: str) -> List[RelationshipMetadata]:
    """Retrieve discovered relationships graph."""
    manager = get_database_manager()
    db_info = manager.get_database(database_id)
    if not db_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{database_id}' is not registered.",
        )

    try:
        db_path = manager.get_database_path(database_id)
        schema = introspect_sqlite_database(db_path, db_info)
        return schema.relationships
    except Exception as e:
        logger.error(f"Relationship discovery error for {database_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Relationship discovery failed: {str(e)}",
        )


@router.get(
    "/{database_id}/tables/{table_name}/preview",
    response_model=TablePreviewResponse,
    summary="Preview Table Records",
    description="Safely preview a bounded page of records from a specific table (default limit 20, max 100).",
)
async def preview_table(
    database_id: str,
    table_name: str,
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> TablePreviewResponse:
    """Fetch paginated read-only records from a table."""
    manager = get_database_manager()
    db_info = manager.get_database(database_id)
    if not db_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{database_id}' is not registered.",
        )

    try:
        db_path = manager.get_database_path(database_id)
        return preview_sqlite_table(
            db_path=db_path,
            database_id=database_id,
            table_name=table_name,
            limit=limit,
            offset=offset,
            max_limit=settings.PREVIEW_MAX_LIMIT,
        )
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Table preview error for {database_id}.{table_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Table preview failed: {str(e)}",
        )


@router.get(
    "/{database_id}/schema-context",
    response_model=SchemaContextResponse,
    summary="Get LLM Schema Context",
    description="Retrieve a deterministic, prompt-ready schema serialization format suitable for Generative AI SQL generation.",
)
async def get_schema_context(database_id: str) -> SchemaContextResponse:
    """Generate prompt-ready schema context."""
    manager = get_database_manager()
    db_info = manager.get_database(database_id)
    if not db_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database '{database_id}' is not registered.",
        )

    try:
        db_path = manager.get_database_path(database_id)
        schema = introspect_sqlite_database(db_path, db_info)
        return generate_deterministic_schema_context(schema)
    except Exception as e:
        logger.error(f"Schema context generation error for {database_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Schema context generation failed: {str(e)}",
        )
