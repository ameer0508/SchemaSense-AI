"""Real Qwen Correction from a Controlled Invalid Candidate.

Phase 6 Reproducible Real-Model Evaluation (Section 6 & Finding D):
1. Loads the actual Qwen2.5-Coder-1.5B-Instruct transformer model on local CPU.
2. Introspects the genuine Campus Intelligence SQLite database schema.
3. Supplies the controlled invalid SQL candidate:
   SELECT student_name, gpa FROM students ORDER BY gpa DESC LIMIT 5;
   with verified diagnostic: Column 'student_name' does not exist in table 'students'.
4. Invokes genuine local transformer inference to regenerate corrected SQL.
5. Performs SQLGlot AST validation on the corrected candidate.
6. Executes the corrected query in the secure read-only SQLite sandbox.
7. Saves the unedited, transparent result to backend/evaluation/results/real_qwen_correction_result.json.
"""

import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import sys
import time
from typing import Any, Dict

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.ai_provider import LocalTransformersProvider
from app.services.database_manager import get_database_manager
from app.services.execution_service import get_execution_service
from app.services.interfaces import SchemaMetadata
from app.services.sqlite_inspector import (
    generate_deterministic_schema_context,
    introspect_sqlite_database,
)
from app.services.sql_validator import get_sql_validator


