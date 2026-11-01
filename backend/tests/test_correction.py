"""Unit and integration tests for execution-guided SQL self-correction loop."""

import pytest
from starlette.testclient import TestClient

from app.db.seed_demo import DEMO_DB_ID
from app.schemas.execution import AIQueryRequest
from app.services.ai_provider import MockAIProvider, set_ai_provider
from app.services.correction_service import CorrectionService, get_correction_service, normalize_sql
from app.services.interfaces import SQLCorrectionResult, SQLGenerationResult


def test_normalize_sql_equality():
    """Verify normalize_sql strips extra whitespace and trailing semicolons for loop detection."""
    sql1 = "SELECT  *  FROM students ;"
    sql2 = "select * from students"
    assert normalize_sql(sql1) == normalize_sql(sql2)


@pytest.mark.anyio
async def test_correction_success_first_attempt():
    """Verify query that succeeds on attempt 1 returns success_first_attempt without repairs."""
    set_ai_provider(MockAIProvider())
    svc = get_correction_service()

    req = AIQueryRequest(
        question="Show top 5 students by GPA",
        database_id=DEMO_DB_ID,
        auto_correct=True,
    )
    res = await svc.run_query_workflow(req)

    assert res.final_status == "success_first_attempt"
    assert res.total_correction_attempts == 0
    assert len(res.correction_trace) == 1
    assert res.correction_trace[0].attempt_number == 1
    assert res.correction_trace[0].attempt_type == "initial"
    assert res.correction_trace[0].is_accepted is True
    assert res.execution is not None
    assert res.execution.status == "success"
    assert res.execution.row_count == 5


@pytest.mark.anyio
async def test_correction_succeeds_on_second_attempt():
    """Verify query with schema mismatch on attempt 1 is repaired on attempt 2."""
    class FailingFirstMock(MockAIProvider):
        def __init__(self):
            super().__init__()
            self.attempt = 0

        async def generate_sql(self, question, schema, dialect="sqlite", context=None):
            return SQLGenerationResult(
                sql="SELECT student_name, gpa FROM students ORDER BY gpa DESC LIMIT 5;",
                explanation="Initial candidate with hallucinated column student_name",
            )

        async def generate_correction(self, question, failed_sql, error_category, error_message, schema, dialect="sqlite", context=None):
            return SQLCorrectionResult(
                sql="SELECT first_name, last_name, gpa FROM students ORDER BY gpa DESC LIMIT 5;",
                explanation="Repaired column to first_name, last_name based on schema",
                changes_made=["Replaced 'student_name' with 'first_name, last_name'"],
            )

    set_ai_provider(FailingFirstMock())
    svc = get_correction_service()

    req = AIQueryRequest(
        question="Show top 5 students by GPA",
        database_id=DEMO_DB_ID,
        auto_correct=True,
    )
    res = await svc.run_query_workflow(req)

    assert res.final_status == "success_after_correction"
    assert res.total_correction_attempts == 1
    assert len(res.correction_trace) == 2

    # Attempt 1 failed validation
    att1 = res.correction_trace[0]
    assert att1.attempt_number == 1
    assert att1.attempt_type == "initial"
    assert att1.validation_status == "schema_mismatch"
    assert att1.error_category == "UNKNOWN_COLUMN"
    assert att1.is_accepted is False

    # Attempt 2 succeeded
    att2 = res.correction_trace[1]
    assert att2.attempt_number == 2
    assert att2.attempt_type == "correction"
    assert att2.validation_status == "valid"
    assert att2.execution_status == "success"
    assert att2.is_accepted is True
    assert "Replaced 'student_name'" in att2.changes_made[0]


@pytest.mark.anyio
async def test_correction_exhausted_retries():
    """Verify loop terminates with correction_exhausted when repair candidate persistently fails."""
    counter = 0

    class PersistentFailMock(MockAIProvider):
        async def generate_sql(self, question, schema, dialect="sqlite", context=None):
            return SQLGenerationResult(
                sql="SELECT invalid_col_1 FROM students;",
                explanation="Initial failure",
            )

        async def generate_correction(self, question, failed_sql, error_category, error_message, schema, dialect="sqlite", context=None):
            nonlocal counter
            counter += 1
            return SQLCorrectionResult(
                sql=f"SELECT invalid_col_{counter + 1} FROM students;",
                explanation="Another failing column attempt",
                changes_made=[f"Tried invalid_col_{counter + 1}"],
            )

    set_ai_provider(PersistentFailMock())
    svc = get_correction_service()

    req = AIQueryRequest(
        question="Show students",
        database_id=DEMO_DB_ID,
        auto_correct=True,
        max_corrections=2,
    )
    res = await svc.run_query_workflow(req)

    assert res.final_status == "correction_exhausted"
    assert res.total_correction_attempts == 2
    assert len(res.correction_trace) == 3  # 1 initial + 2 corrections
    assert all(not a.is_accepted for a in res.correction_trace)


