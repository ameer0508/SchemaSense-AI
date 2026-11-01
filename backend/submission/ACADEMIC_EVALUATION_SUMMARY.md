# SchemaSense AI — Academic Evaluation & Benchmark Summary
## Objective Empirical Analysis of Generative AI Query Generation

**Evaluation Dataset:** `backend/evaluation/evaluation_dataset.json`  
**Master Evidence Matrix:** `backend/evaluation/CLAIM_EVIDENCE_LEDGER.md`  
**Evaluation Runner:** `backend/evaluation/benchmark_eval.py`  
**Target Database:** `campus_intelligence.db` (SQLite 3, 7 tables, 135 rows, Dataset Version 1.1.0)  

---

## 1. Executive Evaluation Principles

To maintain strict academic integrity in the Generative AI (AAT-1) coursework submission, this evaluation summary adheres to the following principles:

1. **No Fabricated or Projected Numbers:** All figures presented herein derive from timestamped execution logs or passing test runs. Previously cited hypothetical percentages (e.g., 73.3%, 86.7%) and hardware estimates (e.g., 420 ms) are formally documented as unverified/projected in the Claim Evidence Ledger.
2. **Clear Distinction of Evaluation Modes:**
   - **Mode A (Deterministic Reference Baseline / Pipeline Test):** Tests system plumbing and database schema compatibility using ground-truth reference queries or deterministic mock inputs.
   - **Mode B (Genuine Qwen Model Inference):** Evaluates actual autoregressive forward passes of `Qwen2.5-Coder-1.5B-Instruct` on local hardware.
   - **Mode C (Controlled Self-Correction Experiment):** Measures the repair capability of the feedback loop when supplied with a deliberate compiler diagnostic.
3. **Multiset-Aware Result Verification:** Queries are evaluated not merely on whether they execute with status code `SUCCESS`, but whether the returned multiset of rows matches the ground-truth reference result.

---

## 2. Benchmark Dataset Structure & Denominators

The academic evaluation suite comprises **16 curated natural language queries** spanning diverse relational algebra operations:

| Query ID | Relational Complexity Category | User Question Intent | Has Reference SQL? | Purpose in Evaluation |
| :--- | :--- | :--- | :---: | :--- |
| **EVAL-01** | Simple Filtering | Students in DEP-CS | Yes | Single-table predicate filtering |
| **EVAL-02** | Sorting & Ordering | Courses ordered by credits DESC | Yes | `ORDER BY ... DESC` sorting |
| **EVAL-03** | Aggregation | Average student GPA | Yes | `AVG(gpa)` scalar aggregation |
| **EVAL-04** | Grouping (`GROUP BY`) | Student count per department | Yes | Multi-entity grouped counts |
| **EVAL-05** | Aggregation Filter (`HAVING`) | Departments with average GPA > 3.5 | Yes | Grouped aggregation filtering |
| **EVAL-06** | Single Table Projection | First name, last name, email of faculty | Yes | Projection of subset attributes |
| **EVAL-07** | Two-Table Relational Join | Student names and department names | Yes | Standard 1-to-N inner join |
| **EVAL-08** | Multi-Table Relational Join | Courses with instructor faculty names | Yes | Multi-hop foreign key traversal |
| **EVAL-09** | Scalar Subquery | Faculty earning above average salary | Yes | Nested subquery comparison |
| **EVAL-10** | Ranking & Limiting | Top 5 students by GPA | Yes | `ORDER BY ... DESC LIMIT 5` |
| **EVAL-11** | Constraint Edge Case | Students with GPA > 8.5 | Yes | Evaluates out-of-scale GPA filtering |
| **EVAL-12** | Empty Result Set | Courses with > 10 credits | Yes | Valid query returning 0 records |
| **EVAL-13** | Schema Rejection Test | Students ordered by age | **No** (`null`) | **Intentionally tests non-existent column** |
| **EVAL-14** | Semantic Duplicate Challenge | Students with enrollments (no duplicates) | Yes | Tests 1-to-N deduplication (`DISTINCT`) |
| **EVAL-15** | Aggregation across Join | Average course grade points per department | Yes | Aggregate computation across join |
| **EVAL-16** | Complex Aggregation Join | Average student grade points per department | Yes | Multi-table grouped calculation |

