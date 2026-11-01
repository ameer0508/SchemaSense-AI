"""Capabilities discovery API router."""

from fastapi import APIRouter
from app.core.config import settings
from app.schemas.capabilities import CapabilitiesResponse, CapabilityFlags

router = APIRouter(tags=["Capabilities"])


@router.get(
    "/capabilities",
    response_model=CapabilitiesResponse,
    summary="System Capabilities Matrix",
    description="Returns accurate capability flags, supported SQL dialects, and active provider info.",
)
async def get_capabilities() -> CapabilitiesResponse:
    """Return actual capability status of SchemaSense AI."""
    active_provider = (
        None if settings.ACTIVE_AI_PROVIDER in ("none", "", None) else settings.ACTIVE_AI_PROVIDER
    )

    return CapabilitiesResponse(
        product=settings.PROJECT_NAME,
        tagline=settings.TAGLINE,
        version=settings.VERSION,
        phase=settings.PHASE,
        phase_description=(
            "Phase 8: Verified Academic GenAI Engine. "
            "Real Qwen2.5-Coder transformer inference, dynamic schema grounding, multi-tier SQLGlot AST validation, "
            "read-only authorizer sandbox, execution-guided self-correction, and conservative semantic integrity auditing."
        ),
        capabilities=CapabilityFlags(
            health_check=True,
            capabilities_discovery=True,
            schema_introspection=True,
            database_registration=True,
            sqlite_upload=True,
            relationship_discovery=True,
            table_preview=True,
            schema_context_generation=True,
            natural_language_sql=True,
            sql_execution=True,
            sql_self_correction=True,
            query_history_archiving=True,
            analytics_telemetry=True,
        ),
        supported_dialects=["postgresql", "sqlite", "mysql", "snowflake"],
        supported_ai_providers=["gemini", "openai", "anthropic", "local"],
        active_ai_provider=active_provider,
    )
