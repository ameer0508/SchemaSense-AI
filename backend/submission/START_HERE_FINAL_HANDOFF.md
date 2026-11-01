# SchemaSense AI — Student Handoff & Submission Guide
**Generative Artificial Intelligence (AAT-1 Coursework Submission)**  
**Project:** SchemaSense AI — Schema-Aware Natural Language to SQL Generation with Automatic Self-Correction  
**Target Audience:** Student 1 & Student 2 (B.Tech Computer Science & Engineering)

---

## Welcome to the Final Submission Phase

All software implementation, local AI inference, database introspection, secure read-only SQL execution, execution-guided self-correction, unit test suites, and academic documentation generation have been fully built and verified locally.

To complete your academic submission, follow this **13-step sequence**. Each step is clear, sequential, and requires no guesswork.

---

## Complete Submission Workflow (Steps 1 – 13)

```
[Local Verification] ──> [Upload to Google Colab] ──> [Run Notebook with T4 GPU]
                                                               │
                                                               ▼
[Regenerate Reports] <── [Capture 8 Screenshots] <── [Download & Import Evidence]
        │
        ▼
[Final Inspection] ──> [Submit Artifacts]
```

---

### Step 1 — Confirm Local Application State
1. Open PowerShell and start the backend:
   ```powershell
   cd "E:\SchemaSense AI\backend"
   .\.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8001
   ```
2. In a second terminal, start the frontend:
   ```powershell
   cd "E:\SchemaSense AI\frontend"
   npm run dev
   ```
3. Open `http://localhost:5173` in Google Chrome.
4. Verify that:
   - The Campus Intelligence SQLite database (7 tables) loads in the Schema Explorer.
   - The model selector displays `Qwen/Qwen2.5-Coder-1.5B-Instruct`.
   - Running tests in backend (`pytest -q`) confirms **161 passing tests**.

---

