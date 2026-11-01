"""Phase 5 Smoke Test Runner.

Demonstrates:
Part 1: Controlled Correction Pipeline Test (Mock Provider)
Part 2: Real Generative AI Transformer End-to-End Smoke Test (Qwen/Qwen2.5-Coder-1.5B-Instruct)
"""

import asyncio
import json
import time
from app.db.seed_demo import DEMO_DB_ID
from app.schemas.execution import AIQueryRequest
from app.services.ai_provider import (
    LocalTransformersProvider,
    MockAIProvider,
    set_ai_provider,
)
from app.services.correction_service import get_correction_service
from app.services.interfaces import SQLCorrectionResult, SQLGenerationResult


async def run_controlled_correction_test():
    """Controlled Correction Pipeline Test — Mock Provider.

    Demonstrates deliberate generation of an invalid SQL candidate (unknown column)
    followed by automated execution feedback, error diagnosis, and successful repair.
    """
    print("\n" + "=" * 80)
    print("PART 1: CONTROLLED CORRECTION PIPELINE TEST — MOCK PROVIDER")
    print("=" * 80)

    class ControlledRepairMock(MockAIProvider):
        def __init__(self):
            super().__init__()
            self.iteration = 0

        async def generate_sql(self, question, schema, dialect="sqlite", context=None):
            # Deliberately generate an invalid column to trigger the correction loop
            return SQLGenerationResult(
                sql="SELECT student_name, gpa FROM students ORDER BY gpa DESC LIMIT 5;",
                explanation="Initial candidate with hallucinated 'student_name' column",
                confidence_score=0.75,
            )

        async def generate_correction(self, question, failed_sql, error_category, error_message, schema, dialect="sqlite", context=None):
            self.iteration += 1
            print(f"  [AI Feedback Received] Category: {error_category}")
            print(f"  [AI Feedback Diagnostic] {error_message}")
            return SQLCorrectionResult(
                sql="SELECT first_name, last_name, gpa FROM students ORDER BY gpa DESC LIMIT 5;",
                explanation="Repaired column reference to 'first_name, last_name' based on verified schema",
                changes_made=["Replaced non-existent 'student_name' with verified schema columns 'first_name, last_name'"],
            )

    mock = ControlledRepairMock()
    set_ai_provider(mock)
    svc = get_correction_service()

    req = AIQueryRequest(
        question="Show top 5 students by GPA",
        database_id=DEMO_DB_ID,
        auto_correct=True,
    )

    start = time.perf_counter()
    response = await svc.run_query_workflow(req)
    total_time = round((time.perf_counter() - start) * 1000, 2)

    print("\nControlled Pipeline Execution Summary:")
    print(f"  Final Status:               {response.final_status}")
    print(f"  Total Correction Attempts:  {response.total_correction_attempts}")
    print(f"  Total Attempts Evaluated:   {len(response.correction_trace)}")
    print(f"  Initial Generated SQL:      {response.initial_sql}")
    print(f"  Final Corrected SQL:        {response.final_sql}")
    print(f"  Rows Returned:              {response.execution.row_count if response.execution else 0}")
    print(f"  Total Duration:             {total_time} ms")
    print(f"  Executive Summary:          {response.summary}")

    print("\nAttempt-by-Attempt Trace:")
    for a in response.correction_trace:
        print(f"  - Attempt #{a.attempt_number} ({a.attempt_type}):")
        print(f"      Candidate SQL:      {a.sql}")
        print(f"      Validation Status:  {a.validation_status}")
        print(f"      Execution Status:   {a.execution_status}")
        print(f"      Error Category:     {a.error_category}")
        print(f"      Diagnostic Message: {a.error_message}")
        print(f"      Accepted:           {a.is_accepted}")
        if a.changes_made:
            print(f"      Changes Applied:    {a.changes_made}")

    return response


async def run_real_model_smoke_test():
    """Real Model End-to-End Smoke Test — Local Qwen2.5-Coder-1.5B-Instruct on CPU."""
    print("\n" + "=" * 80)
    print("PART 2: REAL LOCAL MODEL END-TO-END SMOKE TEST (Qwen2.5-Coder-1.5B-Instruct)")
    print("=" * 80)

    provider = LocalTransformersProvider(
        model_id="Qwen/Qwen2.5-Coder-1.5B-Instruct",
        device="cpu",
    )
    set_ai_provider(provider)

    print("Initializing real transformer model on CPU...")
    init_start = time.perf_counter()
    await provider.initialize()
    print(f"Model loaded successfully in {round(time.perf_counter() - init_start, 2)}s.")

    svc = get_correction_service()

    test_questions = [
        ("Question 1 — Simple Filtering", "Show students with a GPA above 8.5."),
        ("Question 2 — Aggregation", "How many students belong to each department?"),
        ("Question 3 — Multi-Table JOIN", "List student names along with their department names."),
        ("Question 4 — Ranking", "Show the top 5 students with the highest GPA."),
    ]

    results = []

    for label, question in test_questions:
        print(f"\n--- Running: {label} ---")
        print(f"Question: \"{question}\"")
        req = AIQueryRequest(
            question=question,
            database_id=DEMO_DB_ID,
            auto_correct=True,
            temperature=0.0,
        )

        q_start = time.perf_counter()
        resp = await svc.run_query_workflow(req)
        q_duration = round(time.perf_counter() - q_start, 2)

        print(f"  Final Status:        {resp.final_status}")
        print(f"  Generated SQL:       {resp.final_sql}")
        print(f"  Validation Status:   {resp.validation.status} (Valid: {resp.validation.is_valid})")
        print(f"  Execution Status:    {resp.execution.status if resp.execution else 'not_executed'}")
        print(f"  Rows Returned:       {resp.execution.row_count if resp.execution else 0}")
        print(f"  Execution Time:      {resp.execution.duration_ms if resp.execution else 0.0} ms")
        print(f"  Workflow Duration:   {q_duration} s")
        print(f"  Correction Attempts: {resp.total_correction_attempts}")
        if resp.semantic_analysis:
            print(f"  Semantic Sound:      {resp.semantic_analysis.is_semantically_sound}")
            if resp.semantic_analysis.warnings:
                print(f"  Semantic Warnings:   {resp.semantic_analysis.warnings}")
            if resp.semantic_analysis.recommendation:
                print(f"  Recommendation:      {resp.semantic_analysis.recommendation}")

        results.append({
            "label": label,
            "question": question,
            "sql": resp.final_sql,
            "validation_status": resp.validation.status,
            "execution_status": resp.execution.status if resp.execution else "not_executed",
            "row_count": resp.execution.row_count if resp.execution else 0,
            "execution_ms": resp.execution.duration_ms if resp.execution else 0.0,
            "duration_s": q_duration,
            "corrections": resp.total_correction_attempts,
            "semantic_sound": resp.semantic_analysis.is_semantically_sound if resp.semantic_analysis else True,
            "warnings": resp.semantic_analysis.warnings if resp.semantic_analysis else [],
        })

    return results


async def main():
    await run_controlled_correction_test()
    try:
        await run_real_model_smoke_test()
    except Exception as e:
        print(f"\n[Notice] Real model smoke test encountered runtime error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
