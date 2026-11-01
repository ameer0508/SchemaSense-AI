"""Secure Read-Only SQL Execution Sandbox.

Implements defense-in-depth query execution:
- Database identity and safe path verification
- SQLGlot AST validation prior to database execution
- SQLite URI read-only connection (mode=ro)
- Strict SQLite authorizer denying DDL, DML, ATTACH, DETACH, and PRAGMAs
- PRAGMA query_only = ON, PRAGMA trusted_schema = OFF
- SQLite opcode progress-handler timeout interruption
- Bounded row fetching with accurate truncation detection
- JSON-safe cell serialization
- Semantic quality analysis
"""

import re
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.core.logging import get_logger
from app.schemas.execution import ExecuteSQLResponse, SemanticAnalysisResult, SemanticWarningItem
from app.schemas.ai import SQLValidationResult
from app.services.database_manager import DatabaseManager, get_database_manager
from app.services.sqlite_inspector import introspect_sqlite_database
from app.services.sql_validator import SQLValidator, get_sql_validator
from app.services.semantic_analyzer import SemanticAnalyzer, get_semantic_analyzer

logger = get_logger("execution_service")

# Permitted SQLite authorizer actions during query execution
ALLOWED_EXEC_ACTIONS = {
    sqlite3.SQLITE_SELECT,   # 21
    sqlite3.SQLITE_READ,     # 20
    sqlite3.SQLITE_FUNCTION, # 31
    getattr(sqlite3, "SQLITE_RECURSIVE", 33), # CTE iteration
}

# Forbidden SQLite functions
BLOCKED_FUNCTIONS = {
    "load_extension",
    "writefile",
    "readfile",
    "edit",
}


def _execution_authorizer(
    action_code: int,
    arg1: Any,
    arg2: Any,
    db_name: Any,
    trigger_name: Any,
) -> int:
    """SQLite authorizer callback that permits only reads and safe functions during query execution."""
    if action_code in ALLOWED_EXEC_ACTIONS:
        if action_code == sqlite3.SQLITE_FUNCTION:
            func_name = (str(arg2) if arg2 else "").lower()
            if func_name in BLOCKED_FUNCTIONS:
                return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    # Strictly deny all DDL, DML, PRAGMA, ATTACH, DETACH, ALTER, DROP, CREATE, TRANSACTIONS
    return sqlite3.SQLITE_DENY


def disambiguate_column_names(raw_columns: List[str]) -> List[str]:
    """Ensure column names are unique for client consumption while preserving original names.

    E.g. ['id', 'name', 'id'] -> ['id', 'name', 'id_1']
    """
    seen: Dict[str, int] = {}
    disambiguated: List[str] = []

    for col in raw_columns:
        base = col if col else "column"
        count = seen.get(base, 0)
        if count == 0:
            disambiguated.append(base)
            seen[base] = 1
        else:
            new_name = f"{base}_{count}"
            disambiguated.append(new_name)
            seen[base] = count + 1

    return disambiguated


def serialize_cell(value: Any) -> Any:
    """Format SQLite row values safely for JSON serialization."""
    if value is None:
        return None
    if isinstance(value, (int, float, bool, str)):
        # Handle NaN or Infinity floats if present
        if isinstance(value, float):
            import math
            if math.isnan(value) or math.isinf(value):
                return None
        return value
    if isinstance(value, bytes):
        return f"<BLOB {len(value)} bytes>"
    return str(value)


def sanitize_error_message(raw_error: str) -> str:
    """Remove local filesystem paths and raw stack traces from error messages."""
    msg = str(raw_error)
    # Remove file paths e.g. E:\... or /home/... or file:...
    msg = re.sub(r"[A-Za-z]:\\[\w\\\.-]+", "[DATABASE_FILE]", msg)
    msg = re.sub(r"file:[\w\/\.-]+", "[DATABASE_FILE]", msg)
    msg = re.sub(r"\/[\w\/\.-]+", "[DATABASE_FILE]", msg)
    return msg.strip()


