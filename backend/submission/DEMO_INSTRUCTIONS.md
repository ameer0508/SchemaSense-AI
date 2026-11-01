# SchemaSense AI — Demonstration Instructions for Evaluators & Students
## Academic Assessment Task 1 (AAT-1) Live Presentation Runbook

**Course:** Generative Artificial Intelligence (7th Semester B.Tech CSE)  
**System Ports:** Backend: `8001` | Frontend: `5173`  
**Primary Model:** `Qwen/Qwen2.5-Coder-1.5B-Instruct`  

---

## 1. Non-Negotiable Demonstration Policy: ZERO MOCK AI

> **CRITICAL EVALUATION POLICY:**  
> Academic evaluations must ALWAYS demonstrate **genuine Generative AI inference** using `Qwen2.5-Coder-1.5B-Instruct`.  
> The mock provider (`AI_PROVIDER=mock`) is strictly reserved for automated headless unit tests (`pytest`) and CI/CD pipelines.  
> **Under no circumstances should mock AI be presented to faculty evaluators as actual generative intelligence.**

### How to Handle Local Hardware Constraints:
- **If demonstrating on a local machine with GPU:** Set `AI_PROVIDER=local` and `AI_DEVICE=cuda` for GPU-accelerated tensor operations.
- **If demonstrating on a local machine without GPU (CPU only):**  
  Explain to the evaluator that the genuine 1.5B parameter transformer runs autoregressively on CPU with a measured latency of $\approx 51.8\text{ seconds}$. While waiting, explain the forward-pass and token decoding process.
- **Recommended Presentation Alternative (Fastest & Most Impressive):**  
  Open and execute the standalone notebook `SchemaSense_AI_GenAI_AAT1.ipynb` live in **Google Colab with GPU hardware acceleration**, providing real-time token generation during the viva presentation!

---

## 2. Quick-Start Commands

### Terminal 1: Backend Server (Port 8001)
```powershell
cd "E:\SchemaSense AI\backend"
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```
*Health Check:* Open `http://127.0.0.1:8001/api/health` in your browser. Verify `{"status": "healthy"}`.

### Terminal 2: Frontend Web Application (Port 5173)
```powershell
cd "E:\SchemaSense AI\frontend"
npm run dev -- --host 127.0.0.1 --port 5173
```
*Web App:* Open `http://127.0.0.1:5173` in your browser.

---

## 3. Recommended 6-Stage Classroom Demonstration

### Stage 1: System Capability Matrix & Database Overview
1. Open `http://127.0.0.1:5173`.
2. Point out the top header:
   - Green **Backend Connected** indicator showing live ping latency.
   - Click the indicator to show the **System Capability Matrix** (active subsystem flags, SQLGlot AST validation, read-only authorizer).
   - Point out that all 156 backend unit and regression tests pass across 10 modules.
   - Show that **Campus Intelligence** is active.

### Stage 2: Schema Explorer & Relational Introspection
1. Click **Schema Explorer** in the left sidebar (`/schemas`).
2. Show that tables are not hardcoded—they are dynamically queried via `sqlite_master` and `PRAGMA`.
3. Click `students`: highlight column definitions, `CHECK(gpa >= 0.0 AND gpa <= 4.0)`, and foreign keys.
4. Click **Preview Data** to view live records from SQLite.

### Stage 3: Natural Language to SQL Query Generation
1. Navigate back to **Workspace** (`/`).
2. Enter the recommended evaluation question:  
   `"How many students belong to each department?"`
3. Click **Generate & Run**.
4. Show the generated SQL with syntax highlighting:
   ```sql
   SELECT d.department_name, COUNT(s.student_id) AS student_count
   FROM departments d
   LEFT JOIN students s ON d.department_id = s.department_id
   GROUP BY d.department_id, d.department_name
   ORDER BY student_count DESC;
   ```
5. Ground-Truth Answer in Canonical Database: Exactly 5 students in each of the 5 departments (25 students total).
6. Explain the core architectural distinctions to your evaluators:
   - **Generated SQL:** Probabilistic autoregressive output from Qwen2.5-Coder-1.5B-Instruct.
   - **SQL Validation:** Deterministic Abstract Syntax Tree (AST) validation via SQLGlot checking syntax and schema compliance.
   - **SQL Execution:** Secure execution through read-only SQLite sandbox with C-level authorizer hooks.
   - **Self-Correction:** Multi-turn compiler feedback loop when syntax or schema errors occur.
   - **Semantic Correctness:** Verifying whether execution results actually answer the intended question without unintended row multiplication.

### Stage 4: Critical Academic Finding — The Semantic Duplicate Phenomenon
1. Enter query: `"Show the top 5 students with the highest GPA."`
2. Click **Generate & Run**.
3. If the model joins `students` with `enrollments`, draw the evaluator's attention to the amber **Semantic Quality Advisory Banner**:  
   `POTENTIALLY_MULTIPLICATIVE_JOIN`
4. Click **Show Details** to show why execution validity does not guarantee semantic accuracy:
   - In our controlled Qwen experiment, the model repaired the column name from `student_name` to `first_name, last_name` via an `INNER JOIN enrollments`.
   - The query executed with 0 errors in SQLite, returning 5 rows.
   - However, because students have multiple course enrollments, those 5 rows contained only 2 distinct students (Emma Goldberg twice, Sofia Ramirez three times).
   - Highlighting this limitation proves your deep understanding of Generative AI limitations in database contexts.

### Stage 5: Execution-Guided Self-Correction
1. Show the **Correction Trace** tab.
2. Walk the evaluator through Attempt 1 (failing candidate + error diagnostic) $\to$ Attempt 2 (repaired query + green success).
3. Switch to the **Before / After SQL Diff Viewer** to show the exact lines changed by the model.

### Stage 6: Audit History & Analytics
1. Click **Query History** (`/history`): demonstrate the persistent audit log of every query, duration, and status.
2. Click **Insights** (`/insights`): show metrics dynamically aggregated across history.

---
*End of SchemaSense AI Demonstration Instructions*
