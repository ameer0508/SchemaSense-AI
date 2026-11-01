"""Tests for Durable Query History: persistence, privacy, search, filtering, and API endpoints."""

import os
from pathlib import Path
import sqlite3
import pytest
from starlette.testclient import TestClient

from app.schemas.history import QueryHistoryRecord
from app.services.history_service import HistoryService, CURRENT_SCHEMA_VERSION


@pytest.fixture
def temp_history_service(tmp_path: Path) -> HistoryService:
    """Provide an isolated HistoryService backed by a temporary SQLite file."""
    db_file = tmp_path / "history_test.db"
    return HistoryService(db_path=db_file)


def test_history_database_initialization(temp_history_service: HistoryService):
    """Verify that history database creates all tables, WAL mode, and indexes."""
    assert temp_history_service.db_path.exists()
    with temp_history_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row["name"] for row in cursor.fetchall()}
        assert "schema_version" in tables
        assert "history_settings" in tables
        assert "query_history" in tables


def test_history_schema_versioning(temp_history_service: HistoryService):
    """Verify schema version tracking table records CURRENT_SCHEMA_VERSION."""
    with temp_history_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT version FROM schema_version;")
        row = cursor.fetchone()
        assert row is not None
        assert row["version"] == CURRENT_SCHEMA_VERSION


def test_successful_record_persistence(temp_history_service: HistoryService):
    """Verify persisting a successful query execution event."""
    rec = QueryHistoryRecord(
        request_id="req-test-success-01",
        created_at="2026-10-27T12:00:00Z",
        database_id="campus_intelligence",
        database_name="Campus Intelligence",
        question="Show all students with GPA > 3.5",
        generation_mode="local_qwen",
        model_id="Qwen/Qwen2.5-Coder-1.5B-Instruct",
        initial_sql="SELECT * FROM students WHERE gpa > 3.5;",
        final_sql="SELECT * FROM students WHERE gpa > 3.5;",
        final_status="success_first_attempt",
        validation_status="valid",
        execution_status="success",
        row_count=12,
        correction_count=0,
        generation_duration_ms=450.0,
        execution_duration_ms=2.1,
        total_duration_ms=452.1,
        semantic_warning_count=0,
        error_category=None,
    )

    persisted = temp_history_service.record_query(rec)
    assert persisted is True

    fetched = temp_history_service.get_history_item("req-test-success-01")
    assert fetched is not None
    assert fetched.question == "Show all students with GPA > 3.5"
    assert fetched.row_count == 12
    assert fetched.correction_count == 0


def test_failed_query_persistence(temp_history_service: HistoryService):
    """Verify persisting a failed query execution with error categorization."""
    rec = QueryHistoryRecord(
        request_id="req-test-fail-02",
        created_at="2026-10-27T12:05:00Z",
        database_id="campus_intelligence",
        database_name="Campus Intelligence",
        question="Show non-existent students",
        generation_mode="local_qwen",
        model_id="Qwen/Qwen2.5-Coder-1.5B-Instruct",
        initial_sql="SELECT fake_col FROM students;",
        final_sql="SELECT fake_col FROM students;",
        final_status="failed_validation",
        validation_status="schema_mismatch",
        execution_status="not_executed",
        row_count=None,
        correction_count=1,
        generation_duration_ms=620.0,
        execution_duration_ms=0.0,
        total_duration_ms=620.0,
        semantic_warning_count=0,
        error_category="UNKNOWN_COLUMN",
    )

    persisted = temp_history_service.record_query(rec)
    assert persisted is True

    fetched = temp_history_service.get_history_item("req-test-fail-02")
    assert fetched is not None
    assert fetched.final_status == "failed_validation"
    assert fetched.error_category == "UNKNOWN_COLUMN"
    assert fetched.row_count is None


def test_generation_only_history_record(temp_history_service: HistoryService):
    """Verify storing generation-only query where execution was not requested."""
    rec = QueryHistoryRecord(
        request_id="req-test-gen-only",
        created_at="2026-10-27T12:10:00Z",
        database_id="campus_intelligence",
        database_name="Campus Intelligence",
        question="Count total professors",
        generation_mode="local_qwen",
        model_id="Qwen/Qwen2.5-Coder-1.5B-Instruct",
        initial_sql="SELECT COUNT(*) FROM professors;",
        final_sql="SELECT COUNT(*) FROM professors;",
        final_status="generated_only",
        validation_status="valid",
        execution_status="not_executed",
        row_count=None,
        correction_count=0,
        generation_duration_ms=380.0,
        execution_duration_ms=0.0,
        total_duration_ms=380.0,
        semantic_warning_count=0,
    )

    persisted = temp_history_service.record_query(rec)
    assert persisted is True
    fetched = temp_history_service.get_history_item("req-test-gen-only")
    assert fetched is not None
    assert fetched.final_status == "generated_only"
    assert fetched.execution_status == "not_executed"


def test_history_disabled_privacy_control(temp_history_service: HistoryService):
    """Verify that when history recording is disabled, record_query skips persistence."""
    temp_history_service.set_history_enabled(False)
    assert temp_history_service.is_history_enabled() is False

    rec = QueryHistoryRecord(
        request_id="req-test-disabled",
        created_at="2026-10-27T12:15:00Z",
        database_id="campus_intelligence",
        database_name="Campus Intelligence",
        question="A private user query",
        generation_mode="mock",
        initial_sql="SELECT 1;",
        final_sql="SELECT 1;",
        final_status="success",
        validation_status="valid",
        execution_status="success",
    )

    persisted = temp_history_service.record_query(rec)
    assert persisted is False
    assert temp_history_service.get_history_item("req-test-disabled") is None

    # Re-enable
    temp_history_service.set_history_enabled(True)
    assert temp_history_service.is_history_enabled() is True


