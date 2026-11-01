"""Pydantic schemas for the capability discovery endpoint."""

from typing import List, Optional
from pydantic import BaseModel, Field


class CapabilityFlags(BaseModel):
    """Accurate feature capability flags for the current phase."""

    health_check: bool = Field(True, description="System health status reporting")
    capabilities_discovery: bool = True
    schema_introspection: bool = Field(True, description="Real SQLite database schema introspection")
    database_registration: bool = Field(True, description="Local SQLite database registration & management")
    sqlite_upload: bool = Field(True, description="Secure SQLite database file upload & validation")
    relationship_discovery: bool = Field(True, description="Foreign-key based relational constraint discovery")
    table_preview: bool = Field(True, description="Bounded read-only tabular records inspection")
    schema_context_generation: bool = Field(True, description="Deterministic LLM prompt schema context serialization")
    natural_language_sql: bool = Field(True, description="Real transformer-based natural-language-to-SQL generation")
    sql_execution: bool = Field(True, description="Safe read-only SQLite execution with authorizer sandbox and timeouts")
    sql_self_correction: bool = Field(True, description="Execution-guided iterative self-correction loop with diagnostic feedback")
    query_history_archiving: bool = Field(True, description="Query session and history tracking")
    analytics_telemetry: bool = Field(True, description="Execution telemetry and trustworthy analytics aggregation")


class CapabilitiesResponse(BaseModel):
    """Accurate capabilities discovery response."""

    product: str = Field(default="SchemaSense AI", description="Product name")
    tagline: str = Field(default="Natural Language. Precise SQL.", description="Product subtitle")
    version: str = Field(..., description="Application version")
    phase: str = Field(default="Phase 6 - AI Reliability, Persistent History & Analytics", description="Current project milestone")
    phase_description: str = Field(
        default="AI reliability refinements, schema-aware scale understanding, durable query history, and trustworthy execution analytics.",
        description="Summary of enabled functionality in current phase",
    )
    capabilities: CapabilityFlags = Field(..., description="Detailed flags of actual capability status")
    supported_dialects: List[str] = Field(
        default=["postgresql", "sqlite", "mysql", "snowflake"],
        description="Target SQL dialects supported by the architecture",
    )
    supported_ai_providers: List[str] = Field(
        default=["gemini", "openai", "anthropic", "local"],
        description="AI engine backends supported by architecture",
    )
    active_ai_provider: Optional[str] = Field(
        default=None,
        description="Currently active AI provider; null in Phase 1 until integration",
    )
