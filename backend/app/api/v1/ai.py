"""API endpoints for AI natural-language to SQL generation and model lifecycle."""

import asyncio
import time
import uuid
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.core.exceptions import (
    DatabaseNotFoundException,
    NoActiveDatabaseException,
)
from app.core.logging import get_logger
from app.schemas.ai import (
    GenerateSQLRequest,
    GenerateSQLResponse,
    InitializeModelResponse,
    ModelMetadata,
    ModelStatusResponse,
)
from datetime import datetime, timezone
from app.schemas.execution import AIQueryRequest, AIQueryResponse
from app.schemas.history import QueryHistoryRecord
from app.services.ai_provider import get_ai_provider
from app.services.correction_service import get_correction_service
from app.services.database_manager import DatabaseManager, get_database_manager
from app.services.history_service import get_history_service
from app.services.interfaces import SchemaMetadata
from app.services.sql_validator import get_sql_validator
from app.services.sqlite_inspector import (
    generate_deterministic_schema_context,
    introspect_sqlite_database,
)

logger = get_logger("ai_router")
router = APIRouter(prefix="/ai", tags=["AI Engine & Text-to-SQL"])


@router.get(
    "/status",
    response_model=ModelStatusResponse,
    summary="Get AI Model Status",
    description="Returns accurate operational and loading status of the generative model.",
)
async def get_model_status() -> ModelStatusResponse:
    """Retrieve model readiness and configuration status without triggering loads."""
    provider = get_ai_provider()
    return provider.get_status()


@router.post(
    "/initialize",
    response_model=InitializeModelResponse,
    summary="Initialize AI Model",
    description="Trigger model initialization and weight loading in the background.",
)
async def initialize_model(
    background_tasks: BackgroundTasks,
) -> InitializeModelResponse:
    """Trigger background model loading if not already ready."""
    provider = get_ai_provider()
    current_status = provider.get_status()

    if current_status.status == "ready":
        return InitializeModelResponse(
            status="ready",
            model_id=provider.model_id,
            message=f"Model '{provider.model_id}' is already loaded and ready.",
        )

    if current_status.status == "loading":
        return InitializeModelResponse(
            status="loading",
            model_id=provider.model_id,
            message=f"Model '{provider.model_id}' is currently loading.",
        )

    # Schedule initialization in background
    background_tasks.add_task(provider.initialize)

    return InitializeModelResponse(
        status="loading",
        model_id=provider.model_id,
        message=f"Model loading initiated for '{provider.model_id}'. Check /api/ai/status for progress.",
    )


@router.post(
    "/generate-sql",
    response_model=GenerateSQLResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate SQL from Natural Language",
    description="Grounds the question in the active SQLite database schema, executes transformer inference, and validates with SQLGlot.",
)
async def generate_sql(
    request: GenerateSQLRequest,
    db_manager: DatabaseManager = Depends(get_database_manager),
) -> GenerateSQLResponse:
    """End-to-end natural-language to SQL translation pipeline."""
    # 1. Resolve Target Database
    if request.database_id:
        db_info = db_manager.get_database(request.database_id)
        if not db_info:
            raise DatabaseNotFoundException(database_id=request.database_id)
        db_path = db_manager.get_database_path(request.database_id)
    else:
        db_info = db_manager.get_active_database()
        if not db_info:
            raise NoActiveDatabaseException()
        db_path = db_manager.get_database_path(db_info.id)

    # 2. Introspect Schema and Generate Deterministic Context
    schema_response = introspect_sqlite_database(db_path, db_info)
    schema_context_resp = generate_deterministic_schema_context(schema_response)

    schema_metadata = SchemaMetadata(
        dialect="sqlite",
        tables=[t.model_dump() for t in schema_response.tables],
        relationships=[r.model_dump() for r in schema_response.relationships],
    )

    # 3. Model Generation
    provider = get_ai_provider()
    start_time = time.perf_counter()

    gen_result = await provider.generate_sql(
        question=request.question,
        schema=schema_metadata,
        dialect="sqlite",
        context={
            "schema_context": schema_context_resp.prompt_schema_context,
            "temperature": request.temperature if request.temperature is not None else 0.0,
        },
    )

    generation_time_ms = (time.perf_counter() - start_time) * 1000.0

    # 4. Static SQLGlot AST & Schema Validation
    validator = get_sql_validator()
    validation_outcome = validator.validate(
        sql=gen_result.sql,
        schema=schema_response,
    )

    device = getattr(provider, "device", "cpu")
    model_meta = ModelMetadata(
        provider=provider.provider_name,
        model_id=provider.model_id,
        device=device,
    )

    req_id = str(uuid.uuid4())

    # Record generation-only query to durable history
    try:
        hist_svc = get_history_service()
        gen_rec = QueryHistoryRecord(
            request_id=req_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            database_id=db_info.id,
            database_name=db_info.name,
            question=request.question,
            generation_mode=provider.provider_name,
            model_id=provider.model_id,
            initial_sql=gen_result.sql,
            final_sql=gen_result.sql,
            final_status="generated_only" if validation_outcome.is_valid else "failed_validation",
            validation_status=validation_outcome.status,
            execution_status="not_executed",
            row_count=None,
            correction_count=0,
            generation_duration_ms=round(generation_time_ms, 2),
            execution_duration_ms=0.0,
            total_duration_ms=round(generation_time_ms, 2),
            semantic_warning_count=0,
            error_category=None if validation_outcome.is_valid else "VALIDATION_ERROR",
            correction_trace_summary=None,
            semantic_warnings_summary=None,
        )
        hist_svc.record_query(gen_rec)
    except Exception as e:
        logger.warning(f"Failed to record generation-only history: {e}")

    return GenerateSQLResponse(
        request_id=req_id,
        database_id=db_info.id,
        database_name=db_info.name,
        model=model_meta,
        question=request.question,
        sql=gen_result.sql,
        explanation=gen_result.explanation,
        assumptions=gen_result.assumptions or [],
        validation=validation_outcome,
        generation_time_ms=round(generation_time_ms, 2),
        prompt_tokens_estimated=schema_context_resp.token_estimate,
    )


@router.post(
    "/query",
    response_model=AIQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="End-to-End AI Query with Self-Correction",
    description="Translates natural language to SQL, validates AST, executes safely, diagnoses errors, and performs execution-guided self-correction.",
)
async def query_database(
    request: AIQueryRequest,
) -> AIQueryResponse:
    """Execute end-to-end question to SQL and database results workflow."""
    correction_service = get_correction_service()
    try:
        return await correction_service.run_query_workflow(request)
    except KeyError as ke:
        raise DatabaseNotFoundException(database_id=str(request.database_id))
    except ValueError as ve:
        raise NoActiveDatabaseException()
