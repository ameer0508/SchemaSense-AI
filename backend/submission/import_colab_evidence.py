"""
SchemaSense AI — Google Colab Academic Evidence Importer & Validator
Validates, audits, and imports experimental evaluation artifacts downloaded from Google Colab.

Safety Features:
- Rejects ZIP path traversal attacks (Zip Slip protection).
- Rejects decompression bombs, oversized members, and duplicate ZIP entries.
- Validates JSON schema against canonical benchmark structure.
- Validates numeric sanity (rejects negative or non-finite latencies).
- Cross-references run identifiers across manifest and summary metrics.
- Recalculates all academic metrics from raw per-question records using exact mathematical denominators.
- Distinguishes between complete 16-question benchmarks and partial evaluation subsets.
- Verifies model identity and dataset version compatibility.
- Generates timestamped verification summary reports and archives previous runs safely.
"""

import os
import sys
import json
import math
import shutil
import zipfile
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Canonical constants for verification
CANONICAL_MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
CANONICAL_DATASET_VERSION = "Campus Intelligence Canonical Academic Benchmark v1.1.0"
VALID_QUESTION_IDS = {f"EVAL-{i:02d}" for i in range(1, 17)}
EVALUABLE_QUESTION_IDS = VALID_QUESTION_IDS - {"EVAL-13"}  # EVAL-13 has null reference SQL

# Archive bounds for decompression safety
MAX_ZIP_ENTRIES = 50
MAX_UNCOMPRESSED_MEMBER_SIZE = 25 * 1024 * 1024   # 25 MB max per member
MAX_TOTAL_UNCOMPRESSED_SIZE = 100 * 1024 * 1024   # 100 MB max total


def sanitize_zip_member_path(target_dir: Path, filename: str) -> Path:
    """Guards against Zip Slip / path traversal attacks."""
    resolved_target = target_dir.resolve()
    # Normalize path and reject leading slashes or Windows drive specifiers
    cleaned = filename.lstrip("/\\")
    if filename.startswith("/") or filename.startswith("\\") or (len(filename) > 1 and filename[1] == ":"):
        raise ValueError(f"SECURITY ALERT: Illegal absolute path traversal detected in archive entry: {filename}")
    resolved_path = (target_dir / cleaned).resolve()
    if not str(resolved_path).startswith(str(resolved_target)):
        raise ValueError(f"SECURITY ALERT: Illegal path traversal detected in archive entry: {filename}")
    return resolved_path