### Step 2 — Open the Authoritative Notebook in Google Colab
1. Navigate in your browser to: [Google Colab](https://colab.research.google.com).
2. Click **Upload** and select the authoritative notebook from this repository:
   ```
   E:\SchemaSense AI\backend\submission\SchemaSense_AI_GenAI_AAT1.ipynb
   ```
   *(Note: This notebook is completely self-contained. It creates the 7-table SQLite database directly in memory/disk and downloads the Qwen model from Hugging Face.)*

---

### Step 3 — Configure Colab Hardware Accelerator
1. In Google Colab, click **Runtime** in the top menu bar -> **Change runtime type**.
2. Select:
   - **Hardware accelerator:** **T4 GPU** (Standard free tier).
   - If T4 GPU is unavailable due to free-tier quotas, select **CPU** (the notebook has automatic CPU fallback with float32 inference).
3. Click **Save**.

---

### Step 4 — Execute the Notebook Sequentially
1. Click **Runtime** -> **Run all** (or step through cells from Cell 00 to Cell 37).
2. Reference [`NOTEBOOK_CELL_MAP.md`](file:///e:/SchemaSense%20AI/backend/submission/NOTEBOOK_CELL_MAP.md) for detailed descriptions of each cell's purpose and expected output.
3. Observe key execution checkpoints:
   - **Cell 05 (Step 2):** Detects hardware accelerator (confirms NVIDIA T4 or CPU fallback).
   - **Cell 08 (Step 3):** Populates synthetic 7-table Campus Intelligence database (135 relational records).
   - **Cell 15 (Step 6):** Loads `Qwen/Qwen2.5-Coder-1.5B-Instruct` (~3.1 GB downloaded, 4-bit/float16 in VRAM).
   - **Cell 16 (Step 7):** Executes initial smoke test query generation.
   - **Cell 26 (Step 12):** Executes controlled self-correction demonstration (recovering syntax error, followed by semantic duplicate detection).
   - **Cell 30 (Step 15):** Runs 16-question academic evaluation benchmark.
   - **Cell 32 (Step 16):** Generates and displays 4-panel publication visualization.

---

### Step 5 — Verify Genuine Model Inference
1. Confirm that Cell 15 output displays actual Hugging Face download progress bars or cache hits:
   `Loading checkpoint shards: 100%`
2. Confirm that Cell 30 displays live inference logs:
   `[Eval 1/16] Q01: What are the names and GPAs of all students majoring in Computer Science?`
   `Generated in 1.42s (V: PASS, E: PASS)`
3. Ensure that inference was **genuine autoregressive token generation** from Qwen2.5-Coder-1.5B-Instruct, not a hardcoded stub.

---

### Step 6 — Generate Academic Evidence Archive (Cell 37)
1. At the bottom of the notebook, navigate to **Section 19: Export Measured Evaluation Evidence** (Cell 37).
2. Execute Cell 37. It automatically collects in-memory benchmark metrics and exports:
   - `schemasense_colab_run_manifest.json` (hardware metadata, versions, timestamps, run ID)
   - `schemasense_colab_model_results.json` (per-question generated SQL, execution outcomes, latencies)
   - `schemasense_colab_evaluation_metrics.json` (strict recomputed accuracy rates and latency figures)
   - `schemasense_evaluation_metrics.png` (high-resolution 300 DPI 4-panel chart)
   - Bundles everything into: `SchemaSense_AI_Colab_Evidence_<run_id>.zip`

---

### Step 7 — Download Executed Notebook and Evidence Archive
### Step 7 — Download Executed Notebook and Evidence Archive
1. In Google Colab's left sidebar, click the **Files** folder icon.
2. Locate the generated archive:
   `SchemaSense_AI_Colab_Evidence_<run_id>.zip`
3. Right-click and choose **Download**.
4. In the Colab menu, click **File** -> **Download** -> **Download .ipynb** (contains all executed outputs, logs, and plots).
5. Place the downloaded files into your local workspace directory:
   - Place the downloaded ZIP into:
     ```
     E:\SchemaSense AI\backend\submission\colab_evidence\
     ```
   - Save the executed notebook separately as:
     ```
     E:\SchemaSense AI\backend\submission\colab_evidence\SchemaSense_AI_GenAI_AAT1_EXECUTED.ipynb
     ```
   > [!IMPORTANT]
   > **Do NOT overwrite the source notebook `backend/submission/SchemaSense_AI_GenAI_AAT1.ipynb`.**  
   > The source notebook must remain immutable so that its SHA-256 hash matches the authoritative repository source (`backend/notebooks/SchemaSense_AI_GenAI_AAT1.ipynb`). The executed notebook is preserved separately inside `colab_evidence/`.

---

### Step 8 — Import and Validate Colab Evidence Locally
1. In your local terminal, run the automated verification tool:
   ```powershell
   cd "E:\SchemaSense AI\backend"
   .\.venv\Scripts\python.exe submission/import_colab_evidence.py submission/colab_evidence/SchemaSense_AI_Colab_Evidence_<run_id>.zip
   ```
2. The importer will:
   - Verify archive safety against Zip Slip and decompression bombs.
   - Validate JSON structures, numeric sanity, and model identity (`Qwen/Qwen2.5-Coder-1.5B-Instruct`).
   - Recompute all academic metrics using exact mathematical denominators (16 total questions, 15 evaluable questions).
   - Generate: `backend/submission/colab_evidence/EVIDENCE_VERIFICATION_SUMMARY.md`.
3. Review the generated report to confirm **Status: VERIFIED_CONSISTENT**.

---

### Step 9 — Capture Authentic Application Screenshots
Capture 8 authentic screenshots from your running systems and save them in:
`E:\SchemaSense AI\backend\submission\figures\`

Use these exact filenames:

| Filename | Source / Screen | What to Show |
|---|---|---|
| `fig01_schema_explorer.png` | Web UI (`http://localhost:5173`) | Campus Intelligence schema tree showing all 7 tables, columns, and foreign keys |
| `fig02_test_verification.png` | Terminal (PowerShell) | Completed `pytest -q` run showing all passing unit/regression tests |
| `fig03_real_generation.png` | Web UI Workspace | Question input, Qwen model badge, generated SQL with syntax highlighting |
| `fig04_correction_trace.png` | Web UI / History | Step-by-step self-correction card showing original error and repaired SQL |
| `fig05_semantic_warning.png` | Web UI Workspace | Amber advisory alert (`POTENTIALLY_MULTIPLICATIVE_JOIN` duplicate row warning) |
| `fig06_colab_runtime.png` | Google Colab Browser | Cell 05 & Cell 15 output showing NVIDIA T4 GPU and loaded checkpoint |
| `fig07_colab_results.png` | Google Colab Browser | Cell 30 summary table and Cell 32 4-panel evaluation chart |
| `fig08_history_insights.png` | Web UI Insights Tab | Execution latency chart, success rate donut, and query history table |

*(Refer to [`SCREENSHOT_CHECKLIST.md`](file:///e:/SchemaSense%20AI/backend/submission/SCREENSHOT_CHECKLIST.md) for framing and resolution guidelines).*

---

### Step 10 — Personalize Student Credentials
1. Open [`backend/submission/ACADEMIC_REPORT_DRAFT.md`](file:///e:/SchemaSense%20AI/backend/submission/ACADEMIC_REPORT_DRAFT.md).
2. Locate the metadata header and Section 22 (Student Declaration).
3. Replace the placeholder brackets with your real information:
   - `[Student 1 Name]` -> e.g., `Aarav Sharma`
   - `[Student 1 University Roll / Registration Number]` -> e.g., `1RV21CS001`
   - `[Student 2 Name]` -> e.g., `Priya Patel`
   - `[Student 2 University Roll / Registration Number]` -> e.g., `1RV21CS042`
   - `[Course / Semester / Academic Year]` -> e.g., `B.Tech CSE, 7th Semester, 2026`
   - `[Faculty Guide / Evaluator Name]` -> e.g., `Dr. S. R. Rao`
4. Review Section 22's two-person contribution breakdown to reflect your respective responsibilities.

---

### Step 11 — Regenerate DOCX and PDF Academic Reports
1. Run the report generation script:
   ```powershell
   cd "E:\SchemaSense AI\backend"
   .\.venv\Scripts\python.exe submission/generate_reports.py
   ```
2. The script will:
   - Parse `ACADEMIC_REPORT_DRAFT.md`.
   - Embed the authentic screenshots from `backend/submission/figures/`.
   - Compile `SchemaSense_AI_AAT1_Report.docx` (editable Word document with IEEE formatting).
   - Compile `SchemaSense_AI_AAT1_Report_Preview.pdf` (preview PDF with page budget verification >= 10 pages).
3. Confirm output message: `Verified Rendered Page Count: 17 pages -> PASSED`.

---

### Step 12 — Final Quality & Deliverable Inspection
Perform this 5-point inspection before submitting:
- [ ] **Document Completeness:** Open `SchemaSense_AI_AAT1_Report.docx` in Microsoft Word or LibreOffice. Confirm your names, roll numbers, and images appear without overflow.
- [ ] **Notebook Execution Evidence:** Open `backend/submission/colab_evidence/SchemaSense_AI_GenAI_AAT1_EXECUTED.ipynb` and verify all 38 cells display authentic execution outputs, timestamps, and charts.
- [ ] **Immutable Source Notebook:** Verify `backend/submission/SchemaSense_AI_GenAI_AAT1.ipynb` has remained untouched and identical to the template in `backend/notebooks/`.
- [ ] **Evidence Archive & Summary:** Verify `backend/submission/colab_evidence/` contains the downloaded ZIP and `EVIDENCE_VERIFICATION_SUMMARY.md`.
- [ ] **Workspace Cleanliness:** Verify the repository root contains strictly `backend/` and `frontend/`.

---

### Step 13 — Submit Deliverables
Submit the required files to your course portal or evaluation panel as instructed by faculty:
1. **Academic Project Report:** `SchemaSense_AI_AAT1_Report.docx` and `SchemaSense_AI_AAT1_Report_Preview.pdf`
2. **Executed Google Colab Notebook:** `colab_evidence/SchemaSense_AI_GenAI_AAT1_EXECUTED.ipynb`
3. **Immutable Source Template:** `SchemaSense_AI_GenAI_AAT1.ipynb`
4. **Colab Evidence Archive:** `colab_evidence/SchemaSense_AI_Colab_Evidence_<run_id>.zip`
5. **Source Code Repository:** Complete project folder (`frontend/` + `backend/`)

---

## Technical Support & Reference Map
- **Notebook Cell Index Map:** [`NOTEBOOK_CELL_MAP.md`](file:///e:/SchemaSense%20AI/backend/submission/NOTEBOOK_CELL_MAP.md)
- **Colab Runbook:** [`COLAB_EXECUTION_PROCEDURE.md`](file:///e:/SchemaSense%20AI/backend/submission/COLAB_EXECUTION_PROCEDURE.md)
- **Screenshot Guidelines:** [`SCREENSHOT_CHECKLIST.md`](file:///e:/SchemaSense%20AI/backend/submission/SCREENSHOT_CHECKLIST.md)
- **Submission Manifest:** [`README_SUBMISSION_MANIFEST.md`](file:///e:/SchemaSense%20AI/backend/submission/README_SUBMISSION_MANIFEST.md)
- **Evidence Ledger:** [`CLAIM_EVIDENCE_LEDGER.md`](file:///e:/SchemaSense%20AI/backend/submission/CLAIM_EVIDENCE_LEDGER.md)
