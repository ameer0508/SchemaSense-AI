"""Database engine and session management foundation.

Prepares SQLite connection foundation for Phase 2 state and history persistence.
"""

import sqlite3
from typing import Generator
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("db")


def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Provide a scoped SQLite database connection.

    Prepared for Phase 2 query history and schema caching persistence.
    """
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
