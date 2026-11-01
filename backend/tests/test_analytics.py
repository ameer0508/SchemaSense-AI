"""Tests for Analytics: server-side aggregation, zero-division safety, rates, timeseries, and error taxonomies."""

from pathlib import Path
import pytest
from starlette.testclient import TestClient

from app.schemas.history import QueryHistoryRecord
from app.services.analytics_service import AnalyticsService
from app.services.history_service import HistoryService


@pytest.fixture
def temp_analytics_service(tmp_path: Path) -> AnalyticsService:
    """Provide an isolated AnalyticsService backed by a temporary history database."""
    db_file = tmp_path / "analytics_test.db"
    hist_svc = HistoryService(db_path=db_file)
    return AnalyticsService(history_service=hist_svc)


def test_empty_history_statistics_zero_division(temp_analytics_service: AnalyticsService):
    """Verify that an empty history database returns None/null for rates and averages (zero denominator safety)."""
    overview = temp_analytics_service.get_overview()
    assert overview.total_queries == 0
    assert overview.first_attempt_successes == 0
    assert overview.successes_after_correction == 0
    assert overview.total_failures == 0
    assert overview.total_correction_attempts == 0
    # Rates must be None (N/A) rather than 0% or raising ZeroDivisionError
    assert overview.first_attempt_success_rate is None
    assert overview.correction_success_rate is None
    assert overview.overall_success_rate is None
    assert overview.avg_generation_duration_ms is None
    assert overview.avg_execution_duration_ms is None
    assert overview.avg_total_duration_ms is None
    assert overview.most_used_database is None
    assert overview.most_common_error is None


def test_first_attempt_and_overall_success_calculation(temp_analytics_service: AnalyticsService):
    """Verify accurate first-attempt and overall success rate formulas."""
    hist = temp_analytics_service.history_service

    # 3 first attempt successes
    for i in range(3):
        hist.record_query(
            QueryHistoryRecord(
                request_id=f"req-first-{i}",
                created_at=f"2026-10-27T10:00:0{i}Z",
                database_id="db_main",
                database_name="Main DB",
                question="q",
                generation_mode="local_qwen",
                initial_sql="SELECT 1;",
                final_sql="SELECT 1;",
                final_status="success",
                validation_status="valid",
                execution_status="success",
                correction_count=0,
                generation_duration_ms=100.0,
                execution_duration_ms=10.0,
                total_duration_ms=110.0,
            )
        )

    # 1 corrected success
    hist.record_query(
        QueryHistoryRecord(
            request_id="req-corr-1",
            created_at="2026-10-27T10:00:10Z",
            database_id="db_main",
            database_name="Main DB",
            question="q",
            generation_mode="local_qwen",
            initial_sql="SELECT bad;",
            final_sql="SELECT good;",
            final_status="success",
            validation_status="valid",
            execution_status="success",
            correction_count=1,
            generation_duration_ms=200.0,
            execution_duration_ms=10.0,
            total_duration_ms=210.0,
        )
    )

    # 1 failed query
    hist.record_query(
        QueryHistoryRecord(
            request_id="req-fail-1",
            created_at="2026-10-27T10:00:20Z",
            database_id="db_main",
            database_name="Main DB",
            question="q",
            generation_mode="local_qwen",
            initial_sql="SELECT bad;",
            final_sql="SELECT bad;",
            final_status="failed_validation",
            validation_status="schema_mismatch",
            execution_status="not_executed",
            correction_count=1,
            generation_duration_ms=150.0,
            execution_duration_ms=0.0,
            total_duration_ms=150.0,
            error_category="UNKNOWN_COLUMN",
        )
    )

    overview = temp_analytics_service.get_overview()
    assert overview.total_queries == 5
    assert overview.first_attempt_successes == 3
    assert overview.successes_after_correction == 1
    assert overview.total_failures == 1
    assert overview.total_correction_attempts == 2

    # first_attempt_success_rate = 3 / 5 = 0.6
    assert overview.first_attempt_success_rate == 0.6
    # correction_success_rate = 1 / 2 = 0.5 (1 corrected out of 2 that attempted correction)
    assert overview.correction_success_rate == 0.5
    # overall_success_rate = (3 + 1) / 5 = 0.8
    assert overview.overall_success_rate == 0.8


