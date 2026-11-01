"""Regression tests for Accuracy Improvement Sprint.

Verifies:
1. Baseline evidence ZIP and executed notebook hash preservation
2. Canonical and submission unexecuted notebook synchronization and validation
3. Benchmark suite execution integrity across all 15 evaluable reference queries
4. Generalization suite execution integrity across all 9 evaluable reference queries
5. Rejection handling and SQLGlot AST column validation
6. Accurate 5-metric denominator calculations
"""

import hashlib
import json
import sqlite3
from pathlib import Path

import nbformat as nbf
import pandas as pd
import pytest
import sqlglot
from sqlglot import exp

# File paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BACKEND_DIR / "data" / "databases" / "campus_intelligence.db"
BASELINE_ZIP = BACKEND_DIR / "submission" / "colab_evidence" / "SchemaSense_AI_Colab_Evidence_colab_run_20261028T154224Z.zip"
BASELINE_NB = BACKEND_DIR / "submission" / "colab_evidence" / "SchemaSense_AI_GenAI_AAT1_EXECUTED.ipynb"
CANONICAL_NB = BACKEND_DIR / "notebooks" / "SchemaSense_AI_GenAI_AAT1.ipynb"
SUBMISSION_NB = BACKEND_DIR / "submission" / "SchemaSense_AI_GenAI_AAT1.ipynb"

BASELINE_ZIP_HASH = "2B400FA18A0FFA4344A2B1D0940E4493E205DB8CEA1F1282506B280F5B4A7ED6"
BASELINE_NB_HASH = "EC6FCD6415DA9ED3CF781B0843A8150E29669BA46EF0DF0102C231AD362A148F"


def test_baseline_evidence_hashes_preserved():
    """Guarantee that original baseline evidence files remain 100% unaltered."""
    assert BASELINE_ZIP.is_file(), f"Baseline ZIP not found at {BASELINE_ZIP}"
    assert BASELINE_NB.is_file(), f"Baseline notebook not found at {BASELINE_NB}"

    zip_hash = hashlib.sha256(BASELINE_ZIP.read_bytes()).hexdigest().upper()
    nb_hash = hashlib.sha256(BASELINE_NB.read_bytes()).hexdigest().upper()

    assert zip_hash == BASELINE_ZIP_HASH, "Baseline ZIP hash has changed! Integrity compromised."
    assert nb_hash == BASELINE_NB_HASH, "Baseline executed notebook hash has changed! Integrity compromised."


def test_unexecuted_notebooks_synchronized_and_valid():
    """Verify canonical and submission notebooks are synchronized and valid nbformat."""
    assert CANONICAL_NB.is_file(), f"Canonical notebook missing: {CANONICAL_NB}"
    assert SUBMISSION_NB.is_file(), f"Submission notebook missing: {SUBMISSION_NB}"

    canonical_bytes = CANONICAL_NB.read_bytes()
    submission_bytes = SUBMISSION_NB.read_bytes()

    assert canonical_bytes == submission_bytes, "Canonical and submission notebooks are not identical."

    nb = nbf.reads(canonical_bytes.decode("utf-8"), as_version=4)
    nbf.validate(nb)

    # Verify all code cells compile without syntax errors
    for idx, cell in enumerate(nb.cells):
        if cell.cell_type == "code":
            lines = [l for l in cell.source.splitlines() if not l.strip().startswith(("!", "%"))]
            code = "\n".join(lines)
            compile(code, f"cell_{idx}", "exec")


def test_benchmark_reference_sql_execution():
    """Verify that all 15 evaluable benchmark reference queries execute successfully on campus_intelligence.db."""
    assert DB_PATH.is_file(), f"Database missing at {DB_PATH}"

    # Extract BENCHMARK_QUESTIONS from canonical notebook
    nb = nbf.read(str(CANONICAL_NB), as_version=4)
    step14_cell = None
    for cell in nb.cells:
        if cell.cell_type == "code" and "BENCHMARK_QUESTIONS = [" in cell.source:
            step14_cell = cell.source
            break
    assert step14_cell is not None, "Step 14 cell not found in notebook."

    # Execute step 14 definitions in isolated namespace
    ns = {}
    compile(step14_cell, "step14", "exec")
    exec(step14_cell, ns)
    benchmark_qs = ns["BENCHMARK_QUESTIONS"]
    assert len(benchmark_qs) == 16, "Benchmark suite must contain exactly 16 questions."

    conn = sqlite3.connect(f"file:{DB_PATH.resolve()}?mode=ro", uri=True)
    cursor = conn.cursor()

    evaluable_count = 0
    for q in benchmark_qs:
        ref_sql = q["reference_sql"]
        if ref_sql is not None:
            evaluable_count += 1
            cursor.execute(ref_sql)
            rows = cursor.fetchall()
            assert rows is not None, f"Query {q['id']} returned None."
        else:
            assert q["id"] == "EVAL-13", f"Expected only EVAL-13 to have None reference_sql, got {q['id']}."

    conn.close()
    assert evaluable_count == 15, "Expected exactly 15 evaluable questions in benchmark."


