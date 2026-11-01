"""Comprehensive test suite for Phase 3 SQLite database foundation and schema intelligence.

Tests:
- Sample database creation and idempotency
- Database registration and listing
- SQLite file upload validation and rejection of malformed/oversized/empty files
- Schema introspection, column data types, and primary key detection
- Composite primary keys and foreign key relationships
- Safe table preview with bounded pagination
- Security boundaries: read-only authorizer, path traversal rejection, protected deletion
- Deterministic LLM schema context serialization
"""

import io
import os
import sqlite3
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.db.seed_demo import (
    DEMO_DB_ID,
    DEMO_DB_NAME,
    seed_campus_intelligence_db,
)
from app.services.database_manager import get_database_manager
from app.services.sqlite_inspector import (
    get_read_only_connection,
    introspect_sqlite_database,
    is_safe_identifier,
)


def create_in_memory_sqlite_bytes(include_composite_pk: bool = False) -> bytes:
    """Helper to generate valid SQLite database file bytes for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    conn = sqlite3.connect(str(tmp_path))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE authors (
            author_id INTEGER PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            country VARCHAR(50)
        );
    """)
    cursor.execute("""
        CREATE TABLE books (
            book_id INTEGER PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            author_id INTEGER NOT NULL,
            published_year INTEGER,
            FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE CASCADE
        );
    """)

    if include_composite_pk:
        cursor.execute("""
            CREATE TABLE book_categories (
                book_id INTEGER NOT NULL,
                category_id INTEGER NOT NULL,
                assigned_at DATE NOT NULL,
                PRIMARY KEY (book_id, category_id),
                FOREIGN KEY (book_id) REFERENCES books(book_id)
            );
        """)

    cursor.execute("INSERT INTO authors (author_id, name, country) VALUES (1, 'Ada Lovelace', 'UK');")
    cursor.execute("INSERT INTO authors (author_id, name, country) VALUES (2, 'Claude Shannon', 'USA');")
    cursor.execute("INSERT INTO books (book_id, title, author_id, published_year) VALUES (101, 'Notes on Engine', 1, 1843);")
    cursor.execute("INSERT INTO books (book_id, title, author_id, published_year) VALUES (102, 'Mathematical Theory', 2, 1948);")

    if include_composite_pk:
        cursor.execute("INSERT INTO book_categories (book_id, category_id, assigned_at) VALUES (101, 1, '2023-01-01');")
        cursor.execute("INSERT INTO book_categories (book_id, category_id, assigned_at) VALUES (101, 2, '2023-01-02');")

    conn.commit()
    conn.close()

    with open(tmp_path, "rb") as f:
        data = f.read()

    os.remove(tmp_path)
    return data


# --- 1. Sample Database Tests ---

def test_sample_database_creation(tmp_path: Path):
    """Verify that seed_campus_intelligence_db creates all 7 tables with rows and constraints."""
    test_db = tmp_path / "test_campus.db"
    res = seed_campus_intelligence_db(test_db, force=True)
    assert res is True
    assert test_db.exists()

    conn = sqlite3.connect(str(test_db))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = {r[0] for r in cursor.fetchall()}
    expected_tables = {
        "departments",
        "faculty",
        "students",
        "courses",
        "enrollments",
        "attendance",
        "assessments",
    }
    assert expected_tables.issubset(tables)

    # Check student row count
    cursor.execute("SELECT count(*) FROM students;")
    assert cursor.fetchone()[0] == 25

    # Check referential integrity
    cursor.execute("PRAGMA foreign_key_check;")
    assert len(cursor.fetchall()) == 0
    conn.close()


def test_sample_database_idempotency(tmp_path: Path):
    """Verify that calling seed_campus_intelligence_db repeatedly is safe and idempotent."""
    test_db = tmp_path / "idempotent_test.db"
    res1 = seed_campus_intelligence_db(test_db, force=False)
    assert res1 is True
    size1 = test_db.stat().st_size

    res2 = seed_campus_intelligence_db(test_db, force=False)
    assert res2 is True
    size2 = test_db.stat().st_size
    assert size1 == size2


