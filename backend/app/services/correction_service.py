"""Execution-Guided SQL Self-Correction Orchestrator.

Implements the central USP of SchemaSense AI:
Generate SQL -> Validate (AST) -> Execute Safely -> Diagnose Errors ->
Regenerate Corrected SQL -> Revalidate -> Re-execute -> Display Results.

Features:
- Accurate error taxonomy classification (UNKNOWN_COLUMN, UNKNOWN_TABLE, INVALID_SYNTAX, etc.)
- Transparent step-by-step correction history (CorrectionAttempt)
- Bounded retries (default max 2 corrections, 3 attempts total)
- Infinite loop prevention (rejects identical normalized SQL candidates)
- Immediate safety terminal stops on malicious/destructive queries
- Comprehensive timing and telemetry
"""

from datetime import datetime, timezone
import json
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.exceptions import ModelUnavailableException
from app.core.logging import get_logger
from app.schemas.ai import ModelMetadata, SQLValidationResult
from app.schemas.execution import (
    AIQueryRequest,
    AIQueryResponse,
    CorrectionAttempt,
    ExecuteSQLResponse,
    QueryExecutionStatus,
    SemanticAnalysisResult,
)
from app.schemas.history import QueryHistoryRecord
from app.services.ai_provider import AbstractAIProvider, get_ai_provider
from app.services.database_manager import DatabaseManager, get_database_manager
from app.services.execution_service import ExecutionService, get_execution_service
from app.services.history_service import HistoryService, get_history_service
from app.services.interfaces import SchemaMetadata
from app.services.sqlite_inspector import (
    generate_deterministic_schema_context,
    introspect_sqlite_database,
)
from app.services.sql_validator import SQLValidator, get_sql_validator

logger = get_logger("correction_service")


def normalize_sql(sql: str) -> str:
    """Normalize SQL whitespace and casing for loop detection."""
    cleaned = re.sub(r"\s+", " ", sql.strip())
    return cleaned.rstrip(" ;").strip().lower()


def classify_error(
    validation: Optional[SQLValidationResult],
    execution: Optional[ExecuteSQLResponse],
) -> Tuple[str, str]:
    """Classify the root failure into an objective error category and sanitized diagnostic message."""
    if validation and not validation.is_valid:
        if validation.status == "unsafe":
            return "UNSAFE_SQL", "; ".join(validation.issues)
        if validation.status == "schema_mismatch":
            issues_str = "; ".join(validation.issues).lower()
            if "column" in issues_str:
                return "UNKNOWN_COLUMN", "; ".join(validation.issues)
            if "table" in issues_str:
                return "UNKNOWN_TABLE", "; ".join(validation.issues)
            return "SCHEMA_MISMATCH", "; ".join(validation.issues)
        return "INVALID_SYNTAX", "; ".join(validation.issues)

    if execution and execution.status != "success":
        if execution.status == "timeout":
            return "TIMEOUT", execution.error_message or "Execution timed out"
        if execution.status == "rejected":
            return "AUTHORIZER_REJECTED", execution.error_message or "Operation forbidden by security authorizer"
        err_msg = (execution.error_message or "").lower()
        if "no such column" in err_msg:
            return "UNKNOWN_COLUMN", execution.error_message or ""
        if "no such table" in err_msg:
            return "UNKNOWN_TABLE", execution.error_message or ""
        if "ambiguous column" in err_msg:
            return "AMBIGUOUS_COLUMN", execution.error_message or ""
        return "EXECUTION_ERROR", execution.error_message or "Database execution error"

    return "UNKNOWN_ERROR", "Unspecified error occurred"


