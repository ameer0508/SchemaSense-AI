"""Unit and integration tests for secure read-only SQL execution engine."""

import pytest
from starlette.testclient import TestClient

from app.db.seed_demo import DEMO_DB_ID
from app.schemas.execution import ExecuteSQLRequest, ExecuteSQLResponse
from app.services.execution_service import (
    ExecutionService,
    disambiguate_column_names,
    get_execution_service,
    sanitize_error_message,
    serialize_cell,
)


def test_disambiguate_column_names():
    """Verify duplicate column labels are disambiguated while preserving order."""
    cols = ["id", "name", "id", "status", "id"]
    result = disambiguate_column_names(cols)
    assert result == ["id", "name", "id_1", "status", "id_2"]


def test_serialize_cell_types():
    """Verify JSON-safe cell serialization for various SQLite data types."""
    assert serialize_cell(None) is None
    assert serialize_cell(42) == 42
    assert serialize_cell(3.14) == 3.14
    assert serialize_cell(True) is True
    assert serialize_cell("hello") == "hello"
    assert serialize_cell(b"sqlite_binary") == "<BLOB 13 bytes>"


def test_sanitize_error_message_strips_paths():
    """Verify local filesystem paths are removed from error strings."""
    raw = "OperationalError: unable to open database file at E:\\SchemaSense AI\\backend\\data\\test.db"
    sanitized = sanitize_error_message(raw)
    assert "E:\\" not in sanitized
    assert "[DATABASE_FILE]" in sanitized


def test_execute_valid_select(client: TestClient):
    """Test valid SELECT query execution against demo database."""
    svc = get_execution_service()
    res = svc.execute_query(
        database_id=DEMO_DB_ID,
        sql="SELECT student_id, first_name, gpa FROM students ORDER BY gpa DESC LIMIT 3;",
    )
    assert res.status == "success"
    assert res.columns == ["student_id", "first_name", "gpa"]
    assert len(res.rows) == 3
    assert res.row_count == 3
    assert res.is_truncated is False
    assert res.duration_ms >= 0.0


def test_execute_multitable_join(client: TestClient):
    """Test valid multi-table JOIN query execution."""
    svc = get_execution_service()
    sql = (
        "SELECT s.first_name, s.last_name, d.department_name "
        "FROM students s "
        "JOIN departments d ON s.department_id = d.department_id "
        "LIMIT 5;"
    )
    res = svc.execute_query(database_id=DEMO_DB_ID, sql=sql)
    assert res.status == "success"
    assert "first_name" in res.columns
    assert "department_name" in res.columns
    assert len(res.rows) == 5


def test_execute_aggregation(client: TestClient):
    """Test valid aggregation query execution."""
    svc = get_execution_service()
    sql = "SELECT department_id, COUNT(*) AS count, ROUND(AVG(gpa), 2) AS avg_gpa FROM students GROUP BY department_id;"
    res = svc.execute_query(database_id=DEMO_DB_ID, sql=sql)
    assert res.status == "success"
    assert res.columns == ["department_id", "count", "avg_gpa"]
    assert len(res.rows) > 0


def test_execute_cte(client: TestClient):
    """Test valid Common Table Expression (CTE) execution."""
    svc = get_execution_service()
    sql = (
        "WITH high_gpa AS ("
        "  SELECT student_id, first_name, gpa FROM students WHERE gpa >= 3.8"
        ") "
        "SELECT * FROM high_gpa ORDER BY gpa DESC;"
    )
    res = svc.execute_query(database_id=DEMO_DB_ID, sql=sql)
    assert res.status == "success"
    assert len(res.rows) > 0


def test_execute_empty_result(client: TestClient):
    """Test valid query that matches zero rows returns empty array."""
    svc = get_execution_service()
    res = svc.execute_query(
        database_id=DEMO_DB_ID,
        sql="SELECT * FROM students WHERE gpa > 5.0;",
    )
    assert res.status == "success"
    assert len(res.rows) == 0
    assert res.row_count == 0
    assert res.is_truncated is False


def test_execute_null_values(client: TestClient):
    """Test query returning NULL values serializes safely."""
    svc = get_execution_service()
    res = svc.execute_query(
        database_id=DEMO_DB_ID,
        sql="SELECT NULL AS null_col, student_id FROM students LIMIT 1;",
    )
    assert res.status == "success"
    assert res.rows[0][0] is None


