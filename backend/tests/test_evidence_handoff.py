"""Automated verification tests for Colab evidence export, import security, cell map, and report handoff.

SYNTHETIC TEST FIXTURE SUITE — NOT A REAL MODEL EXPERIMENT
All fixtures in this file are synthetic mock records created exclusively for unit and integration testing.
"""

import io
import json
import math
from pathlib import Path
import tempfile
import zipfile
import pytest
import nbformat as nbf

# Import tools from submission
import sys

backend_dir = Path(__file__).resolve().parent.parent
submission_dir = backend_dir / "submission"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(submission_dir) not in sys.path:
    sys.path.insert(0, str(submission_dir))

try:
    from submission.import_colab_evidence import (
        sanitize_zip_member_path,
        inspect_and_extract_zip,
        validate_run_manifest,
        validate_and_recompute_metrics,
        import_and_verify_evidence,
        CANONICAL_MODEL,
        CANONICAL_DATASET_VERSION,
        MAX_UNCOMPRESSED_MEMBER_SIZE,
    )
    from submission.generate_reports import find_figure_file, clean_markdown_inline, to_reportlab_html
except ImportError:
    from import_colab_evidence import (  # type: ignore
        sanitize_zip_member_path,
        inspect_and_extract_zip,
        validate_run_manifest,
        validate_and_recompute_metrics,
        import_and_verify_evidence,
        CANONICAL_MODEL,
        CANONICAL_DATASET_VERSION,
        MAX_UNCOMPRESSED_MEMBER_SIZE,
    )
    from generate_reports import find_figure_file, clean_markdown_inline, to_reportlab_html  # type: ignore


# =============================================================================
# SYNTHETIC TEST FIXTURE FACTORIES — NOT A REAL MODEL EXPERIMENT
# =============================================================================

def make_synthetic_manifest(run_id="test_run_synth_001", model=CANONICAL_MODEL, ds_ver=CANONICAL_DATASET_VERSION, count=16):
    """Factory creating a synthetic run manifest for unit testing."""
    return {
        "run_id": run_id,
        "timestamp_utc": "2026-10-28T12:00:00Z",
        "model_name": model,
        "transformers_version": "4.44.0",
        "torch_version": "2.4.0",
        "sqlglot_version": "25.0.0",
        "python_version": "3.11.9",
        "hardware_type": "GPU",
        "device_name": "NVIDIA Tesla T4",
        "cuda_available": True,
        "model_precision": "torch.float16",
        "decoding_strategy": "greedy",
        "dataset_version": ds_ver,
        "dataset_fingerprint": "a1b2c3d4e5f67890",
        "total_benchmark_questions": 16,
        "evaluated_questions_count": count,
        "evaluated_question_ids": [f"EVAL-{i:02d}" for i in range(1, count + 1)],
        "benchmark_mode": "model",
        "mean_generation_latency_ms": 1100.5,
        "median_generation_latency_ms": 1050.0,
        "mean_execution_latency_ms": 3.8,
        "is_genuine_model_evaluation": True,
    }


def make_synthetic_records(count=16, pass_all=True, invalid_latencies=None):
    """Factory creating synthetic question records for unit testing."""
    records = []
    for i in range(1, count + 1):
        has_ref = (i != 13)
        gen_lat = 1100.0 if not invalid_latencies or i not in invalid_latencies else invalid_latencies[i]
        records.append({
            "question_id": f"EVAL-{i:02d}",
            "question": f"Synthetic question {i}",
            "category": "simple_selection" if i < 14 else "invalid_schema_assumptions",
            "generated_sql": f"SELECT * FROM synthetic_table_{i};",
            "syntax_valid": pass_all,
            "schema_valid": pass_all,
            "execution_status": "success" if pass_all else "error",
            "has_reference_sql": has_ref,
            "exact_match": (pass_all if has_ref else None),
            "generation_latency_ms": gen_lat,
            "execution_latency_ms": 4.0,
            "is_genuine_model_inference": True,
        })
    return records


def make_synthetic_metrics(run_id="test_run_synth_001", count=16, pass_all=True):
    """Factory creating synthetic summary metrics for unit testing."""
    evaluable = count - (1 if count >= 13 else 0)
    passes = count if pass_all else 0
    exact = evaluable if pass_all else 0
    return {
        "run_id": run_id,
        "total_evaluated": count,
        "syntax_valid_count": passes,
        "syntax_valid_rate": 100.0 if pass_all else 0.0,
        "schema_valid_count": passes,
        "schema_valid_rate": 100.0 if pass_all else 0.0,
        "execution_success_count": passes,
        "execution_success_rate": 100.0 if pass_all else 0.0,
        "exact_match_evaluable_count": evaluable,
        "exact_match_count": exact,
        "exact_match_rate": 100.0 if pass_all else 0.0,
        "mean_generation_latency_ms": 1100.5,
        "median_generation_latency_ms": 1050.0,
        "mean_execution_latency_ms": 3.8,
        "controlled_correction_initial_executable": False,
        "controlled_correction_repaired_executable": True,
        "controlled_correction_semantic_distinct_pass": False,
    }


