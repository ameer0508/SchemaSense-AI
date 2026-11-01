"""Database Connection Manager and Registry.

Manages SQLite database registration, safe file upload validation, active database
selection, metadata persistence, and path traversal security.
Ensures the academic demonstration database is seeded and protected.
"""

import json
import os
import re
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.logging import get_logger
from app.db.seed_demo import (
    DEMO_DB_DESCRIPTION,
    DEMO_DB_FILENAME,
    DEMO_DB_ID,
    DEMO_DB_NAME,
    seed_campus_intelligence_db,
)
from app.schemas.database import DatabaseInfo

logger = get_logger("database_manager")

ALLOWED_EXTENSIONS = {".db", ".sqlite", ".sqlite3"}
SQLITE_HEADER = b"SQLite format 3\x00"


class DatabaseManager:
    """Singleton service for local SQLite database management and registration."""

    def __init__(self, data_dir: Optional[Path] = None, databases_dir: Optional[Path] = None):
        base_backend = Path(__file__).resolve().parent.parent.parent
        self.data_dir = data_dir or (base_backend / settings.DATA_DIR)
        self.databases_dir = databases_dir or (base_backend / settings.DATABASES_DIR)
        self.metadata_file = self.data_dir / "metadata.json"

        self._ensure_directories()
        self._initialize_registry()

    def _ensure_directories(self) -> None:
        """Create storage directories safely."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.databases_dir.mkdir(parents=True, exist_ok=True)

    def _initialize_registry(self) -> None:
        """Initialize metadata registry and ensure demo database is seeded."""
        # 1. Seed demo database if missing
        demo_path = self.databases_dir / DEMO_DB_FILENAME
        seed_campus_intelligence_db(demo_path)

        # 2. Inspect demo database stats
        table_count, view_count = self._get_db_object_counts(demo_path)
        file_size = demo_path.stat().st_size if demo_path.exists() else 0

        demo_info = DatabaseInfo(
            id=DEMO_DB_ID,
            name=DEMO_DB_NAME,
            filename=DEMO_DB_FILENAME,
            file_size_bytes=file_size,
            created_at=datetime.now(timezone.utc).isoformat(),
            is_active=True,
            is_protected=True,
            table_count=table_count,
            view_count=view_count,
            description=DEMO_DB_DESCRIPTION,
        )

        metadata = self._load_metadata()
        if DEMO_DB_ID not in metadata.get("databases", {}):
            if "databases" not in metadata:
                metadata["databases"] = {}
            metadata["databases"][DEMO_DB_ID] = demo_info.model_dump()

        if not metadata.get("active_database_id"):
            metadata["active_database_id"] = DEMO_DB_ID

        # Ensure demo DB stats remain updated in metadata
        metadata["databases"][DEMO_DB_ID]["file_size_bytes"] = file_size
        metadata["databases"][DEMO_DB_ID]["table_count"] = table_count
        metadata["databases"][DEMO_DB_ID]["view_count"] = view_count
        metadata["databases"][DEMO_DB_ID]["is_protected"] = True

        self._save_metadata(metadata)

    def _load_metadata(self) -> Dict:
        """Load database metadata from JSON file."""
        if not self.metadata_file.exists():
            return {"active_database_id": DEMO_DB_ID, "databases": {}}
        try:
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading metadata JSON, resetting: {e}")
            return {"active_database_id": DEMO_DB_ID, "databases": {}}

    def _save_metadata(self, metadata: Dict) -> None:
        """Atomic write to metadata JSON file."""
        temp_file = self.metadata_file.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
            temp_file.replace(self.metadata_file)
        except Exception as e:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            logger.error(f"Failed to persist metadata JSON: {e}")

    def _get_db_object_counts(self, db_path: Path) -> Tuple[int, int]:
        """Count tables and views in a SQLite file."""
        if not db_path.exists():
            return 0, 0
        try:
            conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN type='table' THEN 1 ELSE 0 END) AS tables,
                    SUM(CASE WHEN type='view' THEN 1 ELSE 0 END) AS views
                FROM sqlite_master
                WHERE name NOT LIKE 'sqlite_%';
            """)
            res = cursor.fetchone()
            tables = res[0] or 0
            views = res[1] or 0
            conn.close()
            return int(tables), int(views)
        except Exception as e:
            logger.debug(f"Count fetch error for {db_path}: {e}")
            return 0, 0

    def resolve_safe_path(self, filename: str) -> Path:
        """Verify that a filename resolves strictly inside databases_dir to prevent path traversal."""
        clean_name = os.path.basename(filename)
        candidate = (self.databases_dir / clean_name).resolve()
        databases_dir_resolved = self.databases_dir.resolve()

        if not str(candidate).startswith(str(databases_dir_resolved)):
            raise ValueError(f"Illegal path traversal attempt: {filename}")
        return candidate

    def get_database_path(self, database_id: str) -> Path:
        """Retrieve verified path for a registered database."""
        db_info = self.get_database(database_id)
        if not db_info:
            raise KeyError(f"Database with identifier '{database_id}' not found.")
        return self.resolve_safe_path(db_info.filename)

    def list_databases(self) -> List[DatabaseInfo]:
        """List all registered databases with active state."""
        metadata = self._load_metadata()
        active_id = metadata.get("active_database_id")
        results: List[DatabaseInfo] = []

        for db_id, data in metadata.get("databases", {}).items():
            db_path = self.databases_dir / data["filename"]
            if db_path.exists():
                file_size = db_path.stat().st_size
                data["file_size_bytes"] = file_size
            data["is_active"] = (db_id == active_id)
            results.append(DatabaseInfo(**data))

        # Sort: active first, then demo, then by creation date descending
        results.sort(key=lambda d: (not d.is_active, not d.is_protected, d.name))
        return results

    def get_database(self, database_id: str) -> Optional[DatabaseInfo]:
        """Get database metadata by ID."""
        metadata = self._load_metadata()
        db_data = metadata.get("databases", {}).get(database_id)
        if not db_data:
            return None

        active_id = metadata.get("active_database_id")
        db_path = self.databases_dir / db_data["filename"]
        if db_path.exists():
            db_data["file_size_bytes"] = db_path.stat().st_size
        db_data["is_active"] = (database_id == active_id)
        return DatabaseInfo(**db_data)

    def get_active_database(self) -> Optional[DatabaseInfo]:
        """Get the currently active database info."""
        metadata = self._load_metadata()
        active_id = metadata.get("active_database_id")
        if not active_id:
            return None
        return self.get_database(active_id)

    def set_active_database(self, database_id: str) -> DatabaseInfo:
        """Activate a registered database."""
        db_info = self.get_database(database_id)
        if not db_info:
            raise KeyError(f"Database with identifier '{database_id}' is not registered.")

        metadata = self._load_metadata()
        metadata["active_database_id"] = database_id
        self._save_metadata(metadata)

        db_info.is_active = True
        logger.info(f"Active database set to: {database_id} ({db_info.name})")
        return db_info

    def validate_sqlite_file(self, file_path: Path) -> Tuple[bool, str]:
        """Validate header, integrity, and basic read access for an uploaded SQLite file."""
        if not file_path.exists() or file_path.stat().st_size == 0:
            return False, "Uploaded file is empty (0 bytes)."

        # Check magic header
        with open(file_path, "rb") as f:
            header = f.read(16)
            if header != SQLITE_HEADER:
                return False, "File is not a valid SQLite 3 database (invalid magic header)."

        # Check integrity
        try:
            conn = sqlite3.connect(f"file:{file_path.as_posix()}?mode=ro", uri=True, timeout=5.0)
            cursor = conn.cursor()
            cursor.execute("PRAGMA quick_check;")
            res = cursor.fetchone()
            conn.close()
            if not res or res[0] != "ok":
                return False, f"SQLite integrity check failed: {res[0] if res else 'Unknown error'}"
        except Exception as e:
            return False, f"SQLite validation failed: {str(e)}"

        return True, "Valid SQLite database"

    def upload_and_register_database(
        self,
        file_stream: BinaryIO,
        original_filename: str,
        display_name: Optional[str] = None,
        max_bytes: Optional[int] = None,
    ) -> DatabaseInfo:
        """Stream and validate an uploaded SQLite file, then register it in the system.

        Enforces streaming size limits, extension whitelist, integrity checks, and collision avoidance.
        """
        max_size = max_bytes or settings.MAX_UPLOAD_SIZE_BYTES

        # 1. Validate file extension
        ext = os.path.splitext(original_filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        # 2. Sanitize display name and generate unique server-side filename
        clean_stem = re.sub(r"[^\w\-.]", "_", os.path.splitext(original_filename)[0])
        db_uuid = uuid.uuid4().hex[:10]
        safe_filename = f"db_{db_uuid}_{clean_stem}{ext}"
        target_path = self.resolve_safe_path(safe_filename)
        temp_path = target_path.with_suffix(".upload_tmp")

        bytes_written = 0
        chunk_size = 64 * 1024  # 64 KB chunks

        try:
            with open(temp_path, "wb") as f_out:
                while True:
                    chunk = file_stream.read(chunk_size)
                    if not chunk:
                        break
                    bytes_written += len(chunk)
                    if bytes_written > max_size:
                        raise ValueError(
                            f"File exceeds maximum allowed size of {max_size // (1024 * 1024)} MB."
                        )
                    f_out.write(chunk)

            if bytes_written == 0:
                raise ValueError("Uploaded file is empty (0 bytes).")

            # 3. Validate SQLite structure & integrity
            is_valid, reason = self.validate_sqlite_file(temp_path)
            if not is_valid:
                raise ValueError(reason)

            # Move verified temp file to final storage path
            temp_path.replace(target_path)

            # 4. Count tables & views
            table_count, view_count = self._get_db_object_counts(target_path)
            db_id = f"user_db_{db_uuid}"
            name = display_name.strip() if display_name and display_name.strip() else clean_stem

            db_info = DatabaseInfo(
                id=db_id,
                name=name,
                filename=safe_filename,
                file_size_bytes=bytes_written,
                created_at=datetime.now(timezone.utc).isoformat(),
                is_active=False,
                is_protected=False,
                table_count=table_count,
                view_count=view_count,
                description=f"User uploaded database from '{original_filename}'",
            )

            # 5. Persist into metadata
            metadata = self._load_metadata()
            metadata["databases"][db_id] = db_info.model_dump()
            self._save_metadata(metadata)

            logger.info(f"Successfully uploaded and registered database: {db_id} ({name})")
            return db_info

        except Exception as e:
            # Clean up temp file on any failure
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            if target_path.exists():
                try:
                    target_path.unlink()
                except OSError:
                    pass
            logger.error(f"Database upload failed: {e}")
            raise

    def unregister_database(self, database_id: str, delete_file: bool = False) -> bool:
        """Unregister a database. Rejects if database is protected (e.g. demo DB)."""
        db_info = self.get_database(database_id)
        if not db_info:
            raise KeyError(f"Database '{database_id}' is not registered.")

        if db_info.is_protected:
            raise ValueError(f"Database '{db_info.name}' is a protected system database and cannot be deleted.")

        metadata = self._load_metadata()
        if database_id in metadata.get("databases", {}):
            del metadata["databases"][database_id]

        # If deleted DB was active, switch active back to demo DB
        if metadata.get("active_database_id") == database_id:
            metadata["active_database_id"] = DEMO_DB_ID

        self._save_metadata(metadata)

        # Optionally delete physical file
        if delete_file:
            try:
                db_path = self.resolve_safe_path(db_info.filename)
                if db_path.exists():
                    db_path.unlink()
                    logger.info(f"Deleted database file: {db_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file {db_info.filename}: {e}")

        logger.info(f"Unregistered database: {database_id}")
        return True


# Global database manager instance
_db_manager_instance: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Retrieve or create the global DatabaseManager instance."""
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager()
    return _db_manager_instance