class CorrectionService:
    """Orchestrates end-to-end natural-language to SQL generation, validation, execution, and repair."""

    def __init__(
        self,
        ai_provider: Optional[AbstractAIProvider] = None,
        db_manager: Optional[DatabaseManager] = None,
        execution_service: Optional[ExecutionService] = None,
        sql_validator: Optional[SQLValidator] = None,
        history_service: Optional[HistoryService] = None,
    ):
        self._ai_provider = ai_provider
        self.db_manager = db_manager or get_database_manager()
        self.execution_service = execution_service or get_execution_service()
        self.sql_validator = sql_validator or get_sql_validator()
        self.history_service = history_service or get_history_service()

    @property
    def ai_provider(self) -> AbstractAIProvider:
        """Dynamically resolve active AI provider."""
        return self._ai_provider or get_ai_provider()


    async def run_query_workflow(
        self,
        request: AIQueryRequest,
        request_id: Optional[str] = None,
    ) -> AIQueryResponse:
        """Run the end-to-end execution-guided query workflow with intelligent self-correction."""
        req_id = request_id or str(uuid.uuid4())
        workflow_start_time = time.perf_counter()

        # 1. Resolve target database
        target_db_id = request.database_id
        if not target_db_id:
            active_db = self.db_manager.get_active_database()
            if not active_db:
                raise ValueError("No active database configured.")
            target_db_id = active_db.id
            db_info = active_db
        else:
            db_info = self.db_manager.get_database(target_db_id)
            if not db_info:
                raise KeyError(f"Database '{target_db_id}' not found.")

        db_path = self.db_manager.get_database_path(target_db_id)

        # 2. Introspect schema context for LLM prompt and validation
        schema_response = introspect_sqlite_database(db_path, db_info)
        schema_context_resp = generate_deterministic_schema_context(schema_response)
        schema_context_str = schema_context_resp.prompt_schema_context

        # Schema metadata adapter for AIProvider
        schema_meta = SchemaMetadata(
            dialect="sqlite",
            tables=[
                {
                    "name": t.name,
                    "columns": [c.model_dump() for c in t.columns],
                }
                for t in schema_response.tables
            ],
            relationships=[r.model_dump() for r in schema_response.relationships],
        )

        # Get AI Model Status
        model_status = self.ai_provider.get_status()
        model_meta = ModelMetadata(
            provider=model_status.provider,
            model_id=model_status.model_id,
            device=model_status.device,
            total_params=model_status.total_params,
            temperature=request.temperature or 0.0,
        )

        # 3. Iterative execution & self-correction loop state
        max_corrections = max(0, min(request.max_corrections if request.max_corrections is not None else 2, 4))
        auto_correct = request.auto_correct
        max_total_attempts = 1 + (max_corrections if auto_correct else 0)

        attempts_trace: List[CorrectionAttempt] = []
        seen_normalized_queries: Set[str] = set()

        current_sql = ""
        initial_sql = ""
        current_explanation: Optional[str] = None
        current_changes: List[str] = []
        final_execution: Optional[ExecuteSQLResponse] = None
        final_validation: Optional[SQLValidationResult] = None
        final_semantic: Optional[SemanticAnalysisResult] = None
        final_status: QueryExecutionStatus = "failed_validation"

        for attempt_idx in range(1, max_total_attempts + 1):
            is_initial = (attempt_idx == 1)
            attempt_type = "initial" if is_initial else "correction"

            # --- GENERATION STEP ---
            gen_start = time.perf_counter()
            try:
                if is_initial:
                    gen_result = await self.ai_provider.generate_sql(
                        question=request.question,
                        schema=schema_meta,
                        dialect="sqlite",
                        context={
                            "schema_context": schema_context_str,
                            "temperature": request.temperature or 0.0,
                        },
                    )
                    current_sql = gen_result.sql
                    initial_sql = gen_result.sql
                    current_explanation = gen_result.explanation
                    current_changes = []
                else:
                    # Correction step: pass failure diagnostics from previous attempt
                    last_attempt = attempts_trace[-1]
                    corr_result = await self.ai_provider.generate_correction(
                        question=request.question,
                        failed_sql=last_attempt.sql,
                        error_category=last_attempt.error_category or "UNKNOWN_ERROR",
                        error_message=last_attempt.error_message or "Validation or execution failed",
                        schema=schema_meta,
                        dialect="sqlite",
                        context={
                            "schema_context": schema_context_str,
                            "temperature": request.temperature or 0.0,
                        },
                    )
                    current_sql = corr_result.sql
                    current_explanation = corr_result.explanation
                    current_changes = corr_result.changes_made

            except ModelUnavailableException as mue:
                final_status = "model_unavailable"
                break
            except Exception as e:
                logger.error(f"Generation error on attempt {attempt_idx}: {e}")
                final_status = "model_unavailable"
                break

            gen_duration_ms = round((time.perf_counter() - gen_start) * 1000, 2)

            # Loop detection guard: Check if model repeated identical normalized SQL
            norm_sql = normalize_sql(current_sql)
            if not is_initial and norm_sql in seen_normalized_queries:
                attempts_trace.append(
                    CorrectionAttempt(
                        attempt_number=attempt_idx,
                        attempt_type="correction",
                        sql=current_sql,
                        validation_status="repeated_candidate",
                        execution_status="not_executed",
                        error_category="REPEATED_CANDIDATE",
                        error_message="Model generated identical SQL candidate to a previous attempt. Terminating repair loop.",
                        explanation=current_explanation,
                        changes_made=current_changes,
                        generation_time_ms=gen_duration_ms,
                        execution_time_ms=0.0,
                        is_accepted=False,
                    )
                )
                final_status = "correction_exhausted"
                break

            seen_normalized_queries.add(norm_sql)

            # --- VALIDATION STEP ---
            validation = self.sql_validator.validate(current_sql, schema=schema_response)
            final_validation = validation

            # Terminal Safety Rejection: Unsafe DML/DDL or multi-statements
            if validation.status == "unsafe":
                attempts_trace.append(
                    CorrectionAttempt(
                        attempt_number=attempt_idx,
                        attempt_type=attempt_type,
                        sql=current_sql,
                        validation_status="unsafe",
                        execution_status="not_executed",
                        error_category="UNSAFE_SQL",
                        error_message="; ".join(validation.issues),
                        explanation=current_explanation,
                        changes_made=current_changes,
                        generation_time_ms=gen_duration_ms,
                        execution_time_ms=0.0,
                        is_accepted=False,
                    )
                )
                final_status = "unsafe_rejected"
                break

            # If validation failed with syntax or schema mismatch
            if not validation.is_valid:
                category, diag_msg = classify_error(validation, None)
                attempts_trace.append(
                    CorrectionAttempt(
                        attempt_number=attempt_idx,
                        attempt_type=attempt_type,
                        sql=current_sql,
                        validation_status=validation.status,
                        execution_status="not_executed",
                        error_category=category,
                        error_message=diag_msg,
                        explanation=current_explanation,
                        changes_made=current_changes,
                        generation_time_ms=gen_duration_ms,
                        execution_time_ms=0.0,
                        is_accepted=False,
                    )
                )

                if not auto_correct or attempt_idx >= max_total_attempts:
                    final_status = "correction_exhausted" if attempt_idx > 1 else "failed_validation"
                    break
                continue

            # --- EXECUTION STEP ---
            exec_response = self.execution_service.execute_query(
                database_id=target_db_id,
                sql=current_sql,
                max_rows=100,
                timeout_seconds=5.0,
                natural_question=request.question,
                request_id=req_id,
            )
            final_execution = exec_response
            final_semantic = exec_response.semantic_analysis

            # Successful Execution
            if exec_response.status == "success":
                attempts_trace.append(
                    CorrectionAttempt(
                        attempt_number=attempt_idx,
                        attempt_type=attempt_type,
                        sql=current_sql,
                        validation_status="valid",
                        execution_status="success",
                        error_category=None,
                        error_message=None,
                        explanation=current_explanation,
                        changes_made=current_changes,
                        generation_time_ms=gen_duration_ms,
                        execution_time_ms=exec_response.duration_ms,
                        is_accepted=True,
                    )
                )
                final_status = "success_first_attempt" if is_initial else "success_after_correction"
                break

            # Execution Failed (Database error, authorizer denied, or timeout)
            category, diag_msg = classify_error(validation, exec_response)
            attempts_trace.append(
                CorrectionAttempt(
                    attempt_number=attempt_idx,
                    attempt_type=attempt_type,
                    sql=current_sql,
                    validation_status="valid",
                    execution_status=exec_response.status,
                    error_category=category,
                    error_message=diag_msg,
                    explanation=current_explanation,
                    changes_made=current_changes,
                    generation_time_ms=gen_duration_ms,
                    execution_time_ms=exec_response.duration_ms,
                    is_accepted=False,
                )
            )

            if exec_response.status == "timeout":
                final_status = "timeout"
                break

            if not auto_correct or attempt_idx >= max_total_attempts:
                final_status = "correction_exhausted" if attempt_idx > 1 else "failed_execution"
                break

        total_workflow_ms = round((time.perf_counter() - workflow_start_time) * 1000, 2)
        corrections_triggered = max(0, len(attempts_trace) - 1)

        # Build concise executive summary
        summary = self._build_executive_summary(final_status, corrections_triggered, final_execution)

        # Fallback validation object if loop broke early
        if final_validation is None:
            final_validation = self.sql_validator.validate(current_sql or "SELECT 1;", schema=schema_response)

        # Persist execution event into durable history (safe fail-open)
        try:
            total_gen_ms = sum(a.generation_time_ms for a in attempts_trace)
            err_cat = None
            if attempts_trace and not final_status.startswith("success"):
                err_cat = attempts_trace[-1].error_category

            trace_summary_list = [
                {
                    "attempt": a.attempt_number,
                    "type": a.attempt_type,
                    "validation": a.validation_status,
                    "execution": a.execution_status,
                    "category": a.error_category,
                }
                for a in attempts_trace
            ]
            trace_summary_json = json.dumps(trace_summary_list) if trace_summary_list else None

            warnings_summary_json = None
            if final_semantic and final_semantic.structured_warnings:
                warnings_summary_json = json.dumps([w.model_dump() for w in final_semantic.structured_warnings])

            history_rec = QueryHistoryRecord(
                request_id=req_id,
                created_at=datetime.now(timezone.utc).isoformat(),
                database_id=target_db_id,
                database_name=db_info.name,
                question=request.question,
                generation_mode=model_status.provider,
                model_id=model_status.model_id,
                initial_sql=initial_sql or current_sql,
                final_sql=current_sql,
                final_status=final_status,
                validation_status=final_validation.status if final_validation else "unknown",
                execution_status=final_execution.status if final_execution else "not_executed",
                row_count=final_execution.row_count if final_execution else None,
                correction_count=corrections_triggered,
                generation_duration_ms=round(total_gen_ms, 2),
                execution_duration_ms=round(final_execution.duration_ms, 2) if final_execution else 0.0,
                total_duration_ms=total_workflow_ms,
                semantic_warning_count=len(final_semantic.warnings) if final_semantic else 0,
                error_category=err_cat,
                correction_trace_summary=trace_summary_json,
                semantic_warnings_summary=warnings_summary_json,
            )
            self.history_service.record_query(history_rec)
        except Exception as e:
            logger.warning(f"Failed to record history for query {req_id}: {e}")

        return AIQueryResponse(
            request_id=req_id,
            question=request.question,
            database_id=target_db_id,
            database_name=db_info.name,
            model=model_meta,
            final_status=final_status,
            initial_sql=initial_sql or current_sql,
            final_sql=current_sql,
            validation=final_validation,
            execution=final_execution,
            semantic_analysis=final_semantic,
            correction_trace=attempts_trace,
            total_correction_attempts=corrections_triggered,
            total_duration_ms=total_workflow_ms,
            summary=summary,
        )

    def _build_executive_summary(
        self,
        status: QueryExecutionStatus,
        corrections: int,
        execution: Optional[ExecuteSQLResponse],
    ) -> str:
        """Formulate a professional executive summary of the query outcome."""
        if status == "success_first_attempt":
            row_count = execution.row_count if execution else 0
            return f"Query executed successfully on the first attempt returning {row_count} records."
        if status == "success_after_correction":
            row_count = execution.row_count if execution else 0
            return (
                f"Query was successfully repaired and executed after {corrections} "
                f"self-correction {'attempt' if corrections == 1 else 'attempts'}, "
                f"returning {row_count} records."
            )
        if status == "unsafe_rejected":
            return "Query was rejected prior to execution due to security policy violations."
        if status == "correction_exhausted":
            return f"Self-correction loop exhausted all {corrections} allowed repair attempts without reaching a valid query."
        if status == "timeout":
            return "Query execution exceeded server timeout limits and was safely interrupted."
        if status == "model_unavailable":
            return "Generative AI model is currently offline or uninitialized."
        if status == "failed_validation":
            return "Generated query failed AST static validation checks."
        if status == "failed_execution":
            return "Query passed static validation but encountered database execution errors."
        return "Query processing concluded with status: " + status


# Singleton instance
_correction_service_instance: Optional[CorrectionService] = None


def get_correction_service() -> CorrectionService:
    """Return singleton CorrectionService instance."""
    global _correction_service_instance
    if _correction_service_instance is None:
        _correction_service_instance = CorrectionService()
    return _correction_service_instance