async def run_real_qwen_correction_evaluation() -> Dict[str, Any]:
    """Execute real-model correction evaluation from a controlled invalid candidate."""
    print("=" * 70)
    print(" SchemaSense AI — Real Qwen Correction Evaluation")
    print(" Candidate: Controlled Invalid SQL (student_name -> first_name, last_name)")
    print(" Model: Qwen/Qwen2.5-Coder-1.5B-Instruct (Genuine Local Transformers)")
    print("=" * 70)

    # 1. Resolve Target Database
    db_manager = get_database_manager()
    demo_db_id = "campus_intelligence"
    db_info = db_manager.get_database(demo_db_id)
    if not db_info:
        raise RuntimeError("Campus Intelligence database is not initialized.")
    db_path = db_manager.get_database_path(demo_db_id)

    # 2. Introspect Real Schema
    print("\n[Step 1/6] Introspecting Campus Intelligence schema...")
    schema_response = introspect_sqlite_database(db_path, db_info)
    schema_context_resp = generate_deterministic_schema_context(schema_response)
    schema_metadata = SchemaMetadata(
        dialect="sqlite",
        tables=[t.model_dump() for t in schema_response.tables],
        relationships=[r.model_dump() for r in schema_response.relationships],
    )
    print(f"       Schema introspected: {len(schema_response.tables)} tables, {schema_response.total_columns} columns.")

    # 3. Define Controlled Invalid Candidate and Diagnostic
    invalid_candidate_sql = "SELECT student_name, gpa FROM students ORDER BY gpa DESC LIMIT 5;"
    natural_question = "Show the top 5 students with the highest GPA."
    error_category = "UNKNOWN_COLUMN"
    diagnostic_message = (
        "Column 'student_name' does not exist in table 'students'. "
        "Available columns in 'students': [student_id, first_name, last_name, email, department_id, enrollment_year, gpa, status]."
    )

    print(f"\n[Step 2/6] Controlled Invalid Candidate:")
    print(f"       Question:   {natural_question}")
    print(f"       Invalid SQL: {invalid_candidate_sql}")
    print(f"       Diagnostic:  {diagnostic_message}")

    # 4. Initialize Genuine Local Transformer
    print("\n[Step 3/6] Initializing local Qwen2.5-Coder-1.5B-Instruct model...")
    provider = LocalTransformersProvider()
    await provider.initialize()
    status_info = provider.get_status()
    print(f"       Model Status: {status_info.status} ({status_info.device})")

    # 5. Invoke Real Transformer for Self-Correction
    print("\n[Step 4/6] Running genuine transformer inference for correction...")
    start_time = time.perf_counter()
    gen_result = await provider.generate_correction(
        question=natural_question,
        failed_sql=invalid_candidate_sql,
        error_category=error_category,
        error_message=diagnostic_message,
        schema=schema_metadata,
        dialect="sqlite",
        context={
            "schema_context": schema_context_resp.prompt_schema_context,
            "temperature": 0.0,
        },
    )
    inference_duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    corrected_sql = gen_result.sql.strip()

    print(f"       Inference completed in: {inference_duration_ms:.1f} ms ({inference_duration_ms/1000:.1f}s)")
    print(f"       Corrected SQL Generated:\n       >>> {corrected_sql}")
    if gen_result.explanation:
        print(f"       Model Explanation: {gen_result.explanation}")

    # 6. AST Validation
    print("\n[Step 5/6] Performing SQLGlot AST and Schema Validation...")
    validator = get_sql_validator()
    val_result = validator.validate(corrected_sql, schema=schema_response)
    print(f"       Validation Status: {val_result.status} (Valid: {val_result.is_valid})")
    if val_result.issues:
        print(f"       Validation Issues: {val_result.issues}")

    # 7. Safe Read-Only Execution
    print("\n[Step 6/6] Executing corrected query in read-only sandbox...")
    exec_service = get_execution_service()
    exec_result = exec_service.execute_query(
        database_id=demo_db_id,
        sql=corrected_sql,
        max_rows=10,
    )

    is_success = (exec_result.status == "success")
    print(f"       Execution Status: {exec_result.status} (Rows: {exec_result.row_count}, Duration: {exec_result.duration_ms} ms)")
    if is_success and exec_result.rows:
        print(f"       Sample Rows Returned (Top {len(exec_result.rows)}):")
        for r in exec_result.rows:
            print(f"         {r}")
    elif exec_result.error_message:
        print(f"       Execution Error: {exec_result.error_message}")

    # 8. Semantic Quality Analysis on Corrected Query
    from app.services.semantic_analyzer import get_semantic_analyzer
    sem_analyzer = get_semantic_analyzer()
    sem_result = sem_analyzer.analyze(
        sql=corrected_sql,
        schema=schema_response,
        natural_question=natural_question,
        row_count=exec_result.row_count,
    )
    if not sem_result.is_semantically_sound:
        print(f"       [Semantic Quality Advisory]: {sem_result.warnings}")

    # 9. Record Result
    eval_record = {
        "evaluation_name": "Real Qwen Correction from a Controlled Invalid Candidate",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_id": provider.model_id,
        "device": provider.device,
        "environment": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
        },
        "test_case": {
            "question": natural_question,
            "database_id": demo_db_id,
            "controlled_invalid_sql": invalid_candidate_sql,
            "error_category": error_category,
            "diagnostic_message": diagnostic_message,
        },
        "model_output": {
            "corrected_sql": corrected_sql,
            "explanation": gen_result.explanation,
            "changes_made": getattr(gen_result, "changes_made", []),
            "inference_duration_ms": inference_duration_ms,
        },
        "validation_outcome": {
            "is_valid": val_result.is_valid,
            "status": val_result.status,
            "issues": val_result.issues,
        },
        "execution_outcome": {
            "status": exec_result.status,
            "row_count": exec_result.row_count,
            "columns": exec_result.columns,
            "execution_duration_ms": exec_result.duration_ms,
            "sample_rows": exec_result.rows[:5] if exec_result.rows else [],
            "error_message": exec_result.error_message,
        },
        "semantic_analysis": {
            "is_semantically_sound": sem_result.is_semantically_sound,
            "warnings": sem_result.warnings,
            "detected_patterns": sem_result.detected_patterns,
            "structured_warnings": [w.model_dump() for w in sem_result.structured_warnings],
        },
        "correction_verdict": {
            "success": is_success and val_result.is_valid,
            "repaired_unknown_column": "student_name" not in corrected_sql.lower(),
            "projected_valid_columns": any(col in corrected_sql.lower() for col in ["first_name", "last_name", "*"]),
        },
    }

    # Save to backend/evaluation/results/real_qwen_correction_result.json
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_file = results_dir / "real_qwen_correction_result.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(eval_record, f, indent=2)

    print("\n" + "=" * 70)
    verdict_text = "SUCCESS" if eval_record["correction_verdict"]["success"] else "FAILED"
    print(f" Evaluation Verdict: {verdict_text}")
    print(f" Repaired 'student_name' anomaly: {eval_record['correction_verdict']['repaired_unknown_column']}")
    print(f" Saved transparent results to: {out_file}")
    print("=" * 70 + "\n")

    return eval_record


if __name__ == "__main__":
    asyncio.run(run_real_qwen_correction_evaluation())
