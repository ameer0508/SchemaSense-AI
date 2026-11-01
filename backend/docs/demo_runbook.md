# SchemaSense AI — Demonstration Runbook & Reproduction Guide
## Course: Generative AI (AAT-1) — 7th Semester B.Tech Computer Science & Engineering
**Tagline:** Natural Language. Precise SQL.  
**Demonstration Scope:** Web Application (FastAPI + React) & Independent Google Colab Notebook  

---

## 1. System Requirements & Prerequisites

### 1.1 Hardware Specifications
- **Operating System:** Windows 10/11, macOS (Apple Silicon or Intel), or Linux (Ubuntu 22.04+).
- **RAM:** Minimum 8 GB (16 GB recommended for local CPU transformer inference).
- **Storage:** 5 GB free disk space (to cache `Qwen2.5-Coder-1.5B-Instruct` model weights locally).
- **GPU (Optional for Local Web App, Recommended for Colab):** NVIDIA GPU with $\ge 4\text{ GB VRAM}$ or free Google Colab T4 GPU instance.

### 1.2 Software Prerequisites
- **Python:** Version `3.10` or `3.11` (verify via `python --version`).
- **Node.js:** Version `18.x` or `20.x` LTS (verify via `node --version`).
- **Package Managers:** `npm` or `pnpm` and `pip`.

---

## 2. Environment Setup (Fresh Machine Reproduction)

### Step 2.1: Clone and Inspect Directory Structure
Ensure you are in the workspace root. The root directory contains strictly two folders:
```
E:\SchemaSense AI
├── backend/
└── frontend/
```

### Step 2.2: Backend Python Setup
In Windows PowerShell:
```powershell
# Navigate to backend
cd backend

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install nbformat pandas matplotlib tabulate
```

### Step 2.3: Frontend Node.js Setup
In a separate terminal:
```powershell
# Navigate to frontend
cd frontend

# Install Node dependencies
npm install

# Verify production build
npm run build
```

---

## 3. Starting the Application

### 3.1 Start the FastAPI Backend (Port 8001)
From the `backend/` directory with `.venv` active:
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```
**Verification:** Open `http://127.0.0.1:8001/api/health` in your browser. You should receive:
```json
{"status": "healthy", "service": "SchemaSense AI API", "version": "0.1.0", "environment": "development"}
```

### 3.2 Start the React Frontend (Port 5173)
From the `frontend/` directory:
```powershell
npm run dev -- --host 127.0.0.1 --port 5173
```
**Verification:** Open `http://127.0.0.1:5173/` in your browser.

---

## 4. End-to-End Live Demonstration Workflow

### Stage 1: Health & Active Database Verification
1. Open the web interface at `http://127.0.0.1:5173`.
2. Observe the top navigation header:
   - Verify the **Academic Suite** badge is displayed.
   - Check the **Backend Connected** green pill showing API ping latency ($<25\text{ ms}$).
   - Click the connection badge to open the **System Capability Matrix** modal (verifying Phase 8 active capabilities).
3. Confirm that **Campus Intelligence** is selected as the active database in the database switcher.

### Stage 2: Schema Explorer Demonstration
1. Click **Schema Explorer** in the sidebar navigation (`/schemas`).
2. Demonstrate database catalog introspection:
   - Browse the 7 relational tables: `departments`, `faculty`, `students`, `courses`, `enrollments`, `attendance`, `assessments`.
   - Click the `students` table: observe columns, primary key indicator (`student_id`), and constraints (`CHECK(gpa >= 0.0 AND gpa <= 4.0)`).
   - View foreign key relationships: note `students.department_id -> departments.department_id` and `enrollments.student_id -> students.student_id`.
   - Click **Preview Data** to inspect 20 live records rendered from SQLite.

### Stage 3: Natural Language to SQL Generation
1. Navigate back to **Workspace** (`/`).
2. Verify model status in the right pane:
   - Model: `Qwen2.5-Coder-1.5B-Instruct`.
   - Device: `CPU` (or `CUDA` if GPU is configured).
   - Model: `Qwen2.5-Coder-1.5B-Instruct`.
   - Device: `CPU` (or `CUDA` if GPU is configured).
   - Provider: `local` (real transformer inference).
   *Academic Rule:* The final academic evaluation must always use real Qwen inference. The mock provider (`AI_PROVIDER=mock`) is strictly for automated unit tests and CI; it must NEVER be presented to evaluators as actual AI.