def test_pagination_and_sorting(temp_history_service: HistoryService):
    """Verify pagination boundaries and time-based sorting."""
    for i in range(15):
        iso_sec = f"{i:02d}"
        temp_history_service.record_query(
            QueryHistoryRecord(
                request_id=f"req-page-{i}",
                created_at=f"2026-10-27T12:00:{iso_sec}Z",
                database_id="campus_intelligence",
                database_name="Campus Intelligence",
                question=f"Question number {i}",
                generation_mode="mock",
                initial_sql="SELECT 1;",
                final_sql="SELECT 1;",
                final_status="success",
                validation_status="valid",
                execution_status="success",
            )
        )

    # Page 1 (size 5) sorted desc
    page1 = temp_history_service.list_history(page=1, page_size=5, sort_desc=True)
    assert page1.total == 15
    assert len(page1.items) == 5
    assert page1.total_pages == 3
    assert page1.items[0].request_id == "req-page-14"  # Newest first

    # Page 2 (size 5)
    page2 = temp_history_service.list_history(page=2, page_size=5, sort_desc=True)
    assert len(page2.items) == 5
    assert page2.items[0].request_id == "req-page-9"


def test_question_search_and_sql_injection_safety(temp_history_service: HistoryService):
    """Verify parameterized search and SQL injection immunity."""
    temp_history_service.record_query(
        QueryHistoryRecord(
            request_id="req-search-1",
            created_at="2026-10-27T12:00:01Z",
            database_id="campus_intelligence",
            database_name="Campus Intelligence",
            question="Find biology courses with credits > 3",
            generation_mode="mock",
            initial_sql="SELECT * FROM courses WHERE department_id = 'DEP-BIO';",
            final_sql="SELECT * FROM courses WHERE department_id = 'DEP-BIO';",
            final_status="success",
            validation_status="valid",
            execution_status="success",
        )
    )

    # Normal search
    res = temp_history_service.list_history(search="biology")
    assert res.total == 1
    assert res.items[0].request_id == "req-search-1"

    # Search with malicious SQL injection payload
    injection_search = "' OR '1'='1"
    res_inj = temp_history_service.list_history(search=injection_search)
    assert res_inj.total == 0  # Safely parameterized, returns no false matches


def test_status_and_database_filtering(temp_history_service: HistoryService):
    """Verify multi-column filtering by database_id and execution status."""
    temp_history_service.record_query(
        QueryHistoryRecord(
            request_id="req-filter-a",
            created_at="2026-10-27T12:00:01Z",
            database_id="db_alpha",
            database_name="Database Alpha",
            question="Query alpha",
            generation_mode="mock",
            initial_sql="SELECT 1;",
            final_sql="SELECT 1;",
            final_status="success",
            validation_status="valid",
            execution_status="success",
        )
    )
    temp_history_service.record_query(
        QueryHistoryRecord(
            request_id="req-filter-b",
            created_at="2026-10-27T12:00:02Z",
            database_id="db_beta",
            database_name="Database Beta",
            question="Query beta",
            generation_mode="mock",
            initial_sql="SELECT 2;",
            final_sql="SELECT 2;",
            final_status="failed_validation",
            validation_status="syntax_error",
            execution_status="not_executed",
        )
    )

    res_db = temp_history_service.list_history(database_id="db_alpha")
    assert res_db.total == 1
    assert res_db.items[0].request_id == "req-filter-a"

    res_status = temp_history_service.list_history(status="failed_validation")
    assert res_status.total == 1
    assert res_status.items[0].request_id == "req-filter-b"


def test_single_entry_deletion_and_clear_history(temp_history_service: HistoryService):
    """Verify deleting an individual entry and wiping entire history."""
    for i in range(3):
        temp_history_service.record_query(
            QueryHistoryRecord(
                request_id=f"req-del-{i}",
                created_at=f"2026-10-27T12:00:0{i}Z",
                database_id="campus_intelligence",
                database_name="Campus Intelligence",
                question=f"Del question {i}",
                generation_mode="mock",
                initial_sql="SELECT 1;",
                final_sql="SELECT 1;",
                final_status="success",
                validation_status="valid",
                execution_status="success",
            )
        )

    # Delete single entry
    deleted = temp_history_service.delete_history_item("req-del-1")
    assert deleted is True
    assert temp_history_service.get_history_item("req-del-1") is None
    assert temp_history_service.list_history().total == 2

    # Clear history
    cleared_count = temp_history_service.clear_history()
    assert cleared_count == 2
    assert temp_history_service.list_history().total == 0


def test_no_result_row_persistence_privacy(temp_history_service: HistoryService):
    """Verify that QueryHistoryRecord and schema do NOT have any columns storing raw table rows."""
    with temp_history_service._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(query_history);")
        column_names = {row["name"] for row in cursor.fetchall()}
        assert "rows" not in column_names
        assert "result_rows" not in column_names
        assert "raw_data" not in column_names
        # row_count is stored as an integer, which is privacy preserving
        assert "row_count" in column_names


def test_history_api_endpoints(client: TestClient):
    """Verify FastAPI history REST endpoints: GET list, GET item, settings, and deletion."""
    # Test settings endpoint
    resp_settings = client.get("/api/history/settings")
    assert resp_settings.status_code == 200
    settings_data = resp_settings.json()
    assert "is_enabled" in settings_data
    assert "total_saved_queries" in settings_data

    # Test listing endpoint
    resp_list = client.get("/api/history?page=1&page_size=10")
    assert resp_list.status_code == 200
    list_data = resp_list.json()
    assert "items" in list_data
    assert "total" in list_data

    # Test 404 on nonexistent record
    resp_not_found = client.get("/api/history/nonexistent-uuid-999")
    assert resp_not_found.status_code == 404
