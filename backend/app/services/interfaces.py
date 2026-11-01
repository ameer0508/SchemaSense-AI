"""Abstract base interfaces for future SchemaSense AI core services.

These interfaces define the architecture contracts for:
- AI Provider Engine (Phase 2)
- Database Schema Introspection (Phase 2)
- Safe SQL Execution Sandbox (Phase 2)
- Agentic SQL Self-Correction Loop (Phase 3)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class SchemaMetadata(BaseModel):
    """Metadata representation of an introspected database schema."""

    dialect: str
    tables: List[Dict[str, Any]]
    relationships: List[Dict[str, Any]]


class SQLGenerationResult(BaseModel):
    """Result of an AI natural-language to SQL translation."""

    sql: str
    explanation: Optional[str] = None
    confidence_score: Optional[float] = None
    tokens_used: Optional[int] = None
    assumptions: List[str] = []


class SQLCorrectionResult(BaseModel):
    """Result of an AI natural-language to SQL correction step."""

    sql: str
    explanation: Optional[str] = None
    changes_made: List[str] = []
    tokens_used: Optional[int] = None


class ExecutionResult(BaseModel):
    """Result of safe query execution."""

    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    duration_ms: float
    is_truncated: bool = False


class CorrectionStep(BaseModel):
    """Step representation in an iterative self-correction loop."""

    iteration: int
    fault_detected: str
    attempted_fix: str
    revised_sql: str
    passed: bool


class BaseAIProvider(ABC):
    """Interface for LLM / AI engine integrations (Gemini, Claude, GPT, Local)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g., 'gemini', 'anthropic')."""
        pass

    @abstractmethod
    async def generate_sql(
        self,
        question: str,
        schema: SchemaMetadata,
        dialect: str = "postgresql",
        context: Optional[Dict[str, Any]] = None,
    ) -> SQLGenerationResult:
        """Translate a natural language prompt into executable SQL."""
        pass

    @abstractmethod
    async def generate_correction(
        self,
        question: str,
        failed_sql: str,
        error_category: str,
        error_message: str,
        schema: SchemaMetadata,
        dialect: str = "sqlite",
        context: Optional[Dict[str, Any]] = None,
    ) -> SQLCorrectionResult:
        """Translate error diagnostic and failing query into a repaired SQL candidate."""
        pass


class BaseSchemaService(ABC):
    """Interface for database connection and schema introspection."""

    @abstractmethod
    async def introspect(
        self, connection_url: str, schema_filter: Optional[str] = None
    ) -> SchemaMetadata:
        """Extract table schemas, column data types, and primary/foreign keys."""
        pass

    @abstractmethod
    async def validate_connection(self, connection_url: str) -> bool:
        """Verify database connectivity."""
        pass


class BaseExecutionService(ABC):
    """Interface for isolated, read-only SQL execution."""

    @abstractmethod
    async def execute_query(
        self,
        connection_url: str,
        sql: str,
        timeout_seconds: int = 30,
        max_rows: int = 100,
    ) -> ExecutionResult:
        """Safely execute a read-only query and return tabular records."""
        pass


class BaseCorrectionService(ABC):
    """Interface for agentic iterative SQL self-correction."""

    @abstractmethod
    async def correct_query(
        self,
        original_sql: str,
        error_message: str,
        schema: SchemaMetadata,
        dialect: str = "postgresql",
        max_attempts: int = 3,
    ) -> List[CorrectionStep]:
        """Iteratively diagnose, refine, and re-validate failing SQL queries."""
        pass