@pytest.mark.anyio
async def test_correction_repeated_candidate_loop_guard():
    """Verify that if model generates the exact same SQL, loop stops immediately."""
    class LoopMock(MockAIProvider):
        async def generate_sql(self, question, schema, dialect="sqlite", context=None):
            return SQLGenerationResult(
                sql="SELECT bad_col FROM students;",
                explanation="Initial bad column",
            )

        async def generate_correction(self, question, failed_sql, error_category, error_message, schema, dialect="sqlite", context=None):
            # Model returns identical failing SQL
            return SQLCorrectionResult(
                sql="SELECT bad_col FROM students;",
                explanation="Did not fix the column",
            )

    set_ai_provider(LoopMock())
    svc = get_correction_service()

    req = AIQueryRequest(
        question="Show students",
        database_id=DEMO_DB_ID,
        auto_correct=True,
        max_corrections=3,
    )
    res = await svc.run_query_workflow(req)

    assert res.final_status == "correction_exhausted"
    # Should stop after attempt 2 because candidate was repeated
    assert len(res.correction_trace) == 2
    assert res.correction_trace[1].error_category == "REPEATED_CANDIDATE"


@pytest.mark.anyio
async def test_correction_terminal_unsafe_stop():
    """Verify that destructive/unsafe SQL candidate immediately terminates with unsafe_rejected."""
    class UnsafeMock(MockAIProvider):
        async def generate_sql(self, question, schema, dialect="sqlite", context=None):
            return SQLGenerationResult(
                sql="DROP TABLE students;",
                explanation="Unsafe DDL statement",
            )

    set_ai_provider(UnsafeMock())
    svc = get_correction_service()

    req = AIQueryRequest(
        question="Drop the database",
        database_id=DEMO_DB_ID,
        auto_correct=True,
    )
    res = await svc.run_query_workflow(req)

    assert res.final_status == "unsafe_rejected"
    assert len(res.correction_trace) == 1
    assert res.correction_trace[0].validation_status == "unsafe"
    assert res.execution is None


@pytest.mark.anyio
async def test_correction_disabled_workflow():
    """Verify auto_correct=False does not trigger correction even if initial query fails."""
    class FailMock(MockAIProvider):
        async def generate_sql(self, question, schema, dialect="sqlite", context=None):
            return SQLGenerationResult(
                sql="SELECT nonexistent FROM students;",
                explanation="Failing query",
            )

    set_ai_provider(FailMock())
    svc = get_correction_service()

    req = AIQueryRequest(
        question="List students",
        database_id=DEMO_DB_ID,
        auto_correct=False,
    )
    res = await svc.run_query_workflow(req)

    assert res.final_status == "failed_validation"
    assert res.total_correction_attempts == 0
    assert len(res.correction_trace) == 1


@pytest.mark.anyio
async def test_correction_succeeds_on_second_correction_attempt_3():
    """Verify that a query failing on attempt 1 and attempt 2 succeeds on attempt 3 (second correction)."""
    class TwoFailMock(MockAIProvider):
        def __init__(self):
            super().__init__()
            self.corr_count = 0

        async def generate_sql(self, question, schema, dialect="sqlite", context=None):
            return SQLGenerationResult(
                sql="SELECT bad_col_1 FROM students;",
                explanation="Initial failure attempt 1",
            )

        async def generate_correction(self, question, failed_sql, error_category, error_message, schema, dialect="sqlite", context=None):
            self.corr_count += 1
            if self.corr_count == 1:
                return SQLCorrectionResult(
                    sql="SELECT bad_col_2 FROM students;",
                    explanation="First correction still fails with unknown column",
                    changes_made=["Changed to bad_col_2"],
                )
            return SQLCorrectionResult(
                sql="SELECT student_id, first_name, gpa FROM students ORDER BY gpa DESC LIMIT 5;",
                explanation="Second correction fixes query to valid columns",
                changes_made=["Changed to verified columns student_id, first_name, gpa"],
            )

    set_ai_provider(TwoFailMock())
    svc = get_correction_service()

    req = AIQueryRequest(
        question="Show top students",
        database_id=DEMO_DB_ID,
        auto_correct=True,
        max_corrections=2,
    )
    res = await svc.run_query_workflow(req)

    assert res.final_status == "success_after_correction"
    assert res.total_correction_attempts == 2
    assert len(res.correction_trace) == 3
    assert res.correction_trace[0].attempt_number == 1
    assert res.correction_trace[0].is_accepted is False
    assert res.correction_trace[1].attempt_number == 2
    assert res.correction_trace[1].is_accepted is False
    assert res.correction_trace[2].attempt_number == 3
    assert res.correction_trace[2].is_accepted is True
    assert res.execution.status == "success"


