"""Safe, read-only table preview service for SQLite tables.

Executes bounded pagination queries using read-only connections and authorizers.
Formats binary BLOBs, handles NULL values, Unicode text, and dates cleanly.
"""

import math
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.core.exceptions import SchemaSenseException
from app.core.logging import get_logger
from app.schemas.database import TablePreviewResponse
from app.services.sqlite_inspector import (
    get_read_only_connection,
    is_safe_identifier,
    quote_identifier,
)

logger = get_logger("table_preview")


def format_cell_value(val: Any) -> Any:
    """Format raw SQLite cell values safely for JSON serialization."""
    if val is None:
        return None
    if isinstance(val, (bytes, bytearray, memoryview)):
        return f"<BLOB: {len(val)} bytes>"
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return str(val)
        return val
    return val


def preview_sqlite_table(
    db_path: Path,
    database_id: str,
    table_name: str,
    limit: int = 20,
    offset: int = 0,
    max_limit: int = 100,
) -> TablePreviewResponse:
    """Safely fetch a bounded page of records from a specific table.

    Args:
        db_path: Filesystem path to SQLite database.
        database_id: Stable identifier of the database.
        table_name: Requested table name.
        limit: Requested page size (clamped between 1 and max_limit).
        offset: Record offset (>= 0).
        max_limit: Upper bound for limit.

    Returns:
        TablePreviewResponse with columns, types, rows, and pagination stats.
    """
    resolved_path = Path(db_path).resolve()
    if not resolved_path.exists():
        raise FileNotFoundError(f"Database file not found: {resolved_path}")

    if not is_safe_identifier(table_name):
        raise ValueError(f"Invalid table identifier: {table_name}")

    clamped_limit = max(1, min(limit, max_limit))
    clamped_offset = max(0, offset)

    with get_read_only_connection(resolved_path) as conn:
        cursor = conn.cursor()

        # 1. Whitelist validation: verify table exists in sqlite_master
        cursor.execute(
            "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') AND name = ?;",
            (table_name,),
        )
        row = cursor.fetchone()
        if not row:
            raise KeyError(f"Table '{table_name}' does not exist in database '{database_id}'.")

        quoted_table = quote_identifier(table_name)

        # 2. Extract column names & declared types
        try:
            cursor.execute(f"PRAGMA table_xinfo({quoted_table});")
            col_info = cursor.fetchall()
        except Exception:
            cursor.execute(f"PRAGMA table_info({quoted_table});")
            col_info = cursor.fetchall()

        column_names = [c["name"] for c in col_info]
        column_types = {c["name"]: (c["type"] or "TEXT").upper() for c in col_info}

        # 3. Get total row count
        cursor.execute(f"SELECT COUNT(*) AS total FROM {quoted_table};")
        total_rows = cursor.fetchone()["total"]

        # 4. Fetch bounded records
        cursor.execute(
            f"SELECT * FROM {quoted_table} LIMIT ? OFFSET ?;",
            (clamped_limit, clamped_offset),
        )
        raw_rows = cursor.fetchall()

        formatted_rows: List[Dict[str, Any]] = []
        for r in raw_rows:
            formatted_row: Dict[str, Any] = {}
            for col in column_names:
                formatted_row[col] = format_cell_value(r[col])
            formatted_rows.append(formatted_row)

        is_truncated = (clamped_offset + len(formatted_rows)) < total_rows

        return TablePreviewResponse(
            database_id=database_id,
            table_name=table_name,
            columns=column_names,
            column_types=column_types,
            rows=formatted_rows,
            total_rows=total_rows,
            limit=clamped_limit,
            offset=clamped_offset,
            is_truncated=is_truncated,
        )
