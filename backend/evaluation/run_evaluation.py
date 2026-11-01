"""Academic Evaluation Benchmark Runner.

Executes reproducible evaluation across benchmark questions covering:
- Simple filtering, Sorting, Aggregation, GROUP BY, HAVING, Single-table,
  Multi-table JOINs, Ranking, Subqueries, Ambiguous questions, Numeric scale mismatches,
  Empty results, Invalid schema assumptions, and Semantic challenges.

Supports both fast deterministic testing (--mode mock) and real local transformer inference (--mode local).
Outputs full JSON report to backend/evaluation/results/eval_results_<timestamp>.json.
"""

import argparse
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import sys
import time
from typing import Any, Dict, List, Optional

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.schemas.execution import AIQueryRequest
from app.services.ai_provider import LocalTransformersProvider, MockAIProvider
from app.services.correction_service import CorrectionService
from app.services.database_manager import get_database_manager
from app.services.execution_service import get_execution_service


async def run_academic_evaluation(
    mode: str = "mock",
    limit: Optional[int] = None,
    dataset_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Run evaluation benchmark across curated questions."""
    eval_dir = Path(__file__).resolve().parent
    ds_file = dataset_path or (eval_dir / "evaluation_dataset.json")

    if not ds_file.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at {ds_file}")

    with open(ds_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    questions: List[Dict[str, Any]] = dataset.get("questions", [])
    if limit and limit > 0:
        questions = questions[:limit]

    print(f"\n==================================================================")
    print(f" SchemaSense AI — Academic Evaluation Runner")
    print(f" Dataset: {dataset.get('name')} (v{dataset.get('dataset_version')})")
    print(f" Mode: {mode.upper()} | Total Questions: {len(questions)}")
    print(f" Target DB: {dataset.get('target_database')}")
    print(f"==================================================================\n")

    # Set up AI Provider and Correction Service
    db_manager = get_database_manager()
    exec_service = get_execution_service()

    if mode == "local":
        print("Loading genuine local Qwen2.5-Coder-1.5B-Instruct model (CPU)...")
        ai_provider = LocalTransformersProvider()
        await ai_provider.initialize()
        status_info = ai_provider.get_status()
        print(f"Model initialization: {status_info.status} ({status_info.device})")
    else:
        ai_provider = MockAIProvider()

    correction_service = CorrectionService(
        ai_provider=ai_provider,
        db_manager=db_manager,
        execution_service=exec_service,
    )

    results: List[Dict[str, Any]] = []
    total_syntax_valid = 0
    total_schema_valid = 0
    total_executed = 0
    total_corrected = 0
    total_semantic_warnings = 0
    scale_mismatches_flagged = 0

    suite_start = time.perf_counter()

    for idx, q_item in enumerate(questions, start=1):
        q_id = q_item["id"]
        q_text = q_item["question"]
        q_cat = q_item["category"]
        ref_sql = q_item.get("reference_sql")

        print(f"[{idx:02d}/{len(questions):02d}] {q_id} ({q_cat}): \"{q_text}\"")

        req = AIQueryRequest(
            question=q_text,
            database_id=dataset.get("target_database", "campus_intelligence"),
            auto_correct=True,
            max_corrections=2,
            temperature=0.0,
        )

        q_start = time.perf_counter()
        try:
            workflow_res = await correction_service.run_query_workflow(req)
            elapsed_ms = round((time.perf_counter() - q_start) * 1000, 2)

            is_syntax_valid = workflow_res.validation.is_valid if workflow_res.validation else False
            is_exec_success = (workflow_res.execution.status == "success") if workflow_res.execution else False
            correction_count = workflow_res.total_correction_attempts
            warning_count = len(workflow_res.semantic_analysis.warnings) if workflow_res.semantic_analysis else 0

            # Check for scale mismatch warning
            has_scale_mismatch = False
            if workflow_res.semantic_analysis and workflow_res.semantic_analysis.structured_warnings:
                has_scale_mismatch = any(
                    w.code == "POSSIBLE_SCALE_MISMATCH" for w in workflow_res.semantic_analysis.structured_warnings
                )

            if is_syntax_valid:
                total_syntax_valid += 1
            if workflow_res.validation and workflow_res.validation.status != "schema_mismatch":
                total_schema_valid += 1
            if is_exec_success:
                total_executed += 1
            if correction_count > 0 and is_exec_success:
                total_corrected += 1
            if warning_count > 0:
                total_semantic_warnings += 1
            if has_scale_mismatch:
                scale_mismatches_flagged += 1

            # Execute reference query to compare ground truth if available
            ref_rows_count = None
            if ref_sql:
                try:
                    ref_res = exec_service.execute_query(
                        database_id=req.database_id,
                        sql=ref_sql,
                    )
                    ref_rows_count = ref_res.row_count
                except Exception:
                    pass

            item_result = {
                "id": q_id,
                "category": q_cat,
                "question": q_text,
                "final_sql": workflow_res.final_sql,
                "final_status": workflow_res.final_status,
                "syntax_valid": is_syntax_valid,
                "execution_status": workflow_res.execution.status if workflow_res.execution else "not_executed",
                "rows_returned": workflow_res.execution.row_count if workflow_res.execution else None,
                "reference_rows": ref_rows_count,
                "corrections": correction_count,
                "semantic_warnings": workflow_res.semantic_analysis.warnings if workflow_res.semantic_analysis else [],
                "structured_warnings": [
                    w.model_dump() for w in (workflow_res.semantic_analysis.structured_warnings or [])
                ] if workflow_res.semantic_analysis else [],
                "duration_ms": elapsed_ms,
            }
            results.append(item_result)

            status_symbol = "[PASS]" if is_exec_success else "[FAIL]"
            print(f"       -> {status_symbol} Status: {workflow_res.final_status} | Rows: {item_result['rows_returned']} | Latency: {elapsed_ms}ms")
            if has_scale_mismatch:
                print(f"       [Scale Mismatch Flagged]: {workflow_res.semantic_analysis.warnings[0]}")

        except Exception as e:
            elapsed_ms = round((time.perf_counter() - q_start) * 1000, 2)
            print(f"       -> [ERROR] Error running workflow: {e}")
            results.append({
                "id": q_id,
                "category": q_cat,
                "question": q_text,
                "final_status": "exception",
                "error": str(e),
                "duration_ms": elapsed_ms,
            })

    total_time = round(time.perf_counter() - suite_start, 2)

    # Compile Evaluation Summary Report
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "dataset_name": dataset.get("name"),
        "dataset_version": dataset.get("dataset_version"),
        "model_id": getattr(ai_provider, "model_id", "mock"),
        "environment": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
        },
        "metrics": {
            "total_questions": len(questions),
            "syntax_valid_count": total_syntax_valid,
            "syntax_valid_rate": round(total_syntax_valid / len(questions), 4) if questions else 0.0,
            "schema_valid_count": total_schema_valid,
            "schema_valid_rate": round(total_schema_valid / len(questions), 4) if questions else 0.0,
            "execution_success_count": total_executed,
            "execution_success_rate": round(total_executed / len(questions), 4) if questions else 0.0,
            "corrected_success_count": total_corrected,
            "semantic_warnings_flagged": total_semantic_warnings,
            "scale_mismatches_flagged": scale_mismatches_flagged,
            "total_duration_seconds": total_time,
        },
        "detailed_results": results,
    }

    # Save to disk
    results_dir = eval_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    out_file = results_dir / f"eval_results_{int(time.time())}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n==================================================================")
    print(f" Academic Evaluation Complete")
    print(f" Total Duration: {total_time}s")
    print(f" Syntax Validity: {total_syntax_valid}/{len(questions)} ({summary['metrics']['syntax_valid_rate']*100:.1f}%)")
    print(f" Execution Success: {total_executed}/{len(questions)} ({summary['metrics']['execution_success_rate']*100:.1f}%)")
    print(f" Scale Mismatches Flagged: {scale_mismatches_flagged}")
    print(f" Results Saved to: {out_file}")
    print(f"==================================================================\n")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SchemaSense AI Academic Evaluation Suite")
    parser.add_argument("--mode", choices=["mock", "local"], default="mock", help="Execution mode")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of evaluation questions")
    args = parser.parse_args()

    asyncio.run(run_academic_evaluation(mode=args.mode, limit=args.limit))