@pytest.mark.anyio
async def test_correction_model_unavailable_exception():
    """Verify that ModelUnavailableException terminates workflow gracefully."""
    from app.core.exceptions import ModelUnavailableException

    class UnavailableMock(MockAIProvider):
        async def generate_sql(self, question, schema, dialect="sqlite", context=None):
            raise ModelUnavailableException("Model weights failed to load")

    set_ai_provider(UnavailableMock())
    svc = get_correction_service()

    req = AIQueryRequest(
        question="Show students",
        database_id=DEMO_DB_ID,
        auto_correct=True,
    )
    res = await svc.run_query_workflow(req)

    assert res.final_status == "model_unavailable"
    assert len(res.correction_trace) == 0


@pytest.mark.anyio
async def test_correction_unsafe_candidate_in_correction_step():
    """Verify that if model generates unsafe DDL during correction, loop halts immediately."""
    class EvilCorrectionMock(MockAIProvider):
        async def generate_sql(self, question, schema, dialect="sqlite", context=None):
            return SQLGenerationResult(
                sql="SELECT invalid_col FROM students;",
                explanation="Initial failure",
            )

        async def generate_correction(self, question, failed_sql, error_category, error_message, schema, dialect="sqlite", context=None):
            return SQLCorrectionResult(
                sql="DROP TABLE students;",
                explanation="Model maliciously generates DROP TABLE during repair",
            )

    set_ai_provider(EvilCorrectionMock())
    svc = get_correction_service()

    req = AIQueryRequest(
        question="Show students",
        database_id=DEMO_DB_ID,
        auto_correct=True,
        max_corrections=2,
    )
    res = await svc.run_query_workflow(req)

    assert res.final_status == "unsafe_rejected"
    assert len(res.correction_trace) == 2
    assert res.correction_trace[1].validation_status == "unsafe"
    assert res.correction_trace[1].error_category == "UNSAFE_SQL"
    assert res.execution is None


@pytest.mark.anyio
async def test_correction_execution_error_feedback_delivered():
    """Verify that runtime execution diagnostics (e.g. division by zero or SQLite error) are fed into correction."""
    received_error_msg = None
    received_category = None

    class ExecutionFeedbackMock(MockAIProvider):
        async def generate_sql(self, question, schema, dialect="sqlite", context=None):
            # Query passes AST validator, but will fail during SQLite execution (no such column in joined table)
            return SQLGenerationResult(
                sql="SELECT s.first_name FROM students s WHERE s.department_id = (SELECT nonexistent_subcol FROM departments);",
                explanation="Valid AST syntax, but runtime SQLite error",
            )

        async def generate_correction(self, question, failed_sql, error_category, error_message, schema, dialect="sqlite", context=None):
            nonlocal received_error_msg, received_category
            received_category = error_category
            received_error_msg = error_message
            return SQLCorrectionResult(
                sql="SELECT first_name FROM students LIMIT 5;",
                explanation="Repaired to simple working query",
                changes_made=["Removed failing subquery"],
            )

    set_ai_provider(ExecutionFeedbackMock())
    svc = get_correction_service()

    req = AIQueryRequest(
        question="Show students",
        database_id=DEMO_DB_ID,
        auto_correct=True,
    )
    res = await svc.run_query_workflow(req)

    assert res.final_status == "success_after_correction"
    assert received_category in ("UNKNOWN_COLUMN", "EXECUTION_ERROR")
    assert "nonexistent_subcol" in received_error_msg


# --- API INTEGRATION TESTS ---


def test_api_ai_query_endpoint_success(client: TestClient):
    """Test POST /api/ai/query returns full result and correction trace."""
    set_ai_provider(MockAIProvider())
    payload = {
        "question": "Show top 5 students by GPA",
        "database_id": DEMO_DB_ID,
        "auto_correct": True,
    }
    resp = client.post("/api/ai/query", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["final_status"] == "success_first_attempt"
    assert data["initial_sql"] != ""
    assert data["final_sql"] != ""
    assert "execution" in data
    assert data["execution"]["status"] == "success"
    assert len(data["correction_trace"]) == 1
    assert data["correction_trace"][0]["is_accepted"] is True


def test_api_ai_query_backward_compatibility_generate_sql(client: TestClient):
    """Verify that POST /api/ai/generate-sql still exists and does not execute queries."""
    set_ai_provider(MockAIProvider())
    payload = {
        "question": "Show top 5 students by GPA",
        "database_id": DEMO_DB_ID,
    }
    resp = client.post("/api/ai/generate-sql", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "sql" in data
    assert "validation" in data
    assert data["execution"]["status"] == "not_executed"  # Generate-only endpoint does not execute

