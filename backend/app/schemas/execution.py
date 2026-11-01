"""Pydantic schemas for SQL execution, semantic analysis, and iterative self-correction."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.ai import ModelMetadata, SQLValidationResult

QueryExecutionStatus = Literal[
    "success_first_attempt",
    "success_after_correction",
    "failed_validation",
    "failed_execution",
    "correction_exhausted",
    "unsafe_rejected",
    "model_unavailable",
    "timeout",
]


class ExecuteSQLRequest(BaseModel):
    """Request payload for standalone read-only SQL query execution."""

    database_id: str = Field(..., description="Registered database ID to execute against")
    sql: str = Field(..., min_length=1, max_length=10000, description="Read-only SQLite query")
    max_rows: Optional[int] = Field(100, ge=1, le=1000, description="Maximum returned rows before truncation")
    timeout_seconds: Optional[float] = Field(5.0, ge=0.5, le=30.0, description="Execution timeout limit in seconds")


class SemanticWarningItem(BaseModel):
    """Structured semantic advisory item with evidence and severity."""

    code: str = Field(..., description="Machine-readable warning code, e.g. POSSIBLE_SCALE_MISMATCH")
    severity: Literal["info", "warning", "advisory"] = Field("warning", description="Severity level")
    message: str = Field(..., description="Explanatory message for user clarification")
    evidence: Optional[Dict[str, Any]] = Field(None, description="Objective constraint or observational evidence")


class SemanticAnalysisResult(BaseModel):
    """Result of semantic quality analysis (multiplicative joins, Cartesian products, limits, scale)."""

    is_semantically_sound: bool = Field(True, description="Whether query appears free of obvious semantic anomalies")
    warnings: List[str] = Field(default_factory=list, description="Descriptive warnings for potential semantic issues")
    detected_patterns: List[str] = Field(default_factory=list, description="Classification tags of detected patterns")
    recommendation: Optional[str] = Field(None, description="Actionable recommendation to improve semantic clarity")
    structured_warnings: List[SemanticWarningItem] = Field(default_factory=list, description="Structured warnings with evidence")


class ExecuteSQLResponse(BaseModel):
    """Structured response containing executed query results and runtime metrics."""

    request_id: str = Field(..., description="Unique immutable request UUID")
    database_id: str = Field(..., description="Target database identifier")
    sql: str = Field(..., description="Executed SQL statement")
    status: Literal["success", "error", "timeout", "rejected"] = Field(..., description="Execution outcome")
    columns: List[str] = Field(default_factory=list, description="Ordered column labels returned by query")
    rows: List[List[Any]] = Field(default_factory=list, description="2D array of row records")
    row_count: int = Field(0, description="Number of rows returned in this response")
    total_rows_estimated: Optional[int] = Field(None, description="Total matching rows if known")
    is_truncated: bool = Field(False, description="Whether row limit resulted in truncation")
    duration_ms: float = Field(0.0, description="Exact database execution time in milliseconds")
    error_message: Optional[str] = Field(None, description="Sanitized database error description if failed")
    error_code: Optional[str] = Field(None, description="Standardized error category code")
    validation: Optional[SQLValidationResult] = Field(None, description="Static AST validation outcome")
    semantic_analysis: Optional[SemanticAnalysisResult] = Field(None, description="Semantic quality analysis")


class CorrectionAttempt(BaseModel):
    """Audit record for a single step in the iterative self-correction loop."""

    attempt_number: int = Field(..., description="1-indexed attempt sequence number")
    attempt_type: Literal["initial", "correction"] = Field(..., description="Origin classification")
    sql: str = Field(..., description="SQL candidate generated for this attempt")
    validation_status: str = Field(..., description="Validation outcome (valid, invalid, schema_mismatch, etc.)")
    execution_status: str = Field(..., description="Execution outcome (success, error, not_executed, etc.)")
    error_category: Optional[str] = Field(None, description="Classified error category (e.g. UNKNOWN_COLUMN)")
    error_message: Optional[str] = Field(None, description="Diagnostic error fed back to model or user")
    explanation: Optional[str] = Field(None, description="Model-provided reasoning for this candidate")
    changes_made: List[str] = Field(default_factory=list, description="Specific repair changes made by the model")
    generation_time_ms: float = Field(0.0, description="Model generation time in milliseconds")
    execution_time_ms: float = Field(0.0, description="Execution time in milliseconds (0 if not executed)")
    is_accepted: bool = Field(False, description="Whether this attempt passed both validation and execution")


class AIQueryRequest(BaseModel):
    """Request payload for end-to-end natural-language to database results query."""

    question: str = Field(..., min_length=2, max_length=1000, description="Natural language database question")
    database_id: Optional[str] = Field(None, description="Target database ID; defaults to current active database")
    auto_correct: bool = Field(True, description="Whether to trigger execution-guided self-correction on failure")
    max_corrections: Optional[int] = Field(2, ge=0, le=4, description="Maximum iterative repair attempts (default 2)")
    temperature: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="Sampling temperature (0.0 for greedy)")


class AIQueryResponse(BaseModel):
    """Unified response containing final executed query results and transparent correction trace."""

    request_id: str = Field(..., description="Unique immutable request UUID")
    question: str = Field(..., description="Original user prompt")
    database_id: str = Field(..., description="Database ID the query ran against")
    database_name: str = Field(..., description="Human-readable database display name")
    model: ModelMetadata = Field(..., description="Generative AI model metadata")
    final_status: QueryExecutionStatus = Field(..., description="Final end-to-end outcome")
    initial_sql: str = Field(..., description="First SQL candidate produced by the model")
    final_sql: str = Field(..., description="Final SQL candidate accepted or evaluated")
    validation: SQLValidationResult = Field(..., description="Final AST validation result")
    execution: Optional[ExecuteSQLResponse] = Field(None, description="Execution output if query executed")
    semantic_analysis: Optional[SemanticAnalysisResult] = Field(None, description="Semantic quality warnings")
    correction_trace: List[CorrectionAttempt] = Field(default_factory=list, description="Attempt-by-attempt history")
    total_correction_attempts: int = Field(0, description="Count of repair iterations triggered")
    total_duration_ms: float = Field(..., description="Cumulative duration of generation, validation, and execution")
    summary: str = Field(..., description="Executive plain-English summary of the result state")