# --- 2. Database Registration & Listing Tests ---

def test_list_databases_endpoint(client: TestClient):
    """Verify GET /api/databases returns registered databases including Campus Intelligence."""
    response = client.get("/api/databases")
    assert response.status_code == 200
    databases = response.json()
    assert isinstance(databases, list)
    assert len(databases) >= 1

    demo = next((d for d in databases if d["id"] == DEMO_DB_ID), None)
    assert demo is not None
    assert demo["name"] == DEMO_DB_NAME
    assert demo["is_protected"] is True
    assert demo["table_count"] == 7
    assert demo["file_size_bytes"] > 0


def test_get_active_database_endpoint(client: TestClient):
    """Verify GET /api/databases/active returns the active database."""
    response = client.get("/api/databases/active")
    assert response.status_code == 200
    active_db = response.json()
    assert active_db["is_active"] is True
    assert "id" in active_db
    assert "name" in active_db


def test_activate_database_endpoint(client: TestClient):
    """Verify POST /api/databases/{id}/activate switches the active database."""
    response = client.post(f"/api/databases/{DEMO_DB_ID}/activate")
    assert response.status_code == 200
    active_db = response.json()
    assert active_db["id"] == DEMO_DB_ID
    assert active_db["is_active"] is True


def test_invalid_database_id_returns_404(client: TestClient):
    """Verify that querying or activating a non-existent database ID returns 404."""
    resp1 = client.get("/api/databases/non_existent_uuid_12345/schema")
    assert resp1.status_code == 404

    resp2 = client.post("/api/databases/non_existent_uuid_12345/activate")
    assert resp2.status_code == 404


# --- 3. Upload Validation & Security Tests ---

def test_valid_sqlite_upload(client: TestClient):
    """Verify that uploading a valid SQLite database registers it and returns metadata."""
    db_bytes = create_in_memory_sqlite_bytes()
    files = {"file": ("test_library.db", io.BytesIO(db_bytes), "application/x-sqlite3")}
    data = {"name": "Test Library DB"}

    response = client.post("/api/databases/upload", files=files, data=data)
    assert response.status_code == 201
    resp_data = response.json()
    assert "database" in resp_data
    db = resp_data["database"]
    assert db["name"] == "Test Library DB"
    assert db["is_protected"] is False
    assert db["table_count"] == 2
    assert db["file_size_bytes"] == len(db_bytes)

    # Clean up by unregistering
    del_resp = client.delete(f"/api/databases/{db['id']}?delete_file=true")
    assert del_resp.status_code == 200


def test_invalid_extension_upload_rejection(client: TestClient):
    """Verify that uploading a file with an invalid extension is rejected with 400."""
    files = {"file": ("test.txt", io.BytesIO(b"Hello text file"), "text/plain")}
    response = client.post("/api/databases/upload", files=files)
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["error"]["message"]