# =============================================================================
# NOTEBOOK & REPOSITORY STRUCTURE TESTS
# =============================================================================

def test_notebook_cell_count_and_cell_map_consistency():
    """Verify that the submission notebook has exactly 38 cells and matches the cell map."""
    nb_sub = submission_dir / "SchemaSense_AI_GenAI_AAT1.ipynb"
    nb_orig = backend_dir / "notebooks" / "SchemaSense_AI_GenAI_AAT1.ipynb"
    cell_map = submission_dir / "NOTEBOOK_CELL_MAP.md"

    assert nb_sub.exists(), f"Submission notebook missing at {nb_sub}"
    assert nb_orig.exists(), f"Notebook missing at {nb_orig}"
    assert cell_map.exists(), f"NOTEBOOK_CELL_MAP.md missing at {cell_map}"

    with open(nb_sub, "r", encoding="utf-8") as f:
        nb = nbf.read(f, as_version=4)

    assert len(nb.cells) == 38, f"Expected 38 cells, got {len(nb.cells)}"

    cell_map_content = cell_map.read_text(encoding="utf-8")
    for i in range(38):
        cell_str = f"Cell {i:02d}"
        assert cell_str in cell_map_content, f"Cell index {cell_str} missing from NOTEBOOK_CELL_MAP.md"


def test_notebook_has_evidence_export_section():
    """Verify notebook contains Section 19 and Step 17 evidence export code."""
    nb_sub = submission_dir / "SchemaSense_AI_GenAI_AAT1.ipynb"
    with open(nb_sub, "r", encoding="utf-8") as f:
        nb = nbf.read(f, as_version=4)

    sec19_md = nb.cells[36]
    assert sec19_md.cell_type == "markdown"
    assert "Export Measured Evaluation Evidence" in sec19_md.source

    step17_code = nb.cells[37]
    assert step17_code.cell_type == "code"
    assert "schemasense_colab_run_manifest.json" in step17_code.source
    assert "schemasense_colab_model_results.json" in step17_code.source
    assert "schemasense_colab_evaluation_metrics.json" in step17_code.source
    assert "SchemaSense_AI_Colab_Evidence_" in step17_code.source


def test_submission_manifest_integrity():
    """Verify that all files cited in README_SUBMISSION_MANIFEST.md exist on disk."""
    manifest_path = submission_dir / "README_SUBMISSION_MANIFEST.md"
    assert manifest_path.exists()
    content = manifest_path.read_text(encoding="utf-8")

    expected_files = [
        "START_HERE_FINAL_HANDOFF.md",
        "NOTEBOOK_CELL_MAP.md",
        "COLAB_EXECUTION_PROCEDURE.md",
        "SchemaSense_AI_GenAI_AAT1.ipynb",
        "import_colab_evidence.py",
        "generate_reports.py",
        "ACADEMIC_REPORT_DRAFT.md",
        "SchemaSense_AI_AAT1_Report.docx",
        "SchemaSense_AI_AAT1_Report_Preview.pdf",
        "ACADEMIC_EVALUATION_SUMMARY.md",
        "CLAIM_EVIDENCE_LEDGER.md",
        "DEMO_INSTRUCTIONS.md",
        "SCREENSHOT_CHECKLIST.md",
    ]

    for fname in expected_files:
        assert fname in content, f"Expected {fname} in README_SUBMISSION_MANIFEST.md"
        file_path = submission_dir / fname
        assert file_path.exists(), f"Referenced file {fname} does not exist at {file_path}"


# =============================================================================
# SYNTHETIC EVIDENCE CONTRACT TESTS (PRIORITY TWO)
# =============================================================================