### Formal Metric Denominators:
- **Total Benchmark Questions ($N_{total} = 16$):** Used for calculating Syntax Validity Rate ($SVR$), Schema Compliance Rate ($SCR$), and Sandbox Execution Rate ($ESR$).
- **Objectively Evaluable Questions ($N_{eval} = 15$):** Used for calculating Exact Semantic Match ($ESM$). Question `EVAL-13` intentionally references an imaginary column (`age`) to verify that the AST validator rejects non-existent attributes; hence it has no reference SQL and cannot be evaluated for row equivalence.

---

## 3. Verified Empirical Results

### 3.1 Measured Local Model Performance (Real Qwen on CPU)
- **Model:** `Qwen2.5-Coder-1.5B-Instruct` (1.54B parameters)
- **Execution Environment:** Windows 11, Intel/AMD Multi-Core CPU, `torch.float32`
- **Measured Generation Latency:** **$51,828.67\text{ ms}$ ($\approx 51.8\text{ seconds}$)** per query
- **Measured SQLite Execution Latency:** **$0.58\text{ ms}$**
- **Evidence Log:** `backend/evaluation/results/real_qwen_correction_result.json`

### 3.2 Controlled Execution-Guided Self-Correction Outcome
To empirically test the self-correction loop under reproducible conditions, the system was supplied with a candidate query containing a typical LLM column hallucination:
- **Natural Language Question:** *"Show the top 5 students with the highest GPA."*
- **Attempt 1 Candidate SQL:** `SELECT student_name, gpa FROM students ORDER BY gpa DESC LIMIT 5;`
- **Attempt 1 AST Status:** `BLOCKED` (Column `student_name` does not exist in table `students`).
- **Initial Execution Success:** **$0.0\%$**
- **Diagnostic Feedback:** `Column 'student_name' does not exist in table 'students'. Available columns in 'students': [student_id, first_name, last_name, email, department_id, enrollment_year, gpa].`
- **Attempt 2 (Repaired SQL):**
  ```sql
  SELECT T1.first_name, T1.last_name, T1.gpa
  FROM students AS T1
  INNER JOIN enrollments AS T2 ON T1.student_id = T2.student_id
  ORDER BY T1.gpa DESC
  LIMIT 5;
  ```
- **Attempt 2 Execution Status:** `SUCCESS` (Executed in 0.58 ms, returned 5 rows).
- **Post-Correction Execution Success:** **$100.0\%$**

### 3.3 Authentic Cloud T4 GPU Execution & Benchmark Evaluation (`colab_run_20261028T154224Z`)
- **Execution Run ID:** `colab_run_20261028T154224Z`
- **Model:** `Qwen/Qwen2.5-Coder-1.5B-Instruct` (1.54B parameters)
- **Execution Environment:** Google Colab, Linux, NVIDIA Tesla T4 GPU (14.56 GB VRAM), CUDA active, `torch.float16`
- **Total Questions Evaluated:** **16** (`EVAL-01` through `EVAL-16`)
- **Pipeline Layer Verification Rates:**
  - **Syntax Validity Rate ($SVR$):** **16 / 16 (100.0%)**
  - **Schema Compliance Rate ($SCR$):** **16 / 16 (100.0%)**
  - **Sandbox Execution Rate ($ESR$):** **14 / 16 (87.5%)**
    - Failed runtime queries: `EVAL-03` (generated unrecognized token `CURRENT_YEAR`), `EVAL-13` (attempted to query intentionally non-existent column `age`).
  - **Exact Semantic Match ($ESM$):** **5 / 15 (33.33%)**
    - Evaluated over $N_{eval} = 15$ evaluable questions (`EVAL-13` excluded due to null reference SQL).
    - Matched ground truth: `EVAL-06`, `EVAL-07`, `EVAL-08`, `EVAL-11`, `EVAL-12`.
- **Latency Profile:**
  - **Mean Generation Latency:** **$1,665.98\text{ ms}$ ($\approx 1.67\text{ s}$)** per query
  - **Median Generation Latency:** **$1,747.17\text{ ms}$**
  - **Minimum Generation Latency:** **$1,029.35\text{ ms}$**
  - **Maximum Generation Latency:** **$2,058.07\text{ ms}$**
  - **Mean SQLite Execution Latency:** **$0.49\text{ ms}$**
  - **Hardware Acceleration Speedup:** **$\approx 31.1\times$ faster** on Cloud T4 GPU ($1.67\text{ s}$ in FP16) versus local CPU workstation ($51.8\text{ s}$ in FP32).