def test_empty_file_upload_rejection(client: TestClient):
    """Verify that uploading an empty 0-byte file is rejected with 400."""
    files = {"file": ("empty.db", io.BytesIO(b""), "application/x-sqlite3")}
    response = client.post("/api/databases/upload", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["error"]["message"].lower()


def test_malformed_sqlite_upload_rejection(client: TestClient):
    """Verify that uploading corrupt bytes named .db is rejected by integrity/header check."""
    fake_bytes = b"This is not a real SQLite database file content"
    files = {"file": ("corrupt.sqlite", io.BytesIO(fake_bytes), "application/x-sqlite3")}
    response = client.post("/api/databases/upload", files=files)
    assert response.status_code == 400
    assert "magic header" in response.json()["error"]["message"]


def test_oversized_upload_rejection():
    """Verify that DatabaseManager enforces the max upload size limit while streaming."""
    manager = get_database_manager()
    huge_stream = io.BytesIO(b"X" * 1024)  # Small stream but low max
    with pytest.raises(ValueError, match="exceeds maximum allowed size"):
        manager.upload_and_register_database(
            file_stream=huge_stream,
            original_filename="large.db",
            max_bytes=512,  # Limit is 512 bytes
        )


def test_path_traversal_rejection():
    """Verify that attempted path traversal in filenames is prevented."""
    manager = get_database_manager()
    safe_path = manager.resolve_safe_path("../../../etc/passwd.db")
    # Must resolve safely inside databases_dir, taking only the basename
    assert safe_path.parent == manager.databases_dir.resolve()
    assert safe_path.name == "passwd.db"


def test_protected_database_cannot_be_deleted(client: TestClient):
    """Verify that attempting to delete the bundled Campus Intelligence database returns 403."""
    response = client.delete(f"/api/databases/{DEMO_DB_ID}")
    assert response.status_code == 403
    assert "protected" in response.json()["error"]["message"].lower()


# --- 4. Schema Introspection & Column Tests ---

def test_schema_introspection_tables_and_columns(client: TestClient):
    """Verify GET /api/databases/{id}/schema returns accurate table and column metadata."""
    response = client.get(f"/api/databases/{DEMO_DB_ID}/schema")
    assert response.status_code == 200
    data = response.json()

    assert data["dialect"] == "sqlite"
    assert data["total_tables"] == 7
    assert data["total_columns"] == 40
    assert data["total_relationships"] == 9

    tables = {t["name"]: t for t in data["tables"]}
    assert "departments" in tables
    assert "students" in tables
    assert "courses" in tables

    # Verify departments columns
    dept_table = tables["departments"]
    col_names = [c["name"] for c in dept_table["columns"]]
    assert col_names == ["department_id", "department_name", "building", "budget"]
    assert dept_table["row_count"] == 5

    # Verify primary key detection
    assert dept_table["primary_keys"] == ["department_id"]
    dept_id_col = next(c for c in dept_table["columns"] if c["name"] == "department_id")
    assert dept_id_col["primary_key"] is True


def test_primary_key_and_foreign_key_detection(client: TestClient):
    """Verify that foreign keys and referential targets are properly extracted."""
    response = client.get(f"/api/databases/{DEMO_DB_ID}/schema")
    assert response.status_code == 200
    data = response.json()

    tables = {t["name"]: t for t in data["tables"]}
    students_table = tables["students"]

    # Student has FK department_id -> departments(department_id)
    dept_fk = next((fk for fk in students_table["foreign_keys"] if fk["from_column"] == "department_id"), None)
    assert dept_fk is not None
    assert dept_fk["to_table"] == "departments"
    assert dept_fk["to_column"] == "department_id"

    # Verify column object also reflects foreign key target
    dept_col = next(c for c in students_table["columns"] if c["name"] == "department_id")
    assert dept_col["is_foreign_key"] is True
    assert dept_col["fk_target_table"] == "departments"
    assert dept_col["fk_target_column"] == "department_id"


def test_composite_primary_key_handling(client: TestClient):
    """Verify that composite primary keys are accurately extracted with positions."""
    db_bytes = create_in_memory_sqlite_bytes(include_composite_pk=True)
    files = {"file": ("composite_test.db", io.BytesIO(db_bytes), "application/x-sqlite3")}
    upload_res = client.post("/api/databases/upload", files=files)
    assert upload_res.status_code == 201
    db_id = upload_res.json()["database"]["id"]

    try:
        schema_res = client.get(f"/api/databases/{db_id}/schema")
        assert schema_res.status_code == 200
        tables = {t["name"]: t for t in schema_res.json()["tables"]}
        cat_table = tables["book_categories"]

        assert "book_id" in cat_table["primary_keys"]
        assert "category_id" in cat_table["primary_keys"]
        assert len(cat_table["primary_keys"]) == 2

        book_id_col = next(c for c in cat_table["columns"] if c["name"] == "book_id")
        cat_id_col = next(c for c in cat_table["columns"] if c["name"] == "category_id")
        assert book_id_col["primary_key"] is True
        assert cat_id_col["primary_key"] is True
        assert book_id_col["pk_position"] == 1
        assert cat_id_col["pk_position"] == 2
    finally:
        client.delete(f"/api/databases/{db_id}?delete_file=true")


def test_relationships_endpoint(client: TestClient):
    """Verify GET /api/databases/{id}/relationships returns declared relationships."""
    response = client.get(f"/api/databases/{DEMO_DB_ID}/relationships")
    assert response.status_code == 200
    rels = response.json()
    assert len(rels) == 9

    # Check that courses -> departments exists
    course_dept = next((r for r in rels if r["source_table"] == "courses" and r["target_table"] == "departments"), None)
    assert course_dept is not None
    assert course_dept["source_column"] == "department_id"
    assert course_dept["target_column"] == "department_id"


# --- 5. Table Preview & Security Tests ---

def test_table_preview_bounded_records(client: TestClient):
    """Verify GET /api/databases/{id}/tables/{name}/preview returns rows and columns."""
    response = client.get(f"/api/databases/{DEMO_DB_ID}/tables/departments/preview?limit=10&offset=0")
    assert response.status_code == 200
    data = response.json()

    assert data["database_id"] == DEMO_DB_ID
    assert data["table_name"] == "departments"
    assert data["total_rows"] == 5
    assert len(data["rows"]) == 5
    assert "department_id" in data["columns"]
    assert "budget" in data["columns"]
    assert data["column_types"]["department_id"] == "VARCHAR(10)"


def test_table_preview_pagination(client: TestClient):
    """Verify pagination limit and offset behavior in table preview."""
    resp1 = client.get(f"/api/databases/{DEMO_DB_ID}/tables/students/preview?limit=5&offset=0")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert len(data1["rows"]) == 5
    assert data1["is_truncated"] is True
    first_stu_id = data1["rows"][0]["student_id"]

    resp2 = client.get(f"/api/databases/{DEMO_DB_ID}/tables/students/preview?limit=5&offset=5")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2["rows"]) == 5
    second_page_first_id = data2["rows"][0]["student_id"]

    assert first_stu_id != second_page_first_id