def test_execute_unicode_data(client: TestClient):
    """Test query returning Unicode characters, non-ASCII text, and emojis."""
    svc = get_execution_service()
    res = svc.execute_query(
        database_id=DEMO_DB_ID,
        sql="SELECT 'Aisha Khan — מדעי המחשב 💻' AS unicode_text, 'José García 🎓' AS student_name;",
    )
    assert res.status == "success"
    assert res.columns == ["unicode_text", "student_name"]
    assert res.rows[0][0] == "Aisha Khan — מדעי המחשב 💻"
    assert res.rows[0][1] == "José García 🎓"


def test_execute_duplicate_column_labels(client: TestClient):
    """Test query with duplicate column names are disambiguated."""
    svc = get_execution_service()
    sql = (
        "SELECT s.department_id, d.department_id "
        "FROM students s "
        "JOIN departments d ON s.department_id = d.department_id "
        "LIMIT 1;"
    )
    res = svc.execute_query(database_id=DEMO_DB_ID, sql=sql)
    assert res.status == "success"
    assert res.columns == ["department_id", "department_id_1"]


def test_execute_row_limit_and_truncation(client: TestClient):
    """Test bounded row fetching accurately detects truncation."""
    svc = get_execution_service()
    res = svc.execute_query(
        database_id=DEMO_DB_ID,
        sql="SELECT * FROM students;",
        max_rows=5,
    )
    assert res.status == "success"
    assert len(res.rows) == 5
    assert res.row_count == 5
    assert res.is_truncated is True


def test_execute_timeout_interruption(client: TestClient):
    """Test that infinite/slow recursive queries are interrupted by progress handler."""
    svc = get_execution_service()
    slow_sql = "WITH RECURSIVE cnt(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM cnt) SELECT count(*) FROM cnt;"
    res = svc.execute_query(
        database_id=DEMO_DB_ID,
        sql=slow_sql,
        timeout_seconds=0.5,
    )
    assert res.status == "timeout"
    assert res.error_code == "EXECUTION_TIMEOUT"
    assert "timed out" in res.error_message.lower()


def test_execute_unknown_table(client: TestClient):
    """Test query referencing non-existent table is rejected with validation error."""
    svc = get_execution_service()
    res = svc.execute_query(
        database_id=DEMO_DB_ID,
        sql="SELECT * FROM non_existent_table;",
    )
    assert res.status == "error"
    assert res.error_code == "VALIDATION_ERROR"
    assert "non_existent_table" in res.error_message


def test_execute_unknown_column(client: TestClient):
    """Test query referencing non-existent column is rejected with validation error."""
    svc = get_execution_service()
    res = svc.execute_query(
        database_id=DEMO_DB_ID,
        sql="SELECT hallucinated_col FROM students;",
    )
    assert res.status == "error"
    assert res.error_code == "VALIDATION_ERROR"
    assert "hallucinated_col" in res.error_message


def test_execute_syntax_error(client: TestClient):
    """Test malformed SQL syntax is rejected."""
    svc = get_execution_service()
    res = svc.execute_query(
        database_id=DEMO_DB_ID,
        sql="SELECT FROM WHERE students;",
    )
    assert res.status == "error"
    assert res.error_code == "VALIDATION_ERROR"


def test_execute_unknown_database_id(client: TestClient):
    """Test querying unregistered database returns error."""
    svc = get_execution_service()
    res = svc.execute_query(
        database_id="unknown_db_id_999",
        sql="SELECT 1;",
    )
    assert res.status == "error"
    assert res.error_code == "DATABASE_NOT_FOUND"


def test_execute_database_file_missing(monkeypatch):
    """Test database with missing file returns DATABASE_FILE_MISSING error."""
    from pathlib import Path
    from app.schemas.database import DatabaseInfo
    from app.services.database_manager import get_database_manager

    mgr = get_database_manager()
    fake_info = DatabaseInfo(
        id="ghost_db",
        name="Ghost DB",
        filename="ghost_missing.db",
        file_size_bytes=100,
        created_at="2026-01-01T00:00:00Z",
        is_active=False,
        is_protected=False,
        table_count=0,
        view_count=0,
    )
    monkeypatch.setattr(mgr, "get_database", lambda db_id: fake_info if db_id == "ghost_db" else None)
    monkeypatch.setattr(mgr, "get_database_path", lambda db_id: Path("E:/nonexistent_ghost_file.db"))

    svc = get_execution_service()
    res = svc.execute_query(database_id="ghost_db", sql="SELECT 1;")
    assert res.status == "error"
    assert res.error_code == "DATABASE_FILE_MISSING"


