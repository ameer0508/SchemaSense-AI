"""Pydantic schemas for Trustworthy Analytics and Metrics."""

from typing import List, Optional
from pydantic import BaseModel, Field


class AnalyticsOverviewResponse(BaseModel):
    """Server-aggregated overall performance and reliability metrics."""

    total_queries: int = Field(..., description="Total executed query workflows recorded")
    first_attempt_successes: int = Field(..., description="Queries succeeded on attempt 1 without correction")
    successes_after_correction: int = Field(..., description="Queries succeeded after self-correction")
    total_failures: int = Field(..., description="Queries that failed (validation, execution, or exhausted)")
    total_correction_attempts: int = Field(..., description="Queries that required at least 1 correction attempt")

    # Rates: None represents N/A (zero denominator)
    first_attempt_success_rate: Optional[float] = Field(
        None, description="First-attempt successes / total queries (null if 0 queries)"
    )
    correction_success_rate: Optional[float] = Field(
        None, description="Successes after correction / queries attempting correction (null if 0 attempted)"
    )
    overall_success_rate: Optional[float] = Field(
        None, description="Total successful / total queries (null if 0 queries)"
    )

    # Durations
    avg_generation_duration_ms: Optional[float] = Field(None, description="Average AI generation latency in ms")
    avg_execution_duration_ms: Optional[float] = Field(None, description="Average database execution latency in ms")
    avg_total_duration_ms: Optional[float] = Field(None, description="Average end-to-end latency in ms")

    # Qualitative insights
    most_used_database: Optional[str] = Field(None, description="Database ID with the highest query volume")
    most_common_error: Optional[str] = Field(None, description="Most frequent error category")


class TimeseriesPoint(BaseModel):
    """Daily query volume and status breakdown."""

    date: str = Field(..., description="Date formatted as YYYY-MM-DD")
    total: int = Field(0, description="Total queries on this day")
    first_attempt_successes: int = Field(0, description="Successful without correction")
    corrected_successes: int = Field(0, description="Successful after correction")
    failures: int = Field(0, description="Failed queries on this day")


class AnalyticsTimeseriesResponse(BaseModel):
    """Historical timeseries of query volume and outcomes."""

    points: List[TimeseriesPoint]
    range_days: int = Field(..., description="Days included in the timeseries")


class ErrorCategoryStat(BaseModel):
    """Taxonomy category breakdown of query errors."""

    category: str = Field(..., description="Error category code")
    count: int = Field(..., description="Occurrences of this error")
    percentage: float = Field(..., description="Percentage of total recorded errors")


class AnalyticsErrorsResponse(BaseModel):
    """Categorized distribution of validation and execution failures."""

    categories: List[ErrorCategoryStat]
    total_errors: int = Field(..., description="Total failed queries analyzed")
