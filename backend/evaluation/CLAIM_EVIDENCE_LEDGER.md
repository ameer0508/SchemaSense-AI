# SchemaSense AI — Academic Evidence Ledger & Claim Verification Matrix
## Phase 8: Final Quality Assurance & Evidence Integrity Audit

This ledger provides an uncompromising, academically honest audit of all empirical claims, benchmark figures, and performance metrics across the SchemaSense AI project.

### Classification Key
- **`VERIFIED`**: Supported by an unedited, reproducible, timestamped raw JSON log or passing unit tests in this repository.
- **`PARTIALLY_VERIFIED`**: Validated in code and local simulation, but full end-to-end cloud execution remains pending.
- **`UNVERIFIED / PROJECTED`**: Theoretical or estimated values previously cited that lack raw per-question execution logs. These must **never** be presented as empirical facts in academic reports.
- **`ILLUSTRATIVE`**: Synthetic data used solely as a visualization or UI template, not representing an actual measured experiment.

---

## 1. Master Evidence Matrix

| Claim ID | Claim Description | Evidence Artifact | Mode & Environment | Verification Status | Measured Value / Details |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **CLM-001** | Real Qwen2.5-Coder-1.5B-Instruct runs locally without paid APIs | `backend/evaluation/results/real_qwen_correction_result.json` | Mode B (Genuine Transformers on CPU) | **`VERIFIED`** | Generates valid SQL; measured CPU latency is **51,828.67 ms (51.8s)**. |
| **CLM-002** | Execution-guided correction repairs invalid column references | `backend/evaluation/results/real_qwen_correction_result.json` | Mode C (Controlled Correction on CPU) | **`VERIFIED`** | Repaired `student_name` $\to$ `first_name, last_name`. Execution completed in **0.58 ms**. |
| **CLM-003** | Semantic limitation: correction repaired syntax but introduced duplicate rows | `backend/evaluation/results/real_qwen_correction_result.json` | Mode C & Semantic Integrity Analysis | **`VERIFIED`** | Returned 5 rows with only 2 distinct students (Emma Goldberg x2, Sofia Ramirez x3) due to 1-to-N join on `enrollments`. Flagged by `POTENTIALLY_MULTIPLICATIVE_JOIN`. |
| **CLM-004** | 16/16 pipeline tests executed cleanly via Mock Provider | `backend/evaluation/results/eval_results_1793112556.json` | Mode A (Deterministic Mock Pipeline Test) | **`VERIFIED`** *(Pipeline Plumbing Only)* | 16/16 queries executed in 0.18s total. **CRITICAL:** Canned mock SQL; does NOT measure model generation accuracy! |
| **CLM-005** | Curated reference SQL queries execute correctly on SQLite | `backend/tests/test_notebook_and_eval.py` | Mode A (Reference Ground Truth) | **`VERIFIED`** | 15 of 15 reference queries return valid records (EVAL-13 has null reference SQL by design). |
| **CLM-006** | 86.7% syntax, 80.0% schema, 73.3% execution, 66.7% exact match pass rates | *None (Previously cited in Phase 7 report)* | Projected Model Target (Denominator 15) | **`UNVERIFIED / PROJECTED`** | **Rectification:** No 15-question genuine Qwen generation log exists in the repo. These were theoretical targets ($13/15, 12/15, 11/15, 10/15$) and must be labeled as projected. |
| **CLM-007** | 420 ms initial / 480 ms post-correction GPU T4 inference latency | *None (Theoretical FP16 token throughput)* | Projected Hardware Estimate | **`UNVERIFIED / PROJECTED`** | **Rectification:** Local test environment has no GPU. Colab T4 execution must be captured by students directly in Google Colab. |
| **CLM-008** | Colab notebook is valid, self-contained, and path-independent | `backend/tests/test_notebook_and_eval.py` | `nbformat` v4 & regex path audit | **`VERIFIED`** | 36 cells pass `nbformat.validate()`; 0 Windows path references found; local non-inference cells executed successfully. |
| **CLM-009** | Dual-layer AST + SQLite C-Authorizer sandbox blocks write commands | `backend/tests/test_execution.py` | Unit & Integration Security Sandbox | **`VERIFIED`** | 33 security tests pass: `DROP`, `INSERT`, `UPDATE`, `DELETE`, `ATTACH`, multi-statement chaining blocked. |
| **CLM-010** | Campus Intelligence GPA scale is strictly 0.0–4.0 | `backend/tests/test_semantic_analyzer.py` | Schema Catalog & Semantic Analyzer | **`VERIFIED`** | Database schema enforces `CHECK(gpa >= 0.0 AND gpa <= 4.0)`. Query `gpa > 8.5` triggers `POSSIBLE_SCALE_MISMATCH`. |

---

## 2. Inconsistencies Identified & Corrected

### Inconsistency 1: 16-Question Benchmark vs. Denominator of 15
- **Investigation:** `evaluation_dataset.json` contains 16 numbered questions (`EVAL-01` to `EVAL-16`).
- **Explanation:** `EVAL-13` ("List students ordered by their age") has `"reference_sql": null` because it intentionally queries a non-existent attribute (`age`) to evaluate schema rejection/correction. Therefore, only **15 questions** have reference SQL for exact multiset answer evaluation!
- **Resolution:** The evaluation suite now explicitly separates:
  - Total Questions: 16 (for syntax, schema, and execution tracking).
  - Objectively Evaluable with Reference SQL: 15 (for exact-match and semantic accuracy calculation).

### Inconsistency 2: Mock 16/16 Result vs. Real Model Accuracy
- **Investigation:** Phase 6 reported "16/16 evaluation cases passed".
- **Explanation:** That run (`eval_results_1793112556.json`) ran in `mode="mock"` using `MockAIProvider`. It returned canned SQL strings that executed without syntax errors, but returned generic rows that did not answer the questions.
- **Resolution:** We strictly label that test as **"Mode A: Pipeline Plumbing Test"** and explicitly forbid citing it as generative model accuracy.

### Inconsistency 3: Google Colab T4 GPU Claims
- **Investigation:** Previous summaries cited ~420 ms GPU latency and full Colab verification.
- **Explanation:** Local development was conducted on Windows CPU. The notebook was structured and validated to run on Colab T4, but actual execution on Google's cloud servers has not been completed.
- **Resolution:** All GPU latency claims are reclassified as **"Unverified / Projected for T4 GPU"**. The demonstration runbook instructs students on how to perform and record the actual run on Google Colab.