def test_synthetic_fixture_valid_archive_acceptance():
    """Verify that a valid synthetic evidence ZIP is accepted and verified without errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        zip_path = tmp_path / "valid_synth.zip"
        dest_dir = tmp_path / "imported"

        manifest = make_synthetic_manifest("run_valid_01")
        records = make_synthetic_records(16, pass_all=True)
        metrics = make_synthetic_metrics("run_valid_01", 16, pass_all=True)

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("schemasense_colab_run_manifest.json", json.dumps(manifest))
            zf.writestr("schemasense_colab_model_results.json", json.dumps(records))
            zf.writestr("schemasense_colab_evaluation_metrics.json", json.dumps(metrics))

        result = import_and_verify_evidence(zip_path, dest_dir)
        assert result["verification_status"] == "VERIFIED_CONSISTENT"
        assert result["benchmark_coverage"] == "FULL_BENCHMARK (16/16)"
        assert len(result["integrity_errors"]) == 0
        assert (dest_dir / "EVIDENCE_VERIFICATION_SUMMARY.md").exists()
        assert (dest_dir / "evidence_verification_report.json").exists()


def test_synthetic_fixture_missing_mandatory_fields():
    """Verify that missing mandatory manifest fields are flagged as integrity defects."""
    broken_manifest = {
        "run_id": "broken_001",
        # Missing model_name, dataset_version, etc.
    }
    errors = validate_run_manifest(broken_manifest)
    assert len(errors) > 0
    assert any("Missing manifest field" in e for e in errors)


def test_synthetic_fixture_incorrect_model_or_dataset():
    """Verify that wrong model identity or dataset version is flagged."""
    m_wrong = make_synthetic_manifest(model="meta-llama/Llama-3-8B", ds_ver="WrongDataset v2.0")
    errors = validate_run_manifest(m_wrong)
    assert any("Model identity mismatch" in e for e in errors)
    assert any("Dataset version mismatch" in e for e in errors)


def test_synthetic_fixture_duplicate_or_invalid_question_ids():
    """Verify duplicate and invalid question IDs are detected."""
    records = [
        {"question_id": "EVAL-01", "syntax_valid": True, "execution_status": "success"},
        {"question_id": "EVAL-01", "syntax_valid": True, "execution_status": "success"},  # duplicate
        {"question_id": "EVAL-99", "syntax_valid": True, "execution_status": "success"},  # invalid
    ]
    recomp, errors = validate_and_recompute_metrics(records)
    assert any("Duplicate record for question ID 'EVAL-01'" in e for e in errors)
    assert any("invalid question ID 'EVAL-99'" in e for e in errors)


def test_synthetic_fixture_negative_and_nonfinite_latencies():
    """Verify that negative, NaN, or infinite latency values are rejected."""
    records = [
        {"question_id": "EVAL-01", "syntax_valid": True, "execution_status": "success", "generation_latency_ms": -50.0},
        {"question_id": "EVAL-02", "syntax_valid": True, "execution_status": "success", "generation_latency_ms": float("nan")},
        {"question_id": "EVAL-03", "syntax_valid": True, "execution_status": "success", "execution_latency_ms": float("inf")},
    ]
    recomp, errors = validate_and_recompute_metrics(records)
    assert any("invalid or negative generation latency" in e for e in errors)
    assert any("invalid or negative execution latency" in e for e in errors)


def test_synthetic_fixture_rate_numerator_discrepancy():
    """Verify that discrepancy between summary metrics and recomputed record counts is flagged."""
    records = make_synthetic_records(16, pass_all=False)  # All passes are False
    summary_metrics = make_synthetic_metrics("run_discrepancy", 16, pass_all=True)  # Claims all passed

    recomp, errors = validate_and_recompute_metrics(records, summary_metrics)
    assert any("Discrepancy: summary syntax count" in e for e in errors)
    assert any("Discrepancy: summary exec count" in e for e in errors)


def test_synthetic_fixture_inconsistent_run_ids():
    """Verify that inconsistent run IDs across manifest and summary metrics are flagged."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        zip_path = tmp_path / "inconsistent_run_id.zip"
        dest_dir = tmp_path / "imported"

        manifest = make_synthetic_manifest("run_alpha")
        records = make_synthetic_records(16)
        metrics = make_synthetic_metrics("run_beta")  # Inconsistent run_id

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("schemasense_colab_run_manifest.json", json.dumps(manifest))
            zf.writestr("schemasense_colab_model_results.json", json.dumps(records))
            zf.writestr("schemasense_colab_evaluation_metrics.json", json.dumps(metrics))

        result = import_and_verify_evidence(zip_path, dest_dir)
        assert result["verification_status"] == "VERIFICATION_FAILED"
        assert any("Inconsistent run IDs" in e for e in result["integrity_errors"])


def test_synthetic_fixture_path_traversal_rejection():
    """Verify that Zip Slip path traversal attempts are rejected with security errors."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        with pytest.raises(ValueError, match="Illegal path traversal detected"):
            sanitize_zip_member_path(tmp_path, "../evil_file.txt")

        with pytest.raises(ValueError, match="Illegal absolute path traversal detected"):
            sanitize_zip_member_path(tmp_path, "/etc/passwd")


def test_synthetic_fixture_oversized_zip_members(monkeypatch):
    """Verify that oversized zip entries trigger decompression bomb alerts."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        zip_path = tmp_path / "oversized.zip"
        dest_dir = tmp_path / "out"

        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("big_file.bin", b"A" * 100)

        # Set limit lower than 100 bytes for test
        monkeypatch.setattr(f"{sanitize_zip_member_path.__module__}.MAX_UNCOMPRESSED_MEMBER_SIZE", 50)

        with pytest.raises(ValueError, match="exceeds limit"):
            inspect_and_extract_zip(zip_path, dest_dir)


