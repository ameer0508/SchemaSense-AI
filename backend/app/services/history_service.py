"""Durable Query History Persistence Layer.

Provides isolated, transactional, parameterized persistence for execution events in `backend/data/history.db`.
- Distinct and completely separated from user-uploaded databases.
- Parameterized SQLite queries avoiding any string interpolation.
- Safe fail-open behavior: query recording failures log warnings without crashing user workflows.
- User privacy controls: result rows are never persisted, and history logging can be toggled.
"""

import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.history import (
    HistorySettingsResponse,
    QueryHistoryListResponse,
    QueryHistoryRecord,
)

logger = get_logger("history_service")

CURRENT_SCHEMA_VERSION = 1


class HistoryService:
    """Manages persistent SQLite query history records and user privacy settings."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path:
            self.db_path = db_path
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            data_dir = base_dir / settings.DATA_DIR
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "history.db"

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a connection to the local history database."""
        conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            timeout=10.0,
        )
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize tables, WAL mode, indexes, and schema version."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA journal_mode = WAL;")
                cursor.execute("PRAGMA synchronous = NORMAL;")

                # Schema versioning table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY,
                        applied_at TEXT NOT NULL
                    );
                """)

                # Settings table (key-value)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS history_settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    );
                """)

                # Main query history table (records execution events, never user result rows)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS query_history (
                        request_id TEXT PRIMARY KEY,
                        created_at TEXT NOT NULL,
                        database_id TEXT NOT NULL,
                        database_name TEXT NOT NULL,
                        question TEXT NOT NULL,
                        generation_mode TEXT NOT NULL,
                        model_id TEXT,
                        initial_sql TEXT NOT NULL,
                        final_sql TEXT NOT NULL,
                        final_status TEXT NOT NULL,
                        validation_status TEXT NOT NULL,
                        execution_status TEXT NOT NULL,
                        row_count INTEGER,
                        correction_count INTEGER NOT NULL DEFAULT 0,
                        generation_duration_ms REAL NOT NULL DEFAULT 0.0,
                        execution_duration_ms REAL NOT NULL DEFAULT 0.0,
                        total_duration_ms REAL NOT NULL DEFAULT 0.0,
                        semantic_warning_count INTEGER NOT NULL DEFAULT 0,
                        error_category TEXT,
                        correction_trace_summary TEXT,
                        semantic_warnings_summary TEXT
                    );
                """)

                # Indexes for performant filtering and time-series aggregation
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_history_created_at ON query_history(created_at DESC);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_history_db ON query_history(database_id);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_query_history_status ON query_history(final_status);")

                # Default settings initialization
                cursor.execute("INSERT OR IGNORE INTO history_settings (key, value) VALUES ('is_enabled', '1');")

                # Track schema version
                cursor.execute("SELECT version FROM schema_version WHERE version = ?;", (CURRENT_SCHEMA_VERSION,))
                if not cursor.fetchone():
                    from datetime import datetime, timezone
                    now_str = datetime.now(timezone.utc).isoformat()
                    cursor.execute(
                        "INSERT INTO schema_version (version, applied_at) VALUES (?, ?);",
                        (CURRENT_SCHEMA_VERSION, now_str),
                    )

                conn.commit()
                logger.info(f"Initialized history database at {self.db_path} (Schema v{CURRENT_SCHEMA_VERSION})")
        except Exception as e:
            logger.error(f"Failed to initialize history database at {self.db_path}: {e}")

    def is_history_enabled(self) -> bool:
        """Check whether query history recording is currently enabled."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM history_settings WHERE key = 'is_enabled';")
                row = cursor.fetchone()
                if row:
                    return row["value"] == "1"
        except Exception as e:
            logger.warning(f"Error checking history settings: {e}")
        return True

    def set_history_enabled(self, enabled: bool) -> bool:
        """Toggle query history recording on or off."""
        val = "1" if enabled else "0"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO history_settings (key, value) VALUES ('is_enabled', ?);", (val,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating history settings: {e}")
            return False

    def record_query(self, record: QueryHistoryRecord) -> bool:
        """Persist a completed query workflow record safely.

        If recording is disabled or an error occurs, fails open without throwing.
        """
        if not self.is_history_enabled():
            logger.debug(f"Query history recording is disabled. Skipping {record.request_id}.")
            return False

        sql = """
            INSERT OR REPLACE INTO query_history (
                request_id, created_at, database_id, database_name, question,
                generation_mode, model_id, initial_sql, final_sql, final_status,
                validation_status, execution_status, row_count, correction_count,
                generation_duration_ms, execution_duration_ms, total_duration_ms,
                semantic_warning_count, error_category, correction_trace_summary,
                semantic_warnings_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        params = (
            record.request_id,
            record.created_at,
            record.database_id,
            record.database_name,
            record.question,
            record.generation_mode,
            record.model_id,
            record.initial_sql,
            record.final_sql,
            record.final_status,
            record.validation_status,
            record.execution_status,
            record.row_count,
            record.correction_count,
            record.generation_duration_ms,
            record.execution_duration_ms,
            record.total_duration_ms,
            record.semantic_warning_count,
            record.error_category,
            record.correction_trace_summary,
            record.semantic_warnings_summary,
        )

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                conn.commit()
                logger.info(f"Persisted history record: {record.request_id} ({record.final_status})")
                return True
        except Exception as e:
            logger.error(f"Failed to persist history record {record.request_id}: {e}")
            return False

    def list_history(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        database_id: Optional[str] = None,
        status: Optional[str] = None,
        sort_desc: bool = True,
    ) -> QueryHistoryListResponse:
        """Query historical records with search, multi-field filtering, and bounded pagination."""
        safe_page = max(1, page)
        safe_size = max(1, min(page_size, 100))
        offset = (safe_page - 1) * safe_size

        where_clauses: List[str] = ["1=1"]
        params: List[Any] = []

        if search and search.strip():
            clean_search = f"%{search.strip()}%"
            where_clauses.append("(question LIKE ? OR final_sql LIKE ?)")
            params.extend([clean_search, clean_search])

        if database_id and database_id.strip():
            where_clauses.append("database_id = ?")
            params.append(database_id.strip())

        if status and status.strip():
            where_clauses.append("final_status = ?")
            params.append(status.strip())

        where_sql = " AND ".join(where_clauses)
        order_direction = "DESC" if sort_desc else "ASC"

        count_sql = f"SELECT COUNT(*) AS total FROM query_history WHERE {where_sql};"
        select_sql = f"""
            SELECT * FROM query_history
            WHERE {where_sql}
            ORDER BY created_at {order_direction}
            LIMIT ? OFFSET ?;
        """

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(count_sql, params)
                total = cursor.fetchone()["total"]

                cursor.execute(select_sql, params + [safe_size, offset])
                rows = cursor.fetchall()

                items = [
                    QueryHistoryRecord(
                        request_id=row["request_id"],
                        created_at=row["created_at"],
                        database_id=row["database_id"],
                        database_name=row["database_name"],
                        question=row["question"],
                        generation_mode=row["generation_mode"],
                        model_id=row["model_id"],
                        initial_sql=row["initial_sql"],
                        final_sql=row["final_sql"],
                        final_status=row["final_status"],
                        validation_status=row["validation_status"],
                        execution_status=row["execution_status"],
                        row_count=row["row_count"],
                        correction_count=row["correction_count"],
                        generation_duration_ms=row["generation_duration_ms"],
                        execution_duration_ms=row["execution_duration_ms"],
                        total_duration_ms=row["total_duration_ms"],
                        semantic_warning_count=row["semantic_warning_count"],
                        error_category=row["error_category"],
                        correction_trace_summary=row["correction_trace_summary"],
                        semantic_warnings_summary=row["semantic_warnings_summary"],
                    )
                    for row in rows
                ]

                import math
                total_pages = max(1, math.ceil(total / safe_size))

                return QueryHistoryListResponse(
                    items=items,
                    total=total,
                    page=safe_page,
                    page_size=safe_size,
                    total_pages=total_pages,
                )
        except Exception as e:
            logger.error(f"Error querying history: {e}")
            return QueryHistoryListResponse(
                items=[],
                total=0,
                page=safe_page,
                page_size=safe_size,
                total_pages=1,
            )

    def get_history_item(self, request_id: str) -> Optional[QueryHistoryRecord]:
        """Fetch a single historical query execution record by request ID."""
        sql = "SELECT * FROM query_history WHERE request_id = ?;"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (request_id,))
                row = cursor.fetchone()
                if not row:
                    return None

                return QueryHistoryRecord(
                    request_id=row["request_id"],
                    created_at=row["created_at"],
                    database_id=row["database_id"],
                    database_name=row["database_name"],
                    question=row["question"],
                    generation_mode=row["generation_mode"],
                    model_id=row["model_id"],
                    initial_sql=row["initial_sql"],
                    final_sql=row["final_sql"],
                    final_status=row["final_status"],
                    validation_status=row["validation_status"],
                    execution_status=row["execution_status"],
                    row_count=row["row_count"],
                    correction_count=row["correction_count"],
                    generation_duration_ms=row["generation_duration_ms"],
                    execution_duration_ms=row["execution_duration_ms"],
                    total_duration_ms=row["total_duration_ms"],
                    semantic_warning_count=row["semantic_warning_count"],
                    error_category=row["error_category"],
                    correction_trace_summary=row["correction_trace_summary"],
                    semantic_warnings_summary=row["semantic_warnings_summary"],
                )
        except Exception as e:
            logger.error(f"Error fetching history record {request_id}: {e}")
            return None

    def delete_history_item(self, request_id: str) -> bool:
        """Delete an individual history record by ID."""
        sql = "DELETE FROM query_history WHERE request_id = ?;"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (request_id,))
                conn.commit()
                deleted = cursor.rowcount > 0
                if deleted:
                    logger.info(f"Deleted history item: {request_id}")
                return deleted
        except Exception as e:
            logger.error(f"Error deleting history item {request_id}: {e}")
            return False

    def clear_history(self) -> int:
        """Clear all historical query records and return the number of deleted rows."""
        sql = "DELETE FROM query_history;"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql)
                deleted_count = cursor.rowcount
                conn.commit()
                # Run vacuum to reclaim disk space
                cursor.execute("VACUUM;")
                logger.info(f"Cleared query history ({deleted_count} rows deleted).")
                return deleted_count
        except Exception as e:
            logger.error(f"Error clearing query history: {e}")
            return 0

    def get_settings(self) -> HistorySettingsResponse:
        """Retrieve current history settings and disk statistics."""
        is_enabled = self.is_history_enabled()
        total_queries = 0
        db_size = 0

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) AS total FROM query_history;")
                total_queries = cursor.fetchone()["total"]
        except Exception as e:
            logger.warning(f"Error counting history queries: {e}")

        if self.db_path.exists():
            try:
                db_size = self.db_path.stat().st_size
            except OSError:
                pass

        return HistorySettingsResponse(
            is_enabled=is_enabled,
            total_saved_queries=total_queries,
            history_db_size_bytes=db_size,
        )


_history_service_instance: Optional[HistoryService] = None


def get_history_service() -> HistoryService:
    """Retrieve singleton HistoryService instance."""
    global _history_service_instance
    if _history_service_instance is None:
        _history_service_instance = HistoryService()
    return _history_service_instance
