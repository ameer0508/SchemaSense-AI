"""Server-Side Analytics Aggregation Service.

Derives honest, non-fabricated metrics and insights directly from persisted history in SQLite.
- Strictly handles zero denominators returning None / N/A.
- Computes genuine first-attempt vs self-corrected vs failure distributions.
- Prepares daily time-series and error-category taxonomies for UI charts.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import sqlite3

from app.core.logging import get_logger
from app.schemas.analytics import (
    AnalyticsErrorsResponse,
    AnalyticsOverviewResponse,
    AnalyticsTimeseriesResponse,
    ErrorCategoryStat,
    TimeseriesPoint,
)
from app.services.history_service import HistoryService, get_history_service

logger = get_logger("analytics_service")


class AnalyticsService:
    """Aggregates metrics and historical trends from the query history database."""

    def __init__(self, history_service: Optional[HistoryService] = None):
        self.history_service = history_service or get_history_service()

    def _get_connection(self) -> sqlite3.Connection:
        """Reuse connection to history database."""
        return self.history_service._get_connection()

    def get_overview(self, days: Optional[int] = None) -> AnalyticsOverviewResponse:
        """Compute top-level summary metrics with zero-division safety."""
        where_clause = ""
        params: List[str] = []
        if days and days > 0:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            where_clause = "WHERE created_at >= ?"
            params.append(cutoff)

        sql = f"""
            SELECT
                COUNT(*) AS total_queries,
                SUM(CASE WHEN final_status = 'success' AND correction_count = 0 THEN 1 ELSE 0 END) AS first_attempt_successes,
                SUM(CASE WHEN final_status = 'success' AND correction_count > 0 THEN 1 ELSE 0 END) AS successes_after_correction,
                SUM(CASE WHEN final_status != 'success' THEN 1 ELSE 0 END) AS total_failures,
                SUM(CASE WHEN correction_count > 0 THEN 1 ELSE 0 END) AS total_correction_attempts,
                AVG(CASE WHEN generation_duration_ms > 0 THEN generation_duration_ms ELSE NULL END) AS avg_gen_duration,
                AVG(CASE WHEN execution_duration_ms > 0 THEN execution_duration_ms ELSE NULL END) AS avg_exec_duration,
                AVG(CASE WHEN total_duration_ms > 0 THEN total_duration_ms ELSE NULL END) AS avg_total_duration
            FROM query_history
            {where_clause};
        """

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                row = cursor.fetchone()

                total_queries = row["total_queries"] or 0
                first_attempt = row["first_attempt_successes"] or 0
                corrected = row["successes_after_correction"] or 0
                failures = row["total_failures"] or 0
                correction_attempts = row["total_correction_attempts"] or 0

                # Calculate rates safely (null if zero denominator)
                first_attempt_rate = (
                    round(first_attempt / total_queries, 4) if total_queries > 0 else None
                )
                correction_rate = (
                    round(corrected / correction_attempts, 4) if correction_attempts > 0 else None
                )
                overall_rate = (
                    round((first_attempt + corrected) / total_queries, 4) if total_queries > 0 else None
                )

                avg_gen = round(row["avg_gen_duration"], 2) if row["avg_gen_duration"] is not None else None
                avg_exec = round(row["avg_exec_duration"], 2) if row["avg_exec_duration"] is not None else None
                avg_total = round(row["avg_total_duration"], 2) if row["avg_total_duration"] is not None else None

                # Most used database
                cursor.execute(
                    f"""
                    SELECT database_name, COUNT(*) AS count
                    FROM query_history
                    {where_clause}
                    GROUP BY database_id
                    ORDER BY count DESC
                    LIMIT 1;
                    """,
                    params,
                )
                top_db_row = cursor.fetchone()
                most_used_db = top_db_row["database_name"] if top_db_row else None

                # Most common error category
                cursor.execute(
                    f"""
                    SELECT error_category, COUNT(*) AS count
                    FROM query_history
                    WHERE error_category IS NOT NULL AND error_category != ''
                    {("AND created_at >= ?" if where_clause else "")}
                    GROUP BY error_category
                    ORDER BY count DESC
                    LIMIT 1;
                    """,
                    params if where_clause else [],
                )
                top_err_row = cursor.fetchone()
                most_common_error = top_err_row["error_category"] if top_err_row else None

                return AnalyticsOverviewResponse(
                    total_queries=total_queries,
                    first_attempt_successes=first_attempt,
                    successes_after_correction=corrected,
                    total_failures=failures,
                    total_correction_attempts=correction_attempts,
                    first_attempt_success_rate=first_attempt_rate,
                    correction_success_rate=correction_rate,
                    overall_success_rate=overall_rate,
                    avg_generation_duration_ms=avg_gen,
                    avg_execution_duration_ms=avg_exec,
                    avg_total_duration_ms=avg_total,
                    most_used_database=most_used_db,
                    most_common_error=most_common_error,
                )
        except Exception as e:
            logger.error(f"Error computing analytics overview: {e}")
            return AnalyticsOverviewResponse(
                total_queries=0,
                first_attempt_successes=0,
                successes_after_correction=0,
                total_failures=0,
                total_correction_attempts=0,
            )

    def get_timeseries(self, days: int = 14) -> AnalyticsTimeseriesResponse:
        """Generate daily query activity timeseries over the requested range."""
        safe_days = max(1, min(days, 90))
        today = datetime.now(timezone.utc).date()
        cutoff_date = today - timedelta(days=safe_days - 1)
        cutoff_iso = datetime(cutoff_date.year, cutoff_date.month, cutoff_date.day, tzinfo=timezone.utc).isoformat()

        sql = """
            SELECT
                SUBSTR(created_at, 1, 10) AS day_str,
                COUNT(*) AS total,
                SUM(CASE WHEN final_status = 'success' AND correction_count = 0 THEN 1 ELSE 0 END) AS first_attempt,
                SUM(CASE WHEN final_status = 'success' AND correction_count > 0 THEN 1 ELSE 0 END) AS corrected,
                SUM(CASE WHEN final_status != 'success' THEN 1 ELSE 0 END) AS failures
            FROM query_history
            WHERE created_at >= ?
            GROUP BY day_str
            ORDER BY day_str ASC;
        """

        data_map: Dict[str, Dict[str, int]] = {}
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, (cutoff_iso,))
                for row in cursor.fetchall():
                    data_map[row["day_str"]] = {
                        "total": row["total"] or 0,
                        "first_attempt": row["first_attempt"] or 0,
                        "corrected": row["corrected"] or 0,
                        "failures": row["failures"] or 0,
                    }
        except Exception as e:
            logger.error(f"Error generating analytics timeseries: {e}")

        # Fill continuous date sequence so frontend charts render smoothly
        points: List[TimeseriesPoint] = []
        for i in range(safe_days):
            current_day = cutoff_date + timedelta(days=i)
            day_str = current_day.isoformat()
            stats = data_map.get(day_str, {"total": 0, "first_attempt": 0, "corrected": 0, "failures": 0})
            points.append(
                TimeseriesPoint(
                    date=day_str,
                    total=stats["total"],
                    first_attempt_successes=stats["first_attempt"],
                    corrected_successes=stats["corrected"],
                    failures=stats["failures"],
                )
            )

        return AnalyticsTimeseriesResponse(
            points=points,
            range_days=safe_days,
        )

    def get_error_distribution(self, days: Optional[int] = None) -> AnalyticsErrorsResponse:
        """Categorize and count all error occurrences with percentage breakdown."""
        where_clause = "WHERE error_category IS NOT NULL AND error_category != ''"
        params: List[str] = []
        if days and days > 0:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            where_clause += " AND created_at >= ?"
            params.append(cutoff)

        sql = f"""
            SELECT error_category, COUNT(*) AS count
            FROM query_history
            {where_clause}
            GROUP BY error_category
            ORDER BY count DESC;
        """

        categories: List[ErrorCategoryStat] = []
        total_errors = 0

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql, params)
                rows = cursor.fetchall()

                total_errors = sum(row["count"] for row in rows)
                for row in rows:
                    cnt = row["count"]
                    pct = round((cnt / total_errors) * 100, 1) if total_errors > 0 else 0.0
                    categories.append(
                        ErrorCategoryStat(
                            category=row["error_category"],
                            count=cnt,
                            percentage=pct,
                        )
                    )
        except Exception as e:
            logger.error(f"Error fetching error distribution: {e}")

        return AnalyticsErrorsResponse(
            categories=categories,
            total_errors=total_errors,
        )


_analytics_service_instance: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Retrieve singleton AnalyticsService instance."""
    global _analytics_service_instance
    if _analytics_service_instance is None:
        _analytics_service_instance = AnalyticsService()
    return _analytics_service_instance