class ExecutionService:
    """Service for validating, securing, and executing read-only SQL queries on SQLite."""

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        validator: Optional[SQLValidator] = None,
        semantic_analyzer: Optional[SemanticAnalyzer] = None,
    ):
        self.db_manager = db_manager or get_database_manager()
        self.validator = validator or get_sql_validator()
        self.semantic_analyzer = semantic_analyzer or get_semantic_analyzer()

    def execute_query(
        self,
        database_id: str,
        sql: str,
        max_rows: int = 100,
        timeout_seconds: float = 5.0,
        natural_question: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> ExecuteSQLResponse:
        """Execute a read-only SQL query against the target database with full defense-in-depth."""
        req_id = request_id or str(uuid.uuid4())
        clean_sql = sql.strip()

        # 1. Verify Database Registration
        try:
            db_info = self.db_manager.get_database(database_id)
            if not db_info:
                return ExecuteSQLResponse(
                    request_id=req_id,
                    database_id=database_id,
                    sql=clean_sql,
                    status="error",
                    error_code="DATABASE_NOT_FOUND",
                    error_message=f"Database with identifier '{database_id}' is not registered.",
                )
            db_path = self.db_manager.get_database_path(database_id)
        except KeyError:
            return ExecuteSQLResponse(
                request_id=req_id,
                database_id=database_id,
                sql=clean_sql,
                status="error",
                error_code="DATABASE_NOT_FOUND",
                error_message=f"Database with identifier '{database_id}' is not registered.",
            )
        except ValueError as ve:
            return ExecuteSQLResponse(
                request_id=req_id,
                database_id=database_id,
                sql=clean_sql,
                status="rejected",
                error_code="ILLEGAL_PATH",
                error_message=str(ve),
            )

        if not db_path.exists():
            return ExecuteSQLResponse(
                request_id=req_id,
                database_id=database_id,
                sql=clean_sql,
                status="error",
                error_code="DATABASE_FILE_MISSING",
                error_message="Database storage file is missing from the server.",
            )

        # 2. Schema Introspection for Validation & Semantic Analysis
        try:
            schema = introspect_sqlite_database(db_path, db_info)
        except Exception as e:
            logger.warning(f"Schema introspection warning before execution: {e}")
            schema = None

        # 3. Static AST Validation
        validation = self.validator.validate(clean_sql, schema=schema)
        if not validation.is_valid:
            if validation.status == "unsafe":
                return ExecuteSQLResponse(
                    request_id=req_id,
                    database_id=database_id,
                    sql=clean_sql,
                    status="rejected",
                    error_code="UNSAFE_SQL",
                    error_message="; ".join(validation.issues),
                    validation=validation,
                )
            else:
                return ExecuteSQLResponse(
                    request_id=req_id,
                    database_id=database_id,
                    sql=clean_sql,
                    status="error",
                    error_code="VALIDATION_ERROR",
                    error_message="; ".join(validation.issues),
                    validation=validation,
                )

        # 4. Semantic Quality Analysis
        semantic_analysis = self.semantic_analyzer.analyze(
            clean_sql,
            schema=schema,
            natural_question=natural_question,
        )

        # 5. Secure Read-Only Execution with Timeout and Authorizer
        bounded_max_rows = max(1, min(max_rows, 1000))
        bounded_timeout = max(0.5, min(timeout_seconds, 30.0))

        uri_path = db_path.as_posix()
        conn_uri = f"file:{uri_path}?mode=ro"

        conn: Optional[sqlite3.Connection] = None
        start_time = time.perf_counter()

        try:
            conn = sqlite3.connect(
                conn_uri,
                uri=True,
                timeout=bounded_timeout,
                check_same_thread=False,
            )

            # Defensive PRAGMAs (applied before restrictive authorizer)
            cursor = conn.cursor()
            cursor.execute("PRAGMA query_only = ON;")
            cursor.execute("PRAGMA trusted_schema = OFF;")

            # Apply restrictive authorizer callback
            conn.set_authorizer(_execution_authorizer)

            # Register opcode progress handler for server-side timeout interruption
            deadline = time.perf_counter() + bounded_timeout

            def _progress_checker() -> int:
                if time.perf_counter() > deadline:
                    return 1  # Aborts with sqlite3.OperationalError: interrupted
                return 0

            # Check every 1000 virtual machine opcodes
            conn.set_progress_handler(_progress_checker, 1000)

            # Execute query
            cursor.execute(clean_sql)
            raw_columns = [desc[0] for desc in cursor.description] if cursor.description else []
            columns = disambiguate_column_names(raw_columns)

            # Fetch bounded rows (+1 to detect truncation without mutating user SQL)
            raw_rows = cursor.fetchmany(bounded_max_rows + 1)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            is_truncated = len(raw_rows) > bounded_max_rows
            if is_truncated:
                raw_rows = raw_rows[:bounded_max_rows]

            serialized_rows = [
                [serialize_cell(val) for val in row]
                for row in raw_rows
            ]

            if len(serialized_rows) == 0 and semantic_analysis:
                zero_item = SemanticWarningItem(
                    code="EMPTY_RESULT_SET",
                    severity="info",
                    message="The query executed successfully but returned 0 rows. Verify that the filtering criteria match the actual values in the database.",
                    evidence={"row_count": 0},
                )
                if not any(w.code == "EMPTY_RESULT_SET" for w in semantic_analysis.structured_warnings):
                    semantic_analysis.structured_warnings.append(zero_item)
                    semantic_analysis.detected_patterns.append("EMPTY_RESULT_SET")

            return ExecuteSQLResponse(
                request_id=req_id,
                database_id=database_id,
                sql=clean_sql,
                status="success",
                columns=columns,
                rows=serialized_rows,
                row_count=len(serialized_rows),
                is_truncated=is_truncated,
                duration_ms=duration_ms,
                validation=validation,
                semantic_analysis=semantic_analysis,
            )

        except sqlite3.OperationalError as oe:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            err_text = str(oe).lower()
            if "interrupted" in err_text:
                return ExecuteSQLResponse(
                    request_id=req_id,
                    database_id=database_id,
                    sql=clean_sql,
                    status="timeout",
                    error_code="EXECUTION_TIMEOUT",
                    error_message=f"Query execution timed out exceeding {bounded_timeout:.1f}s resource limit.",
                    duration_ms=duration_ms,
                    validation=validation,
                    semantic_analysis=semantic_analysis,
                )
            if "not authorized" in err_text or "authorizer" in err_text:
                return ExecuteSQLResponse(
                    request_id=req_id,
                    database_id=database_id,
                    sql=clean_sql,
                    status="rejected",
                    error_code="AUTHORIZER_DENIED",
                    error_message="Query attempted database operations forbidden by security authorizer.",
                    duration_ms=duration_ms,
                    validation=validation,
                    semantic_analysis=semantic_analysis,
                )
            return ExecuteSQLResponse(
                request_id=req_id,
                database_id=database_id,
                sql=clean_sql,
                status="error",
                error_code="DATABASE_ERROR",
                error_message=sanitize_error_message(str(oe)),
                duration_ms=duration_ms,
                validation=validation,
                semantic_analysis=semantic_analysis,
            )

        except Exception as ex:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(f"Execution error on database '{database_id}': {ex}")
            return ExecuteSQLResponse(
                request_id=req_id,
                database_id=database_id,
                sql=clean_sql,
                status="error",
                error_code="DATABASE_ERROR",
                error_message=sanitize_error_message(str(ex)),
                duration_ms=duration_ms,
                validation=validation,
                semantic_analysis=semantic_analysis,
            )

        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass


# Singleton instance
_execution_service_instance: Optional[ExecutionService] = None


def get_execution_service() -> ExecutionService:
    """Return singleton ExecutionService instance."""
    global _execution_service_instance
    if _execution_service_instance is None:
        _execution_service_instance = ExecutionService()
    return _execution_service_instance
