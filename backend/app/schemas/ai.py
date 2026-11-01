"""Pydantic schemas for AI text-to-SQL generation and validation."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


ValidationStatus = Literal[
    "valid",
    "invalid",
    "unsafe",
    "schema_mismatch",
    "unsupported",
    "unverified",
]

ModelLoadStatus = Literal[
    "not_loaded",
    "loading",
    "ready",
    "unavailable",
    "error",
]


class ModelMetadata(BaseModel):
    """Metadata regarding the generative language model."""

    provider: str = Field("local", description="Provider identifier (e.g. 'local', 'mock')")
    model_id: str = Field(..., description="Hugging Face model identifier or mock name")
    device: Optional[str] = Field("cpu", description="Hardware execution device ('cpu' or 'cuda')")


class SQLValidationResult(BaseModel):
    """Result of static AST parsing and schema validation using SQLGlot."""

    status: ValidationStatus = Field(..., description="Categorized validation status")
    is_valid: bool = Field(..., description="Whether SQL passed syntax and safety verification")
    syntax_valid: bool = Field(..., description="Whether SQL successfully parsed as SQLite dialect")
    schema_valid: bool = Field(..., description="Whether referenced tables and columns exist in schema")
    ast_type: Optional[str] = Field(None, description="Primary statement AST type (e.g. 'Select')")
    tables_referenced: List[str] = Field(default_factory=list, description="Tables referenced in query")
    columns_referenced: List[str] = Field(default_factory=list, description="Columns referenced in query")
    issues: List[str] = Field(default_factory=list, description="Explanations of syntax, safety, or schema issues")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings or resolution notes")


class ExecutionStatus(BaseModel):
    """Execution status indicator (strictly 'not_executed' in Phase 4)."""

    status: str = Field("not_executed", description="Execution status; scheduled for Phase 5")
    message: str = Field(
        "Query execution is scheduled for Phase 5 (Execution Sandbox & Agentic Self-Correction).",
        description="Explanation of execution state",
    )


class GenerateSQLRequest(BaseModel):
    """Request payload for natural-language to SQL translation."""

    question: str = Field(..., min_length=2, max_length=1000, description="Natural language question")
    database_id: Optional[str] = Field(
        None, description="Database ID to query. If omitted, uses current active database."
    )
    temperature: Optional[float] = Field(0.0, ge=0.0, le=1.0, description="Sampling temperature")


class GenerateSQLResponse(BaseModel):
    """Typed response containing generated SQL, explanation, and validation results."""

    request_id: str = Field(..., description="Unique immutable request UUID")
    database_id: str = Field(..., description="Database ID the query was grounded against")
    database_name: str = Field(..., description="Display name of the target database")
    model: ModelMetadata = Field(..., description="Generative model metadata")
    question: str = Field(..., description="Submitted natural language question")
    sql: str = Field(..., description="Generated SQLite SQL query")
    explanation: Optional[str] = Field(None, description="Model-generated explanation of query logic")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made by the model")
    validation: SQLValidationResult = Field(..., description="SQLGlot static AST validation outcome")
    execution: ExecutionStatus = Field(default_factory=ExecutionStatus, description="Execution status")
    generation_time_ms: float = Field(..., description="End-to-end inference and validation duration in ms")
    prompt_tokens_estimated: Optional[int] = Field(None, description="Estimated prompt token count")


class ModelStatusResponse(BaseModel):
    """Accurate status of the generative AI engine."""

    provider: str = Field("local", description="Configured provider ('local' or 'mock')")
    model_id: str = Field(..., description="Configured Hugging Face model identifier")
    status: ModelLoadStatus = Field(..., description="Current load status of the model")
    device: str = Field("cpu", description="Execution device ('cpu' or 'cuda')")
    is_available: bool = Field(False, description="Whether generation is currently available")
    is_loading: bool = Field(False, description="Whether model is currently downloading or initializing")
    total_params: Optional[str] = Field(None, description="Parameter scale (e.g. '1.54B')")
    max_new_tokens: int = Field(384, description="Configured token generation limit")
    temperature: float = Field(0.0, description="Configured generation temperature")
    error_message: Optional[str] = Field(None, description="Failure details if status is 'error'")


class InitializeModelResponse(BaseModel):
    """Response returned upon triggering model initialization."""

    status: ModelLoadStatus = Field(..., description="Status after initialization attempt")
    model_id: str = Field(..., description="Target model ID")
    message: str = Field(..., description="Status message")
