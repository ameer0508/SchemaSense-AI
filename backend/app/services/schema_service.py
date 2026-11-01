"""Database schema introspection service implementation for SQLite."""

from pathlib import Path
from typing import Optional
from app.core.logging import get_logger
from app.schemas.database import DatabaseInfo
from app.services.database_manager import get_database_manager
from app.services.interfaces import BaseSchemaService, SchemaMetadata
from app.services.sqlite_inspector import introspect_sqlite_database

logger = get_logger("schema_service")


class SchemaService(BaseSchemaService):
    """Orchestrates connection verification and metadata introspection for SQLite."""

    def __init__(self):
        self.db_manager = get_database_manager()

    async def introspect(
        self, connection_url: str, schema_filter: Optional[str] = None
    ) -> SchemaMetadata:
        """Introspect database schema from URL or registered database ID."""
        # Check if connection_url is a registered database ID
        db_info = self.db_manager.get_database(connection_url)
        if db_info:
            db_path = self.db_manager.get_database_path(connection_url)
        else:
            clean_path = connection_url.replace("sqlite:///", "").replace("sqlite:", "")
            db_path = Path(clean_path)
            db_info = DatabaseInfo(
                id="adhoc",
                name="Ad-hoc SQLite Database",
                filename=db_path.name,
                file_size_bytes=db_path.stat().st_size if db_path.exists() else 0,
                created_at="",
                is_active=False,
                is_protected=False,
            )

        schema_resp = introspect_sqlite_database(db_path, db_info)

        # Convert to BaseSchemaService SchemaMetadata contract
        return SchemaMetadata(
            dialect="sqlite",
            tables=[t.model_dump() for t in schema_resp.tables],
            relationships=[r.model_dump() for r in schema_resp.relationships],
        )

    async def validate_connection(self, connection_url: str) -> bool:
        """Verify SQLite database connectivity and readability."""
        try:
            db_info = self.db_manager.get_database(connection_url)
            if db_info:
                db_path = self.db_manager.get_database_path(connection_url)
            else:
                clean_path = connection_url.replace("sqlite:///", "").replace("sqlite:", "")
                db_path = Path(clean_path)

            is_valid, _ = self.db_manager.validate_sqlite_file(db_path)
            return is_valid
        except Exception as e:
            logger.warning(f"Connection validation failed for {connection_url}: {e}")
            return False