def test_average_latency_calculation(temp_analytics_service: AnalyticsService):
    """Verify average generation, execution, and total latency calculation."""
    hist = temp_analytics_service.history_service

    hist.record_query(
        QueryHistoryRecord(
            request_id="req-lat-1",
            created_at="2026-10-27T10:00:01Z",
            database_id="db_main",
            database_name="Main DB",
            question="q",
            generation_mode="mock",
            initial_sql="SELECT 1;",
            final_sql="SELECT 1;",
            final_status="success",
            validation_status="valid",
            execution_status="success",
            generation_duration_ms=100.0,
            execution_duration_ms=20.0,
            total_duration_ms=120.0,
        )
    )
    hist.record_query(
        QueryHistoryRecord(
            request_id="req-lat-2",
            created_at="2026-10-27T10:00:02Z",
            database_id="db_main",
            database_name="Main DB",
            question="q",
            generation_mode="mock",
            initial_sql="SELECT 1;",
            final_sql="SELECT 1;",
            final_status="success",
            validation_status="valid",
            execution_status="success",
            generation_duration_ms=300.0,
            execution_duration_ms=40.0,
            total_duration_ms=340.0,
        )
    )

    overview = temp_analytics_service.get_overview()
    # (100 + 300) / 2 = 200.0
    assert overview.avg_generation_duration_ms == 200.0
    # (20 + 40) / 2 = 30.0
    assert overview.avg_execution_duration_ms == 30.0
    # (120 + 340) / 2 = 230.0
    assert overview.avg_total_duration_ms == 230.0


def test_timeseries_aggregation_continuous_dates(temp_analytics_service: AnalyticsService):
    """Verify daily query volume aggregation produces continuous date sequence without gaps."""
    from datetime import datetime, timezone
    today_str = datetime.now(timezone.utc).date().isoformat()

    hist = temp_analytics_service.history_service
    hist.record_query(
        QueryHistoryRecord(
            request_id="req-ts-1",
            created_at=f"{today_str}T11:00:00Z",
            database_id="db_main",
            database_name="Main DB",
            question="q",
            generation_mode="mock",
            initial_sql="SELECT 1;",
            final_sql="SELECT 1;",
            final_status="success",
            validation_status="valid",
            execution_status="success",
            correction_count=0,
        )
    )

    ts_resp = temp_analytics_service.get_timeseries(days=7)
    assert ts_resp.range_days == 7
    assert len(ts_resp.points) == 7

    # The last point should be today
    today_point = ts_resp.points[-1]
    assert today_point.date == today_str
    assert today_point.total == 1
    assert today_point.first_attempt_successes == 1


def test_error_taxonomy_grouping_and_percentages(temp_analytics_service: AnalyticsService):
    """Verify categorizing errors by frequency and computing percentages correctly."""
    hist = temp_analytics_service.history_service

    # 3 UNKNOWN_COLUMN errors
    for i in range(3):
        hist.record_query(
            QueryHistoryRecord(
                request_id=f"req-err-col-{i}",
                created_at="2026-10-27T10:00:00Z",
                database_id="db_main",
                database_name="Main DB",
                question="q",
                generation_mode="mock",
                initial_sql="SELECT col;",
                final_sql="SELECT col;",
                final_status="failed_validation",
                validation_status="schema_mismatch",
                execution_status="not_executed",
                error_category="UNKNOWN_COLUMN",
            )
        )

    # 1 SYNTAX_ERROR
    hist.record_query(
        QueryHistoryRecord(
            request_id="req-err-syn-1",
            created_at="2026-10-27T10:00:00Z",
            database_id="db_main",
            database_name="Main DB",
            question="q",
            generation_mode="mock",
            initial_sql="SELECT ;",
            final_sql="SELECT ;",
            final_status="failed_validation",
            validation_status="syntax_error",
            execution_status="not_executed",
            error_category="SYNTAX_ERROR",
        )
    )

    err_resp = temp_analytics_service.get_error_distribution()
    assert err_resp.total_errors == 4
    assert len(err_resp.categories) == 2

    # Most frequent first
    top_err = err_resp.categories[0]
    assert top_err.category == "UNKNOWN_COLUMN"
    assert top_err.count == 3
    assert top_err.percentage == 75.0

    second_err = err_resp.categories[1]
    assert second_err.category == "SYNTAX_ERROR"
    assert second_err.count == 1
    assert second_err.percentage == 25.0


def test_analytics_api_endpoints(client: TestClient):
    """Verify FastAPI analytics endpoints: /api/analytics/overview, /timeseries, and /errors."""
    resp_overview = client.get("/api/analytics/overview")
    assert resp_overview.status_code == 200
    data_overview = resp_overview.json()
    assert "total_queries" in data_overview

    resp_ts = client.get("/api/analytics/timeseries?days=7")
    assert resp_ts.status_code == 200
    data_ts = resp_ts.json()
    assert "points" in data_ts
    assert len(data_ts["points"]) == 7

    resp_err = client.get("/api/analytics/errors")
    assert resp_err.status_code == 200
    data_err = resp_err.json()
    assert "categories" in data_err
    assert "total_errors" in data_err