def test_synthetic_fixture_duplicate_zip_entries():
    """Verify that archives with duplicate member entries are rejected."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        zip_path = tmp_path / "duplicate_entries.zip"
        dest_dir = tmp_path / "out"

        # Create zip with duplicate member names
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.writestr("schemasense_colab_run_manifest.json", "{}")
            zf.writestr("schemasense_colab_run_manifest.json", "{}")

        with pytest.raises(ValueError, match="duplicate member entries"):
            inspect_and_extract_zip(zip_path, dest_dir)


def test_synthetic_fixture_partial_evaluation_subset():
    """Verify that a partial evaluation run (e.g. 6 questions on CPU) is computed with accurate denominators."""
    records = make_synthetic_records(count=6, pass_all=True)
    recomp, errors = validate_and_recompute_metrics(records)

    assert len(errors) == 0
    assert recomp["total_evaluated"] == 6
    assert recomp["evaluable_exact_match_denominator"] == 6  # EVAL-01 to EVAL-06 all have reference SQL
    assert recomp["syntax_validity_rate_pct"] == 100.0
    assert recomp["exact_match_rate_pct"] == 100.0


def test_synthetic_fixture_preserves_historical_runs():
    """Verify that re-importing does not overwrite previously imported distinct runs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        dest_dir = tmp_path / "colab_evidence"

        # Import run 1
        zip1 = tmp_path / "run1.zip"
        with zipfile.ZipFile(zip1, "w") as zf:
            zf.writestr("schemasense_colab_run_manifest.json", json.dumps(make_synthetic_manifest("run_001")))
            zf.writestr("schemasense_colab_model_results.json", json.dumps(make_synthetic_records(16)))
            zf.writestr("schemasense_colab_evaluation_metrics.json", json.dumps(make_synthetic_metrics("run_001")))
        import_and_verify_evidence(zip1, dest_dir)

        # Import run 2
        zip2 = tmp_path / "run2.zip"
        with zipfile.ZipFile(zip2, "w") as zf:
            zf.writestr("schemasense_colab_run_manifest.json", json.dumps(make_synthetic_manifest("run_002")))
            zf.writestr("schemasense_colab_model_results.json", json.dumps(make_synthetic_records(16)))
            zf.writestr("schemasense_colab_evaluation_metrics.json", json.dumps(make_synthetic_metrics("run_002")))
        import_and_verify_evidence(zip2, dest_dir)

        # Both runs must be archived independently
        assert (dest_dir / "runs" / "run_001").exists()
        assert (dest_dir / "runs" / "run_002").exists()
        assert (dest_dir / "evidence_verification_run_001.json").exists()
        assert (dest_dir / "evidence_verification_run_002.json").exists()


# =============================================================================
# REPORT GENERATION & FORMATTING TESTS
# =============================================================================

def test_report_generator_screenshot_handling():
    """Verify find_figure_file correctly maps figure names and falls back safely."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        fig_dir = Path(tmp_dir)
        # Empty dir -> None
        assert find_figure_file("Figure 1 — Schema Explorer", fig_dir) is None

        # Create dummy fig01 file
        dummy_fig = fig_dir / "fig01_schema_explorer.png"
        dummy_fig.write_bytes(b"\x89PNG\r\n\x1a\n")

        found = find_figure_file("Figure 1 — Schema Explorer", fig_dir)
        assert found == dummy_fig

        # Figure 2 should still be None
        assert find_figure_file("Figure 2 — Test Verification", fig_dir) is None


def test_markdown_and_html_sanitizers():
    """Verify markdown cleaners produce safe, well-formed formatting for report generators."""
    raw = "Show all **students** with `gpa >= 3.5` & enrolled in *DEP-CS*."
    cleaned_inline = clean_markdown_inline(raw)
    assert "**" not in cleaned_inline
    assert "`" not in cleaned_inline
    assert "*" not in cleaned_inline

    rl_html = to_reportlab_html(raw)
    assert "<b>students</b>" in rl_html
    assert '<font name="Courier">gpa &gt;= 3.5</font>' in rl_html
    assert "<i>DEP-CS</i>" in rl_html
    assert "&amp;" in rl_html  # & properly escaped