3. Try standard queries using the quick sample suggestion chips or typing:
   - **Query A (Simple Filter):**  
     `"Show all students enrolled in the Computer Science department (DEP-CS)."`  
     *Action:* Click **Generate & Run**.  
     *Observe:* Model generates `SELECT * FROM students WHERE department_id = 'DEP-CS';`, AST validator marks it **AST Valid & Grounded**, query executes in $<2\text{ ms}$ returning 5 student rows.
   - **Query B (Aggregation with HAVING):**  
     `"Show departments that have an average student GPA greater than 3.5."`  
     *Action:* Click **Generate & Run**.  
     *Observe:* Query uses `GROUP BY department_id HAVING AVG(gpa) > 3.5`, returns 4 rows (`DEP-CS`, `DEP-DS`, `DEP-MATH`, `DEP-PHYS`).
   - **Query C (Multi-Table Relational Join):**  
     `"Show student names along with their department names and building locations."`  
     *Action:* Click **Generate & Run**.  
     *Observe:* Generates inner join between `students` and `departments`, projects requested columns, returns 25 rows.

### Stage 4: Critical Semantic Quality Demonstration (Research Finding)
1. In the composer, enter:  
   `"Show the top 5 students with the highest GPA."`
2. Click **Generate & Run**.
3. **If the model repairs or introduces an unnecessary join to `enrollments`:**  
   Observe the **Semantic Quality Advisory Banner** in the Results Table:  
   > **Semantic Quality Advisory:** *SQL executed successfully, but results may not answer the question correctly.*  
   > Code: `POTENTIALLY_MULTIPLICATIVE_JOIN`  
   > *Explanation:* The query joined child table `enrollments` without projecting course attributes and without `DISTINCT`, multiplying student rows.
4. **Contrast:** Click **Show Details** to reveal the foreign key multiplicity evidence (`enrollments.student_id -> students.student_id`). Explain to evaluators that this proves execution validity does not equal semantic answer correctness!

### Stage 5: Execution-Guided Self-Correction Demonstration
1. Enter an intentionally mis-scoped question or query requiring schema repair.
2. Observe the **Correction Trace** tab in the Workspace:
   - Attempt 1: Failed query + compiler diagnostic.
   - Attempt 2: Repaired query + green success badge.
   - View the **Before / After SQL Diff Viewer** showing the exact syntax changes made by the model.

### Stage 6: Export, Query History & Analytics
1. In the Results Table, click **Export CSV**. Inspect the downloaded `.csv` file.
2. Navigate to **Query History** (`/history`):
   - View persistent logs of all executed queries with latency, status, and row counts.
   - Use the search bar to filter by keyword.
   - Click **Reuse Query** to load it back into the Workspace without auto-executing.
3. Navigate to **Insights** (`/insights`):
   - Inspect query volume, average execution duration, syntax validity rates, and failure taxonomy distributions computed from actual history records.

---

## 5. Google Colab Notebook Demonstration

### 5.1 Upload to Google Colab
1. Open [Google Colab](https://colab.research.google.com/).
2. Click **Upload** and select `backend/notebooks/SchemaSense_AI_GenAI_AAT1.ipynb`.
3. Select **Runtime > Change runtime type** and choose **T4 GPU** (or standard CPU if GPU quota is exhausted).

### 5.2 Execute Top-to-Bottom
1. Click **Runtime > Run all** (`Ctrl+F9`).
2. Observe sequential cell execution:
   - Cell 1-2: Dependency installation and GPU detection (`Hardware Acceleration Detected: GPU (Tesla T4)`).
   - Cell 3: Synthetic `campus_intelligence.db` generation and record counts summary table.
   - Cell 4-5: Dynamic schema introspection and ChatML prompt serialization.
   - Cell 6-7: Loading `Qwen2.5-Coder-1.5B-Instruct` into GPU VRAM in `torch.float16`.
   - Cell 8-11: Running text-to-SQL inference, SQLGlot AST validation, and read-only authorizer sandbox.
   - Cell 12-13: Controlled correction experiment demonstrating the semantic duplicate join phenomenon.
   - Cell 14-15: Evaluation benchmark runner across academic test cases.
   - Cell 16: Publication-quality Matplotlib figures generated and saved as `schemasense_evaluation_metrics.png`.

---

## 6. Troubleshooting Common Issues

| Symptom | Cause | Solution |
| :--- | :--- | :--- |
| **Backend connection badge shows "Disconnected"** | FastAPI server is not running on port 8001 | Run `python -m uvicorn app.main:app --port 8001` in `backend/` |
| **Model inference takes ~50s on local computer** | Running genuine 1.5B transformer autoregressively on CPU | Expected for local CPU execution. Do NOT switch to mock mode for evaluation. Recommend demonstrating via Google Colab with free T4 GPU (~500ms latency), or review the verified timestamped execution log in `real_qwen_correction_result.json`. |
| **CORS error in browser console** | Accessing from an unregistered origin | Access via `http://localhost:5173` or `http://127.0.0.1:5173` which are whitelisted in `config.py`. |
| **Colab out of memory (OOM)** | Loading weights in full float32 on GPU | Ensure `torch_dtype=torch.float16` is used on CUDA (handled automatically in notebook). |