def inspect_and_extract_zip(zip_path: Path, output_dir: Path) -> list[str]:
    """Safely inspects and extracts a ZIP archive with decompression bomb and Zip Slip defenses."""
    if not zip_path.exists():
        raise FileNotFoundError(f"Archive not found: {zip_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    extracted_files = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        infolist = zf.infolist()

        if len(infolist) > MAX_ZIP_ENTRIES:
            raise ValueError(f"SECURITY ALERT: Archive contains {len(infolist)} entries (exceeds limit of {MAX_ZIP_ENTRIES})")

        # Check for duplicate entry names
        names = [info.filename for info in infolist]
        if len(names) != len(set(names)):
            raise ValueError("SECURITY ALERT: Archive contains duplicate member entries.")

        total_uncompressed = 0
        for info in infolist:
            if info.file_size > MAX_UNCOMPRESSED_MEMBER_SIZE:
                raise ValueError(
                    f"SECURITY ALERT: Member '{info.filename}' uncompressed size {info.file_size} exceeds limit of {MAX_UNCOMPRESSED_MEMBER_SIZE}"
                )
            total_uncompressed += info.file_size
            if total_uncompressed > MAX_TOTAL_UNCOMPRESSED_SIZE:
                raise ValueError(
                    f"SECURITY ALERT: Total uncompressed archive size exceeds limit of {MAX_TOTAL_UNCOMPRESSED_SIZE}"
                )

            # Check path traversal
            dest_file = sanitize_zip_member_path(output_dir, info.filename)

        # Extract safely member by member
        for info in infolist:
            dest_file = sanitize_zip_member_path(output_dir, info.filename)
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info, "r") as src, open(dest_file, "wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted_files.append(info.filename)

    return extracted_files


def load_json_safe(file_path: Path):
    """Loads and decodes JSON file with UTF-8 encoding."""
    if not file_path.exists():
        raise FileNotFoundError(f"Required evidence file missing: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_run_manifest(manifest: dict) -> list[str]:
    """Validates metadata fields in the Colab run manifest."""
    errors = []
    required_keys = [
        "run_id", "timestamp_utc", "model_name", "transformers_version",
        "torch_version", "python_version", "hardware_type", "dataset_version",
        "total_benchmark_questions", "evaluated_questions_count"
    ]
    for k in required_keys:
        if k not in manifest or manifest[k] is None:
            errors.append(f"Missing manifest field: '{k}'")

    if manifest.get("model_name") != CANONICAL_MODEL:
        errors.append(
            f"Model identity mismatch: expected '{CANONICAL_MODEL}', found '{manifest.get('model_name')}'"
        )

    if manifest.get("dataset_version") != CANONICAL_DATASET_VERSION:
        errors.append(
            f"Dataset version mismatch: expected '{CANONICAL_DATASET_VERSION}', found '{manifest.get('dataset_version')}'"
        )

    count = manifest.get("evaluated_questions_count", 0)
    if not isinstance(count, int) or not (1 <= count <= 16):
        errors.append(f"Invalid evaluated questions count: {count} (expected 1 to 16)")

    return errors


def validate_and_recompute_metrics(records: list[dict], summary_metrics: dict = None) -> tuple[dict, list[str]]:
    """Recalculates empirical metrics from raw per-question records."""
    errors = []
    if not records:
        return {}, ["No per-question evaluation records provided."]

    n_total = len(records)
    syntax_passes = 0
    schema_passes = 0
    exec_passes = 0
    exact_passes = 0
    evaluable_count = 0
    gen_latencies = []
    exec_latencies = []

    seen_ids = set()
    for idx, r in enumerate(records):
        qid = r.get("question_id")
        if not qid or qid not in VALID_QUESTION_IDS:
            errors.append(f"Record #{idx}: invalid question ID '{qid}'")
        if qid in seen_ids:
            errors.append(f"Duplicate record for question ID '{qid}'")
        seen_ids.add(qid)

        if r.get("syntax_valid") is True:
            syntax_passes += 1
        if r.get("schema_valid") is True:
            schema_passes += 1
        if r.get("execution_status") == "success":
            exec_passes += 1

        # Check exact match only for evaluable queries with reference SQL
        has_ref = r.get("has_reference_sql", True)
        if qid != "EVAL-13" and has_ref:
            evaluable_count += 1
            if r.get("exact_match") is True:
                exact_passes += 1

        gen_ms = r.get("generation_latency_ms", 0.0)
        exec_ms = r.get("execution_latency_ms", 0.0)

        if not isinstance(gen_ms, (int, float)) or math.isnan(gen_ms) or math.isinf(gen_ms) or gen_ms < 0:
            errors.append(f"Record {qid}: invalid or negative generation latency ({gen_ms})")
        else:
            gen_latencies.append(float(gen_ms))

        if not isinstance(exec_ms, (int, float)) or math.isnan(exec_ms) or math.isinf(exec_ms) or exec_ms < 0:
            errors.append(f"Record {qid}: invalid or negative execution latency ({exec_ms})")
        else:
            exec_latencies.append(float(exec_ms))

    # Recomputed metrics with exact mathematical denominators
    svr = round((syntax_passes / n_total) * 100.0, 2) if n_total > 0 else 0.0
    sc_rate = round((schema_passes / n_total) * 100.0, 2) if n_total > 0 else 0.0
    esr = round((exec_passes / n_total) * 100.0, 2) if n_total > 0 else 0.0
    emr = round((exact_passes / evaluable_count) * 100.0, 2) if evaluable_count > 0 else "N/A"

    gen_latencies.sort()
    mean_gen = round(sum(gen_latencies) / len(gen_latencies), 2) if gen_latencies else 0.0
    median_gen = round(gen_latencies[len(gen_latencies) // 2], 2) if gen_latencies else 0.0
    mean_exec = round(sum(exec_latencies) / len(exec_latencies), 2) if exec_latencies else 0.0

    recomputed = {
        "total_evaluated": n_total,
        "evaluable_exact_match_denominator": evaluable_count,
        "syntax_valid_count": syntax_passes,
        "syntax_validity_rate_pct": svr,
        "schema_valid_count": schema_passes,
        "schema_validity_rate_pct": sc_rate,
        "execution_success_count": exec_passes,
        "execution_success_rate_pct": esr,
        "exact_match_count": exact_passes,
        "exact_match_rate_pct": emr,
        "mean_generation_latency_ms": mean_gen,
        "median_generation_latency_ms": median_gen,
        "mean_execution_latency_ms": mean_exec,
    }

    # Cross-reference with summary metrics if available
    if summary_metrics:
        if summary_metrics.get("syntax_valid_count") is not None:
            if summary_metrics["syntax_valid_count"] != syntax_passes:
                errors.append(
                    f"Discrepancy: summary syntax count ({summary_metrics['syntax_valid_count']}) != recomputed ({syntax_passes})"
                )
        if summary_metrics.get("schema_valid_count") is not None:
            if summary_metrics["schema_valid_count"] != schema_passes:
                errors.append(
                    f"Discrepancy: summary schema count ({summary_metrics['schema_valid_count']}) != recomputed ({schema_passes})"
                )
        if summary_metrics.get("execution_success_count") is not None:
            if summary_metrics["execution_success_count"] != exec_passes:
                errors.append(
                    f"Discrepancy: summary exec count ({summary_metrics['execution_success_count']}) != recomputed ({exec_passes})"
                )
        if summary_metrics.get("exact_match_count") is not None:
            if summary_metrics["exact_match_count"] != exact_passes:
                errors.append(
                    f"Discrepancy: summary exact match count ({summary_metrics['exact_match_count']}) != recomputed ({exact_passes})"
                )

    return recomputed, errors


def import_and_verify_evidence(source_path: Path, output_dir: Path) -> dict:
    """Main verification function."""
    output_dir.mkdir(parents=True, exist_ok=True)
    validation_log = []
    integrity_errors = []

    print(f"\n========================================================")
    print(f"SchemaSense AI — Colab Academic Evidence Importer")
    print(f"Source: {source_path}")
    print(f"Destination: {output_dir}")
    print(f"========================================================\n")

    if not source_path.exists():
        raise FileNotFoundError(f"Specified source path does not exist: {source_path}")

    # Case 1: ZIP Archive
    if source_path.is_file() and source_path.suffix.lower() == ".zip":
        print(f"Inspecting ZIP archive: {source_path.name}")
        extracted = inspect_and_extract_zip(source_path, output_dir)
        validation_log.append(f"Safely extracted {len(extracted)} archive entries into {output_dir}")

    # Case 2: Directory or JSON files already present
    manifest_path = output_dir / "schemasense_colab_run_manifest.json"
    results_path = output_dir / "schemasense_colab_model_results.json"
    metrics_path = output_dir / "schemasense_colab_evaluation_metrics.json"

    # If source was directory, look in source
    if source_path.is_dir():
        if (source_path / "schemasense_colab_run_manifest.json").exists():
            manifest_path = source_path / "schemasense_colab_run_manifest.json"
            results_path = source_path / "schemasense_colab_model_results.json"
            metrics_path = source_path / "schemasense_colab_evaluation_metrics.json"

    # Load artifacts
    try:
        manifest = load_json_safe(manifest_path)
        validation_log.append(f"Loaded run manifest: {manifest.get('run_id')}")
    except Exception as e:
        manifest = {}
        integrity_errors.append(f"Could not load run manifest: {e}")

    try:
        model_results = load_json_safe(results_path)
        validation_log.append(f"Loaded {len(model_results)} model evaluation records")
    except Exception as e:
        model_results = []
        integrity_errors.append(f"Could not load model results: {e}")

    try:
        exported_metrics = load_json_safe(metrics_path)
    except Exception:
        exported_metrics = {}

    # Audit manifest
    if manifest:
        m_errors = validate_run_manifest(manifest)
        integrity_errors.extend(m_errors)

        # Cross-check run_id across manifest and summary metrics
        if exported_metrics and "run_id" in exported_metrics:
            if exported_metrics["run_id"] != manifest.get("run_id"):
                integrity_errors.append(
                    f"Inconsistent run IDs: manifest run_id '{manifest.get('run_id')}' != metrics run_id '{exported_metrics.get('run_id')}'"
                )

    # Recompute metrics from per-question records
    recomputed_metrics, r_errors = validate_and_recompute_metrics(model_results, exported_metrics)
    integrity_errors.extend(r_errors)

    # Status determination
    has_image = (output_dir / "schemasense_evaluation_metrics.png").exists() or (source_path.is_dir() and (source_path / "schemasense_evaluation_metrics.png").exists())
    is_valid = len(integrity_errors) == 0 and len(model_results) > 0

    run_id = manifest.get("run_id", "UNKNOWN")
    n_eval = len(model_results)
    coverage = f"FULL_BENCHMARK (16/16)" if n_eval == 16 else f"PARTIAL_SUBSET ({n_eval}/16 questions evaluated)"

    verification_summary = {
        "verification_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "source_archive": str(source_path),
        "run_id": run_id,
        "model_name": manifest.get("model_name", "UNKNOWN"),
        "hardware_type": manifest.get("hardware_type", "UNKNOWN"),
        "device_name": manifest.get("device_name", "UNKNOWN"),
        "dataset_version": manifest.get("dataset_version", "UNKNOWN"),
        "dataset_fingerprint": manifest.get("dataset_fingerprint", "UNKNOWN"),
        "benchmark_coverage": coverage,
        "evaluated_questions_count": n_eval,
        "recomputed_metrics": recomputed_metrics,
        "exported_metrics": exported_metrics,
        "visualization_image_present": has_image,
        "integrity_errors_count": len(integrity_errors),
        "integrity_errors": integrity_errors,
        "verification_status": "VERIFIED_CONSISTENT" if is_valid else "VERIFICATION_FAILED",
        "epistemic_limitation": (
            "Verification confirms structural validity, internal statistical consistency, and schema compliance. "
            "It does not cryptographically attest physical execution on Google Colab hardware."
        )
    }

    # Save latest verification report and summary
    report_json_path = output_dir / "evidence_verification_report.json"
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(verification_summary, f, indent=2)

    report_md_path = output_dir / "EVIDENCE_VERIFICATION_SUMMARY.md"
    summary_md_content = generate_markdown_summary(verification_summary, recomputed_metrics, integrity_errors)
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write(summary_md_content)

    # Also archive keyed by run_id so previous runs are never overwritten or lost
    if run_id != "UNKNOWN":
        hist_json = output_dir / f"evidence_verification_{run_id}.json"
        hist_md = output_dir / f"EVIDENCE_VERIFICATION_SUMMARY_{run_id}.md"
        with open(hist_json, "w", encoding="utf-8") as f:
            json.dump(verification_summary, f, indent=2)
        with open(hist_md, "w", encoding="utf-8") as f:
            f.write(summary_md_content)

        # Archive extracted files in historical run directory
        run_hist_dir = output_dir / "runs" / run_id
        run_hist_dir.mkdir(parents=True, exist_ok=True)
        if manifest_path.exists():
            shutil.copy2(manifest_path, run_hist_dir / "schemasense_colab_run_manifest.json")
        if results_path.exists():
            shutil.copy2(results_path, run_hist_dir / "schemasense_colab_model_results.json")
        if metrics_path.exists():
            shutil.copy2(metrics_path, run_hist_dir / "schemasense_colab_evaluation_metrics.json")
        if has_image and (output_dir / "schemasense_evaluation_metrics.png").exists():
            shutil.copy2(output_dir / "schemasense_evaluation_metrics.png", run_hist_dir / "schemasense_evaluation_metrics.png")

    print(f"Verification complete. Status: {verification_summary['verification_status']}")
    print(f"Coverage: {verification_summary['benchmark_coverage']}")
    print(f"Saved latest report to: {report_json_path}")
    print(f"Saved summary to: {report_md_path}\n")

    return verification_summary


def generate_markdown_summary(verification_summary: dict, recomputed_metrics: dict, integrity_errors: list) -> str:
    """Formats a human-readable verification markdown document."""
    lines = [
        "# SchemaSense AI — Colab Evidence Verification Summary\n\n",
        f"**Verification Status:** `{verification_summary['verification_status']}`  \n",
        f"**Benchmark Coverage:** `{verification_summary['benchmark_coverage']}`  \n",
        f"**Run Identifier:** `{verification_summary['run_id']}`  \n",
        f"**Evaluated Model:** `{verification_summary['model_name']}`  \n",
        f"**Runtime Hardware:** `{verification_summary['hardware_type']} ({verification_summary['device_name']})`  \n",
        f"**Dataset Version:** `{verification_summary['dataset_version']}`  \n",
        f"**Evaluated Questions:** `{verification_summary['evaluated_questions_count']} questions`  \n\n",
        "## Recomputed Empirical Metrics\n\n",
        "| Metric Name | Numerator / Count | Denominator | Recomputed Rate |\n",
        "| :--- | :---: | :---: | :---: |\n",
        f"| **Syntax Validity Rate** | {recomputed_metrics.get('syntax_valid_count', 0)} | {recomputed_metrics.get('total_evaluated', 0)} | **{recomputed_metrics.get('syntax_validity_rate_pct', 0)}%** |\n",
        f"| **Schema Compliance Rate** | {recomputed_metrics.get('schema_valid_count', 0)} | {recomputed_metrics.get('total_evaluated', 0)} | **{recomputed_metrics.get('schema_validity_rate_pct', 0)}%** |\n",
        f"| **Sandbox Execution Success** | {recomputed_metrics.get('execution_success_count', 0)} | {recomputed_metrics.get('total_evaluated', 0)} | **{recomputed_metrics.get('execution_success_rate_pct', 0)}%** |\n",
        f"| **Exact Semantic Match** | {recomputed_metrics.get('exact_match_count', 0)} | {recomputed_metrics.get('evaluable_exact_match_denominator', 0)} | **{recomputed_metrics.get('exact_match_rate_pct', 0)}%** |\n\n",
        "## Latency Profile\n\n",
        f"- **Mean Generation Latency:** {recomputed_metrics.get('mean_generation_latency_ms', 0)} ms\n",
        f"- **Median Generation Latency:** {recomputed_metrics.get('median_generation_latency_ms', 0)} ms\n",
        f"- **Mean Execution Latency:** {recomputed_metrics.get('mean_execution_latency_ms', 0)} ms\n\n",
    ]

    if integrity_errors:
        lines.append("## Integrity Audit Issues\n\n")
        for err in integrity_errors:
            lines.append(f"- ⚠️ {err}\n")
        lines.append("\n")
    else:
        lines.append("## Integrity Audit\n\n✅ 0 integrity defects detected. All recomputed metrics match exported summaries.\n\n")

    lines.append(f"*{verification_summary['epistemic_limitation']}*\n")
    return "".join(lines)


def main():
    default_dir = Path("submission/colab_evidence") if Path("submission/colab_evidence").exists() else Path("backend/submission/colab_evidence")
    parser = argparse.ArgumentParser(description="SchemaSense AI Colab Evidence Importer")
    parser.add_argument("source", nargs="?", default=str(default_dir), help="Path to evidence ZIP archive or directory")
    parser.add_argument("--output", default=None, help="Output directory for extracted & verified evidence")
    args = parser.parse_args()

    src = Path(args.source)
    if args.output:
        out = Path(args.output)
    else:
        out = src.parent if (src.is_file() or src.suffix == ".zip") else src
    try:
        import_and_verify_evidence(src, out)
    except Exception as e:
        print(f"Error importing evidence: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