def test_table_preview_invalid_table_404(client: TestClient):
    """Verify that requesting preview for a non-existent table returns 404."""
    response = client.get(f"/api/databases/{DEMO_DB_ID}/tables/non_existent_table/preview")
    assert response.status_code == 404


def test_table_preview_unsafe_table_identifier_rejected(client: TestClient):
    """Verify that dangerous identifiers with semicolons or quotes are rejected."""
    assert is_safe_identifier("students; DROP TABLE students;--") is False
    assert is_safe_identifier("students\x00extra") is False
    assert is_safe_identifier("students") is True


def test_read_only_authorizer_denies_writes(tmp_path: Path):
    """Verify that the SQLite read-only authorizer strictly denies INSERT/UPDATE/DELETE."""
    test_db = tmp_path / "ro_test.db"
    seed_campus_intelligence_db(test_db)

    with get_read_only_connection(test_db) as conn:
        cursor = conn.cursor()
        # SELECT is allowed
        cursor.execute("SELECT count(*) FROM students;")
        assert cursor.fetchone()[0] == 25

        # INSERT must be blocked
        with pytest.raises(sqlite3.DatabaseError):
            cursor.execute("INSERT INTO departments (department_id, department_name, building, budget) VALUES ('D-FAIL', 'Fail', 'Hall', 0);")

        # DROP TABLE must be blocked
        with pytest.raises(sqlite3.DatabaseError):
            cursor.execute("DROP TABLE students;")


# --- 6. Schema Context Serialization Tests ---

def test_schema_context_serialization(client: TestClient):
    """Verify GET /api/databases/{id}/schema-context returns prompt-ready LLM context."""
    response = client.get(f"/api/databases/{DEMO_DB_ID}/schema-context")
    assert response.status_code == 200
    data = response.json()

    assert data["database_id"] == DEMO_DB_ID
    assert data["dialect"] == "sqlite"
    assert data["token_estimate"] > 0

    ctx = data["prompt_schema_context"]
    assert "### Database: Campus Intelligence" in ctx
    assert "departments" in ctx
    assert "students" in ctx
    assert "courses" in ctx
    assert "PRIMARY KEY" in ctx
    assert "REFERENCES" in ctx
    assert "Relational Foreign Key Graph:" in ctx