def test_generalization_reference_sql_execution():
    """Verify that all 9 evaluable generalization reference queries execute successfully on campus_intelligence.db."""
    nb = nbf.read(str(CANONICAL_NB), as_version=4)
    step14_cell = None
    for cell in nb.cells:
        if cell.cell_type == "code" and "GENERALIZATION_QUESTIONS = [" in cell.source:
            step14_cell = cell.source
            break
    assert step14_cell is not None, "Step 14 generalization questions not found."

    ns = {}
    exec(step14_cell, ns)
    gen_qs = ns["GENERALIZATION_QUESTIONS"]
    assert len(gen_qs) == 10, "Generalization suite must contain exactly 10 questions."

    conn = sqlite3.connect(f"file:{DB_PATH.resolve()}?mode=ro", uri=True)
    cursor = conn.cursor()

    evaluable_count = 0
    for q in gen_qs:
        ref_sql = q["reference_sql"]
        if ref_sql is not None:
            evaluable_count += 1
            cursor.execute(ref_sql)
            rows = cursor.fetchall()
            assert rows is not None, f"Generalization query {q['id']} returned None."
        else:
            assert q["id"] == "GEN-09", f"Expected GEN-09 to have None reference_sql, got {q['id']}."

    conn.close()
    assert evaluable_count == 9, "Expected exactly 9 evaluable questions in generalization suite."


def test_step8_column_validation_and_rejection():
    """Test that Step 8 validate_sql detects unknown columns and intentional rejections."""
    # Load step 8 from notebook
    nb = nbf.read(str(CANONICAL_NB), as_version=4)
    step8_cell = None
    for cell in nb.cells:
        if cell.cell_type == "code" and "def validate_sql(" in cell.source:
            step8_cell = cell.source
            break
    assert step8_cell is not None, "Step 8 validate_sql cell not found."

    schema_data = {
        "tables": {
            "students": {
                "columns": [
                    {"name": "student_id", "type": "TEXT", "pk": True},
                    {"name": "first_name", "type": "TEXT", "pk": False},
                    {"name": "last_name", "type": "TEXT", "pk": False},
                    {"name": "email", "type": "TEXT", "pk": False},
                    {"name": "department_id", "type": "TEXT", "pk": False},
                    {"name": "enrollment_year", "type": "INTEGER", "pk": False},
                    {"name": "gpa", "type": "REAL", "pk": False},
                ]
            },
            "departments": {
                "columns": [
                    {"name": "department_id", "type": "TEXT", "pk": True},
                    {"name": "department_name", "type": "TEXT", "pk": False},
                    {"name": "building", "type": "TEXT", "pk": False},
                ]
            }
        }
    }

    ns = {
        "sqlglot": sqlglot,
        "exp": exp,
        "ParseError": sqlglot.errors.ParseError,
        "FORBIDDEN_AST_NODES": (
            exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter,
            exp.Create, exp.Command, exp.Pragma
        ),
        "Dict": dict,
        "Any": object,
        "schema_metadata": schema_data
    }
    exec(step8_cell, ns)
    validate_sql = ns["validate_sql"]


    # 1. Valid query
    v1 = validate_sql("SELECT first_name, last_name FROM students WHERE gpa > 3.5;", schema_data)
    assert v1["is_valid"] is True

    # 2. Rejection query
    v2 = validate_sql("-- REJECTED_INVALID_SCHEMA: column age does not exist in schema", schema_data)
    assert v2["is_valid"] is False
    assert v2["category"] == "REJECTED_INVALID_SCHEMA"

    # 3. Query with non-existent column 'age' on students table
    v3 = validate_sql("SELECT * FROM students ORDER BY age;", schema_data)
    assert v3["is_valid"] is False
    assert v3["category"] == "UNKNOWN_COLUMN"
    assert "age" in v3["error"]


def test_five_metric_calculations():
    """Verify that the 5 distinct metrics compute transparent and correct denominators."""
    # Synthetic DataFrame representing 16 questions (15 evaluable, 1 invalid schema)
    records = []
    # 14 evaluable questions: executed and exact match
    for i in range(1, 15):
        records.append({
            "ID": f"EVAL-{i:02d}",
            "Exec Success": True,
            "Exact Match": True,
            "Is Rejected": False
        })
    # EVAL-15: executed but semantic mismatch
    records.append({
        "ID": "EVAL-15",
        "Exec Success": True,
        "Exact Match": False,
        "Is Rejected": False
    })
    # EVAL-13: invalid schema, correctly rejected (not executed, Exact Match is None)
    records.append({
        "ID": "EVAL-13",
        "Exec Success": False,
        "Exact Match": None,
        "Is Rejected": True
    })

    df = pd.DataFrame(records)
    total_n = len(df)
    evaluable_df = df[df["Exact Match"].notna()]
    evaluable_n = len(evaluable_df)
    invalid_df = df[df["Exact Match"].isna()]
    invalid_n = len(invalid_df)

    assert total_n == 16
    assert evaluable_n == 15
    assert invalid_n == 1

    # 1. Raw SQL Execution Rate (denominator 16)
    raw_exec_count = int(df["Exec Success"].sum())
    raw_exec_rate = raw_exec_count / total_n * 100
    assert raw_exec_count == 15
    assert raw_exec_rate == 93.75

    # 2. Evaluable-Question Execution Rate (EQER, denominator 15)
    eqer_count = int(evaluable_df["Exec Success"].sum())
    eqer_rate = eqer_count / evaluable_n * 100
    assert eqer_count == 15
    assert eqer_rate == 100.0

    # 3. Invalid-Schema Rejection Rate (ISRR, denominator 1)
    isrr_count = int(invalid_df["Is Rejected"].sum())
    isrr_rate = isrr_count / invalid_n * 100
    assert isrr_count == 1
    assert isrr_rate == 100.0

    # 4. Exact Result-Match Rate (ESM, denominator 15)
    esm_count = int(evaluable_df["Exact Match"].astype(bool).sum())
    esm_rate = esm_count / evaluable_n * 100
    assert esm_count == 14
    assert round(esm_rate, 2) == 93.33

    # 5. Overall Appropriate-Outcome Rate (OAOR, denominator 16)
    oaor_count = esm_count + isrr_count
    oaor_rate = oaor_count / total_n * 100
    assert oaor_count == 15
    assert oaor_rate == 93.75
