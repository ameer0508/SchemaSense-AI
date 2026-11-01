# SchemaSense AI — Academic Submission Manifest & Verification Package
## Course: Generative AI (AAT-1) — 7th Semester B.Tech Computer Science & Engineering
**Project Title:** SchemaSense AI: Schema-Aware Natural Language to SQL Query Generation with Automatic Self-Correction Using Generative AI  
**Workspace:** `E:\SchemaSense AI`  
**Package Location:** `backend/submission/`  
**Generated At:** 2026-10-28  

---

## 1. Submission Package Overview

This package contains the complete academic deliverables, verified implementation scripts, benchmark ledgers, demonstration protocols, and student execution procedures for **SchemaSense AI**.

| Artifact Filename | Description | Completeness Status | Action Required by Students |
| :--- | :--- | :---: | :--- |
| **`START_HERE_FINAL_HANDOFF.md`** | Definitive 13-step student handoff and submission guide | **Complete** | **Start here and follow Steps 1 to 13** |
| **`NOTEBOOK_CELL_MAP.md`** | Comprehensive mapping of all 38 cells (indices, types, purposes, outputs) | **Complete** | Reference during Colab execution |
| **`COLAB_EXECUTION_PROCEDURE.md`** | Step-by-step instructions for running the notebook on Google Colab T4 GPU | **Complete** | Reference for reproduction on Google Colab |
| **`SchemaSense_AI_GenAI_AAT1.ipynb`** | Standalone, self-contained Google Colab notebook (38 cells with evidence exporter) | **Complete (Canonical Source)** | Retain immutable submission template |
| **`import_colab_evidence.py`** | Local automated verification and metric recomputation script | **Complete** | Validates Colab evidence ZIP archives |
| **`generate_reports.py`** | Automated DOCX and PDF academic report generator with image embedding | **Complete** | Compiles report with embedded figures |
| **`ACADEMIC_REPORT_DRAFT.md`** | Comprehensive 22-section academic report source document | **Complete (Verified Evidence)** | Fill student details & insert UI screenshots |
| **`SchemaSense_AI_AAT1_Report.docx`** | Publication-grade Microsoft Word report deliverable | **Generated (~501 KB)** | Fill student placeholders & save final |
| **`SchemaSense_AI_AAT1_Report_Preview.pdf`** | Formatted PDF academic preview (17 verified pages) | **Rendered (~666 KB)** | Review layout and page requirement |
| **`ACADEMIC_EVALUATION_SUMMARY.md`** | Measured evaluation summary based on verified T4 GPU evidence | **Complete** | Reference during viva presentation |
| **`CLAIM_EVIDENCE_LEDGER.md`** | Master evidence matrix mapping claims to empirical logs | **Complete** | Evidence reference |
| **`DEMO_INSTRUCTIONS.md`** | Classroom demonstration runbook with Zero-Mock rule | **Complete** | Follow during live presentation |
| **`SCREENSHOT_CHECKLIST.md`** | Detailed checklist mapping required figures to UI views | **Complete** | Capture and place remaining UI screenshots |
| **`colab_evidence/`** | Verified Colab evidence archive & executed notebook | **VERIFIED (`colab_run_20261028T154224Z`)** | Retain original artifacts untouched |
| **`figures/`** | Publication figure directory with authentic Colab evaluation charts | **fig07 embedded (524 KB)** | Place remaining UI screenshots here |

---

## 2. Status of Academic Deliverables

### A. Google Colab Notebooks (Source Template vs Executed Deliverable)
- **Immutable Source Template (`SchemaSense_AI_GenAI_AAT1.ipynb`):**
  - **Structure:** 38 sequential cells (21 Markdown cells, 17 executable Python code cells).
  - **Validation:** 100% compliant with `nbformat` v4; validated via automated Pytest tests.
  - **Defect Fixes Applied:** Step 11 question formatting repaired; Step 16 nullable Exact Match boolean handling and mutually exclusive failure categories resolved; Step 17 read-only SQLite fingerprinting and robust evidence export validated.
  - **Portability:** Strictly zero Windows path dependencies (`E:\`, `C:\`, backslashes). Self-contained synthetic database generation and dynamic PRAGMA introspection.
  - **Integrity Rule:** Canonical source synchronized between `backend/notebooks/` and `backend/submission/` (SHA-256 identical).
- **Executed Notebook Deliverable (`colab_evidence/SchemaSense_AI_GenAI_AAT1_EXECUTED.ipynb`):**
  - Downloaded after running all 38 cells in Google Colab on an NVIDIA Tesla T4 GPU.
  - Preserved separately with visible cell execution counts, generation logs, and rendered Matplotlib plots (SHA-256: `EC6FCD6415DA9ED3CF781B0843A8150E29669BA46EF0DF0102C231AD362A148F`).

### B. Academic Report Draft (`ACADEMIC_REPORT_DRAFT.md`)
- **Structure:** 22 formal academic sections spanning abstract, problem definition, transformer mathematical formulations (RoPE, causal attention, SwiGLU), dynamic schema grounding, AST validation, execution-guided self-correction, empirical evaluation, and references.
- **Integrity:** Strictly measured figures only: 16/16 syntax (100%), 16/16 schema (100%), 14/16 execution (87.5%), 5/15 exact match (33.33%), and 1,665.98 ms mean generation latency on T4 GPU.
- **Placeholders:** Contains clearly labeled placeholders for student names, roll numbers, faculty supervisor, and pending UI application screenshots.

### C. Live Demonstration Policy (Zero-Mock Requirement)
- **Requirement:** The primary demonstration to course evaluators MUST use genuine generative AI inference (`Qwen2.5-Coder-1.5B-Instruct`), either on local CPU or via Google Colab on T4 GPU.
- **Policy:** The mock AI provider (`AI_PROVIDER=mock`) is strictly for headless unit testing (`pytest`) and CI pipelines. It must NEVER be presented to evaluators as actual generative AI.

---

## 3. Directory Cleanliness & Hygiene Verification
The workspace strictly satisfies the project architectural constraints:
1. Exactly two root directories: `backend/` and `frontend/`.
2. No temporary caches, virtual environments (`.venv`), or dependencies (`node_modules`) bundled in this submission package.
3. No destructive alterations made to existing history or user databases.
4. Total test suite status: **161 passing backend unit tests** across 10 test modules; frontend builds with 0 errors.

---
*End of SchemaSense AI Academic Submission Manifest*