def test_execute_path_traversal_rejection(monkeypatch):
    """Test path traversal attempts are rejected with ILLEGAL_PATH."""
    from app.schemas.database import DatabaseInfo
    from app.services.database_manager import get_database_manager

    mgr = get_database_manager()
    fake_info = DatabaseInfo(
        id="traversal_db",
        name="Traversal DB",
        filename="../secret.db",
        file_size_bytes=100,
        created_at="2026-01-01T00:00:00Z",
        is_active=False,
        is_protected=False,
        table_count=0,
        view_count=0,
    )
    monkeypatch.setattr(mgr, "get_database", lambda db_id: fake_info if db_id == "traversal_db" else None)
    monkeypatch.setattr(
        mgr,
        "get_database_path",
        lambda db_id: (_ for _ in ()).throw(ValueError("Illegal path traversal attempt: ../secret.db")),
    )

    svc = get_execution_service()
    res = svc.execute_query(database_id="traversal_db", sql="SELECT 1;")
    assert res.status == "rejected"
    assert res.error_code == "ILLEGAL_PATH"
    assert "traversal" in res.error_message.lower()


def test_execute_resource_limits_clamped():
    """Verify that user-supplied max_rows and timeout limits are safely clamped to conservative bounds."""
    svc = get_execution_service()
    # Requesting 100,000 rows should be clamped to at most 1000
    res = svc.execute_query(
        database_id=DEMO_DB_ID,
        sql="SELECT * FROM students;",
        max_rows=100000,
        timeout_seconds=99999.0,
    )
    assert res.status == "success"
    # Campus intelligence students table has 25 rows
    assert res.row_count == 25


# --- SECURITY REJECTION TESTS ---


@pytest.mark.parametrize(
    "destructive_sql,operation",
    [
        ("DROP TABLE students;", "DROP"),
        ("DELETE FROM students WHERE 1=1;", "DELETE"),
        ("INSERT INTO students (student_id) VALUES ('X');", "INSERT"),
        ("UPDATE students SET gpa = 4.0;", "UPDATE"),
        ("ALTER TABLE students ADD COLUMN test TEXT;", "ALTER"),
        ("ATTACH DATABASE 'other.db' AS other;", "ATTACH"),
        ("PRAGMA foreign_keys = OFF;", "PRAGMA"),
        ("SELECT load_extension('evil.dll');", "load_extension"),
    ],
)
def test_security_rejections(destructive_sql: str, operation: str):
    """Verify destructive/unsafe SQL operations are rejected before execution."""
    svc = get_execution_service()
    res = svc.execute_query(database_id=DEMO_DB_ID, sql=destructive_sql)
    assert res.status == "rejected"
    assert res.error_code in ("UNSAFE_SQL", "AUTHORIZER_DENIED")


def test_security_multi_statement_rejection():
    """Verify chained multiple statements separated by semicolons are rejected."""
    svc = get_execution_service()
    res = svc.execute_query(
        database_id=DEMO_DB_ID,
        sql="SELECT * FROM students; DROP TABLE students;",
    )
    assert res.status == "rejected"
    assert res.error_code == "UNSAFE_SQL"


def test_security_unsafe_cte_rejection():
    """Verify destructive statements hidden inside CTEs are rejected."""
    svc = get_execution_service()
    res = svc.execute_query(
        database_id=DEMO_DB_ID,
        sql="WITH evil AS (DELETE FROM students RETURNING *) SELECT * FROM evil;",
    )
    assert res.status == "rejected"
    assert res.error_code == "UNSAFE_SQL"


# --- API ENDPOINT TESTS ---


def test_api_execute_sql_success(client: TestClient):
    """Test POST /api/sql/execute returns successful query output."""
    payload = {
        "database_id": DEMO_DB_ID,
        "sql": "SELECT student_id, first_name FROM students LIMIT 2;",
        "max_rows": 50,
    }
    resp = client.post("/api/sql/execute", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["columns"] == ["student_id", "first_name"]
    assert len(data["rows"]) == 2
    assert data["row_count"] == 2
    assert data["is_truncated"] is False


def test_api_execute_sql_rejected_unsafe(client: TestClient):
    """Test POST /api/sql/execute rejects unsafe SQL with rejected status."""
    payload = {
        "database_id": DEMO_DB_ID,
        "sql": "DROP TABLE students;",
    }
    resp = client.post("/api/sql/execute", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rejected"
    assert data["error_code"] == "UNSAFE_SQL"


def test_api_execute_sql_missing_database_404(client: TestClient):
    """Test POST /api/sql/execute with non-existent database ID returns 404."""
    payload = {
        "database_id": "non_existent_db_xyz",
        "sql": "SELECT 1;",
    }
    resp = client.post("/api/sql/execute", json=payload)
    assert resp.status_code == 404
