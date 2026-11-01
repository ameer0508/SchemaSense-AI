# SchemaSense AI — Genuine Screenshot Capture Checklist
## Student Guide for Academic Report Figure Preparation

> **ACADEMIC HONESTY & FIDELITY RULE:**  
> Never generate synthetic, fabricated, or mock screenshots. Every figure in your academic report must be captured directly from your genuine local web application, terminal output, or Google Colab cloud execution environment.

---

## 1. Master Screenshot Capture Checklist

All screenshots should be placed directly in:  
📁 **`backend/submission/figures/`**

When you place files in this folder matching the names below, running `python submission/generate_reports.py` will **automatically embed them** into both your editable Word report (`SchemaSense_AI_AAT1_Report.docx`) and PDF preview (`SchemaSense_AI_AAT1_Report_Preview.pdf`).

| Figure | Recommended Filename | Source Environment | Specific Elements Required in Snip | Status |
| :---: | :--- | :--- | :--- | :---: |
| **Figure 1** | `fig01_schema_explorer.png` | Web App (`http://localhost:5173/schemas`) | Left table list (7 tables), `students` column definitions, and live 20-row preview | [ ] To Capture |
| **Figure 2** | `fig02_test_verification.png` | PowerShell Terminal | Completed `pytest -q` run showing all passing unit/regression tests | [ ] To Capture |
| **Figure 3** | `fig03_real_generation.png` | Web App (`http://localhost:5173/`) | Input question, `Qwen2.5-Coder-1.5B-Instruct` model badge, generated SQL, and Results Table | [ ] To Capture |
| **Figure 4** | `fig04_correction_trace.png` | Web App or Colab Cell 26 | Correction Trace showing Attempt 1 failure diagnostic and Attempt 2 successful syntax repair | [ ] To Capture |
| **Figure 5** | `fig05_semantic_warning.png` | Web App (`http://localhost:5173/`) | Amber `POTENTIALLY_MULTIPLICATIVE_JOIN` advisory banner with expanded details drawer | [ ] To Capture |
| **Figure 6** | `fig06_colab_runtime.png` | Google Colab Notebook | Top bar showing **T4 GPU** connected, Cell 05 GPU detection, and Cell 15 model load logs | [ ] To Capture |
| **Figure 7** | `fig07_colab_results.png` | Colab Cell 30 & Cell 32 | Evaluation summary table and the 4-panel Matplotlib plot (`schemasense_evaluation_metrics.png`) | [ ] To Save & Embed |
| **Figure 8** | `fig08_history_insights.png` | Web App (`/history` or `/insights`) | Execution history table with latency and status, or Insights KPI overview cards | [ ] To Capture |

---

## 2. Capture Walkthrough & Snipping Guide

### Figure 1: Schema Explorer (`fig01_schema_explorer.png`)
1. Open `http://localhost:5173/schemas`.
2. Click on the `students` table in the sidebar.
3. Scroll so that the columns table, constraints (`CHECK(gpa >= 0.0 AND gpa <= 4.0)`), and the **Preview Data** tab are in view.
4. Press `Win + Shift + S` (Windows Snipping Tool), capture the window, and save as `backend/submission/figures/fig01_schema_explorer.png`.

### Figure 2: Automated Test Verification (`fig02_test_verification.png`)
> **Note on Capability Matrix vs Test Output:**  
> The web application's Capability Matrix modal verifies live feature flags and subsystem operational status, but does not display unit test counts. An authentic terminal capture of the passing Pytest regression suite provides authoritative proof of test execution.
1. In PowerShell, navigate to `backend/` and run:
   ```powershell
   pytest -q
   ```
2. Capture the terminal window showing the test execution line and summary (e.g., `139 passed in X.XXs`).
3. Save as `backend/submission/figures/fig02_test_verification.png`.

### Figure 3: NL-to-SQL Generation Workspace (`fig03_real_generation.png`)
1. In `http://localhost:5173/`, enter:  
   `"Show all students enrolled in the Computer Science department (DEP-CS)."`
2. Click **Generate & Run**.
3. Capture the screen showing the Composer, the **Qwen2.5-Coder-1.5B-Instruct** badge, the generated SQL block, and the 5-row results table.
4. Save as `backend/submission/figures/fig03_real_generation.png`.

### Figure 4: Self-Correction Trace (`fig04_correction_trace.png`)
1. In the Workspace or Colab Cell 26, view the controlled correction trace.
2. Ensure both Attempt 1 (initial error diagnostic) and Attempt 2 (repaired SQL) are visible.
3. Capture and save as `backend/submission/figures/fig04_correction_trace.png`.

### Figure 5: Semantic Quality Advisory Banner (`fig05_semantic_warning.png`)
1. In the web workspace, enter: `"Show the top 5 students with the highest GPA."`
2. When the result displays the amber **Semantic Quality Advisory** banner (`POTENTIALLY_MULTIPLICATIVE_JOIN`), click **Show Details**.
3. Capture the banner and foreign key explanation showing duplicate row detection.
4. Save as `backend/submission/figures/fig05_semantic_warning.png`.

### Figure 6: Google Colab T4 GPU Session (`fig06_colab_runtime.png`)
1. In Google Colab after running all cells (following [`COLAB_EXECUTION_PROCEDURE.md`](COLAB_EXECUTION_PROCEDURE.md)).
2. Scroll to the top showing the connected `RAM/Disk` bar with `GPU (T4)`.
3. Capture Cell 05 (`Hardware Acceleration Detected: GPU (Tesla T4)`) and Cell 15 model loading confirmation.
4. Save as `backend/submission/figures/fig06_colab_runtime.png`.

### Figure 7: Publication Visualizations (`fig07_colab_results.png`)
1. In Google Colab, download `schemasense_evaluation_metrics.png` from Cell 32 (or extract it from `SchemaSense_AI_Colab_Evidence_<run_id>.zip`).
2. Alternatively, capture Cell 30 and Cell 32 showing the rendered 4-panel chart.
3. Save as `backend/submission/figures/fig07_colab_results.png`.

### Figure 8: Query History & Analytics Insights (`fig08_history_insights.png`)
1. Navigate to `http://localhost:5173/history` or `http://localhost:5173/insights`.
2. Capture the table showing recorded queries, execution latencies, and status pills.
3. Save as `backend/submission/figures/fig08_history_insights.png`.

---

## 3. How Screenshots Are Automatically Embedded
You do **not** need to manually edit Microsoft Word or ReportLab templates to embed your screenshots:
1. Place the 8 PNG files in `backend/submission/figures/`.
2. Run:
   ```powershell
   cd "E:\SchemaSense AI\backend"
   .\.venv\Scripts\python.exe submission/generate_reports.py
   ```
3. The generator detects the images, resizes them with preserved aspect ratios, embeds them beneath their respective captions, and builds both `SchemaSense_AI_AAT1_Report.docx` and `SchemaSense_AI_AAT1_Report_Preview.pdf`.
4. If an image file is missing, the generator gracefully falls back to a clean placeholder box without crashing.

---
*End of Genuine Screenshot Capture Checklist*
