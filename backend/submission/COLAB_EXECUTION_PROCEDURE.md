# SchemaSense AI — Google Colab Cloud Execution & Evidence Capture Procedure
## Student Execution Guide for Generative AI AAT-1 Assignment

**Target Notebook:** `backend/submission/SchemaSense_AI_GenAI_AAT1.ipynb`  
**Authoritative Cell Index Reference:** [`NOTEBOOK_CELL_MAP.md`](NOTEBOOK_CELL_MAP.md)  
**Target Platform:** [Google Colab](https://colab.research.google.com/) (Free Tier)  
**Recommended Compute Accelerator:** NVIDIA Tesla T4 GPU (or CPU Fallback)

---

## 1. Why Google Colab Execution is Required

While the entire SchemaSense AI codebase, backend tests, and notebook files have been programmatically validated in the local workspace:
1. **Academic Honesty:** An unexecuted `.ipynb` notebook file contains code and cell structure, but lacks **genuine execution outputs, execution counts, timestamps, and rendered Matplotlib figures**.
2. **GPU Hardware Verification:** Local execution on CPU takes $\approx 51.8\text{ seconds}$ per query. Running on Google Colab with an allocated GPU validates high-throughput FP16 tensor inference (measuring actual GPU forward-pass latency under cloud conditions), providing empirical evidence for evaluators.
3. **Reproducibility Requirement:** Your faculty evaluators expect an exported notebook containing visible cell outputs, terminal logs, and high-resolution plots.

---

## 2. Step-by-Step Google Colab Execution Walkthrough

### Step 1: Open Google Colab and Upload Notebook
1. Open your web browser and navigate to:  
   👉 **`https://colab.research.google.com/`**
2. In the modal dialog that appears, click the **Upload** tab.
3. Click **Browse** and navigate to your workspace:  
   `E:\SchemaSense AI\backend\submission\SchemaSense_AI_GenAI_AAT1.ipynb`
4. The notebook will upload and open in the Colab interactive environment (total 38 cells: alternating markdown documentation and Python code cells).

---

### Step 2: Configure Free T4 GPU Hardware Accelerator
1. In the top menu bar, click:  
   **Runtime** $\to$ **Change runtime type**
2. In the *Hardware accelerator* dropdown, select:  
   **T4 GPU** *(Note: Google Colab free-tier GPU assignment is subject to dynamic cloud capacity; if GPU is temporarily unavailable, standard CPU execution will still complete all cells).*
3. Ensure *Python 3* is selected as the runtime language.
4. Click **Save**.
5. In the top right corner, click **Connect**.
6. Verify connection: After connecting, hover over the RAM/Disk meters in the top right. You should see `Connected to Python 3 Google Compute Engine backend (GPU)`.

---

### Step 3: Execute the Notebook Sequentially
1. In the menu bar, click:  
   **Runtime** $\to$ **Run all** (or press keyboard shortcut `Ctrl + F9`).
2. Monitor execution cell by cell using the exact cell indices from [`NOTEBOOK_CELL_MAP.md`](NOTEBOOK_CELL_MAP.md):
   - **Cell 02 & Cell 05 (Environment & Accelerator Check):** Installs dependencies and checks accelerator. Cell 05 prints detected hardware (`Tesla T4`, CUDA active, bfloat16/float16).
   - **Cell 08 (Synthetic Database Creation):** Generates `campus_intelligence.db` with 7 tables and 135 total relational records (Dataset Version 1.1.0). Prints record summary table.
   - **Cell 11 (Schema Introspection):** Runs PRAGMA catalog queries and builds the ChatML schema prompt context.
   - **Cell 15 (Model Loading):** Downloads `Qwen/Qwen2.5-Coder-1.5B-Instruct` directly from Hugging Face Hub ($\approx 3.1\text{ GB}$).  
     *Timing note:* First download takes $\approx 60 - 90\text{ seconds}$. Subsequent execution runs quickly from cache.
   - **Cell 16 (Sanity Generation):** Runs single test generation. Record the measured inference latency printed by the cell timer.
   - **Cell 20 & Cell 22 (AST & Sandbox):** Tests SQLGlot validation guardrails and read-only authorizer.
   - **Cell 26 (Controlled Self-Correction & Multiplicative Join):** Demonstrates `student_name` syntax error recovery to executable SQL, followed by semantic duplicate row detection.
   - **Cell 30 (Benchmark Evaluation Suite):** Evaluates all 16 benchmark questions and prints live progress logs and evaluation summary table.
   - **Cell 32 (Matplotlib Visualizations):** Renders the 4 publication-quality evaluation charts and saves `schemasense_evaluation_metrics.png`.
   - **Cell 37 (Export Measured Evaluation Evidence):** Serializes actual in-memory metrics, per-question records, and bundles them into `SchemaSense_AI_Colab_Evidence_<run_id>.zip`.

---

### Step 4: Download Executed Artifacts & Evidence
Once all cells have completed execution (every cell shows a green checkmark or number):

1. **Download the Evidence Archive:**  
   Click the **Files** folder icon on the left sidebar in Colab.  
   Locate `SchemaSense_AI_Colab_Evidence_<run_id>.zip`.  
   Right-click $\to$ **Download**.  
   Save this archive into your local directory:  
   `backend/submission/colab_evidence/`
2. **Download the Executed Notebook:**  
   Click **File** $\to$ **Download** $\to$ **Download .ipynb**  
   Save this file separately as:  
   `backend/submission/colab_evidence/SchemaSense_AI_GenAI_AAT1_EXECUTED.ipynb`  
   *(Do NOT overwrite the source notebook `backend/submission/SchemaSense_AI_GenAI_AAT1.ipynb`; the source must remain immutable and SHA-256 identical to the repository template).*
3. **Download the Visualization Figure (Optional, included in ZIP):**  
   Download `schemasense_evaluation_metrics.png` if you wish to inspect it directly.
4. **Import Evidence Locally:**  
   Run the local verification tool to validate evidence integrity:  
   ```powershell
   cd "E:\SchemaSense AI\backend"
   .\.venv\Scripts\python.exe submission/import_colab_evidence.py submission/colab_evidence/SchemaSense_AI_Colab_Evidence_<run_id>.zip
   ```

---

## 3. Required Screenshot Evidence Checklist

While the notebook is open in Colab, capture the following high-resolution screenshots for your report (using Windows Snipping Tool `Win + Shift + S`):

| Screenshot ID | Filename for `figures/` | What to Capture in Colab | Report Location |
| :--- | :--- | :--- | :--- |
| **COLAB-01** | `fig06_colab_runtime.png` | Top of notebook showing connected **T4 GPU** badge and Cell 05 output: `Hardware Acceleration Detected: GPU (Tesla T4)`. | Figure 6 in Report |
| **COLAB-02** | *Model verification* | Cell 15 showing model load confirmation: `Model loaded successfully in X.XX seconds. Total Parameters: 1.54 Billion | Target Device: cuda`. | Appendix / Model Section |
| **COLAB-03** | `fig04_correction_trace.png` | Cell 26 showing controlled correction trace: `Invalid SQL` $\to$ `Repaired SQL` $\to$ `POTENTIALLY_MULTIPLICATIVE_JOIN warning`. | Figure 4 in Report |
| **COLAB-04** | `fig07_colab_results.png` | Cell 30 evaluation summary table and Cell 32 rendered 4-panel publication visualization plot. | Figure 7 in Report |

---

## 4. Troubleshooting Common Google Colab Issues

| Problem | Cause | Exact Solution |
| :--- | :--- | :--- |
| **Cell 05 says "Hardware Acceleration: CPU"** | Runtime type was not changed to GPU | Go to **Runtime $\to$ Change runtime type $\to$ Select T4 GPU**, then click Save and re-run cells 02 and 05. |
| **GPU quota exceeded / Cannot allocate T4** | Free Google account reached daily GPU limit | Switch Google account, or run in standard CPU mode (will take longer, but completes cleanly). |
| **Model download hangs or fails** | Transient network drop to Hugging Face | Re-run Cell 15. Hugging Face downloads resume from cached chunks. |
| **Session disconnected after idle time** | Colab timeouts after 30 minutes of inactivity | Re-run using **Runtime $\to$ Run all**. Cell execution takes only 3-5 minutes total on T4 GPU. |

---
*End of Google Colab Execution Procedure*