- **Controlled Self-Correction Experiment on Cloud GPU (Cell 26):**
  - **Initial Candidate SQL:** `SELECT student_name, gpa FROM students ORDER BY gpa DESC LIMIT 5;`
  - **Initial AST Status:** `BLOCKED` (Column `student_name` does not exist in table `students`).
  - **Diagnostic Feedback:** `Column 'student_name' does not exist in table 'students'. Available columns in 'students': [student_id, first_name, last_name, email, department_id, enrollment_year, gpa].`
  - **Repaired SQL (T4 GPU Output):**
    ```sql
    SELECT s.first_name, s.last_name, s.gpa
    FROM students s
    ORDER BY s.gpa DESC
    LIMIT 5;
    ```
  - **Generation Latency:** $1,368.70\text{ ms}$
  - **Execution Latency:** $0.45\text{ ms}$
  - **Repaired Execution Status:** `SUCCESS` (5 rows returned, 0 errors).
  - **Empirical Contrast:** Unlike the local CPU trial where the model introduced an unnecessary `INNER JOIN enrollments` causing row duplication, on the Cloud T4 GPU the model resolved the column error by cleanly projecting `s.first_name, s.last_name, s.gpa` from `students s`, returning 5 unique top students that exactly match the ground-truth reference multiset.
- **Evidence Archive:** `backend/submission/colab_evidence/SchemaSense_AI_Colab_Evidence_colab_run_20261028T154224Z.zip`
- **Execution Log:** `backend/submission/colab_evidence/schemasense_colab_model_results.json`

---

## 4. Key Academic Finding: The Semantic Correctness Gap

While the self-correction engine successfully achieved 100% execution recovery, analysis of the returned records revealed an important phenomenon:

```
+--------------------------------------------------------------------------------------------------+
|                            CONTROLLED EXPERIMENT RESULT COMPARISON                               |
+--------------------------------------------------------------------------------------------------+
  Model-Repaired Query Output (5 rows):          Ground-Truth Reference Output (5 rows):
  - Emma Goldberg (3.96)                         - Emma Goldberg (3.96)
  - Emma Goldberg (3.96) [DUPLICATE]             - Sofia Ramirez (3.95)
  - Sofia Ramirez (3.95)                         - Aria Patel (3.92)
  - Sofia Ramirez (3.95) [DUPLICATE]             - Ananya Deshmukh (3.90)
  - Sofia Ramirez (3.95) [DUPLICATE]             - Layla Hassan (3.89)
  
  Unique Students Returned: 2 / 5                Unique Students Returned: 5 / 5
+--------------------------------------------------------------------------------------------------+
```

### Root Cause Analysis:
1. In attempting to resolve the query, the model joined `students` with `enrollments`.
2. Because a student can have multiple enrollments, a 1-to-N join without projecting course attributes and without `DISTINCT` duplicates the parent rows.
3. The query is completely valid SQL and executes without SQLite error, but the returned answer is semantically defective.
4. **Resolution in SchemaSense AI:** The conservative semantic integrity analyzer detects this pattern (`POTENTIALLY_MULTIPLICATIVE_JOIN`) and renders an advisory banner warning the user that row counts may be inflated.

---

## 5. Verification Matrix Summary

| Verification Aspect | Methodology | Scope | Pass Rate | Status |
| :--- | :--- | :---: | :---: | :---: |
| **Backend Unit Tests** | Pytest (`backend/tests/`) | 161 tests across 10 modules | 161 / 161 (100%) | **VERIFIED** |
| **Frontend Production Build** | Vite v8.3.5 / TypeScript | 2032 modules | 0 errors | **VERIFIED** |
| **Reference SQL Validity** | SQLite sandbox execution | 15 queries | 15 / 15 (100%) | **VERIFIED** |
| **Execution Security & Controls** | SQLGlot + C-Authorizer | 33 execution tests (10 security, 8 resilience, 15 correctness) | 33 / 33 (100%) | **VERIFIED** |
| **Notebook Schema** | `nbformat` v4 audit | 38 cells (with evidence exporter) | 38 / 38 (100%) | **VERIFIED** |
| **Real Qwen CPU Execution** | Transformers inference | Real model log | 51.8s measured | **VERIFIED** |
| **Cloud T4 GPU Execution** | Google Colab cloud run (`colab_run_20261028T154224Z`) | 16 benchmark queries + controlled correction | 16/16 syntax (100%), 16/16 schema (100%), 14/16 exec (87.5%), 5/15 exact match (33.33%); 1.67s mean latency | **VERIFIED** |

---
*End of SchemaSense AI Academic Evaluation Summary*
