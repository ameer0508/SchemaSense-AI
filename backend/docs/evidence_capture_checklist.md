# SchemaSense AI — Screenshot Evidence Capture Checklist
## For Generative AI Academic Report (AAT-1)
**Project Title:** SchemaSense AI — Natural Language. Precise SQL.  
**Target Document:** 10+ Page Academic Assignment Report (AAT-1)  
**Authors:** Student 1 (Generative AI & Inference Lead) & Student 2 (Validation, Execution & Benchmarking Lead)  

---

## 1. Overview & Instructions for the Student Team

This checklist details every required visual screenshot artifact to incorporate into the final AAT-1 academic report.

> [!IMPORTANT]
> **Strict Academic Rule:** All screenshots must be captured from the actual running application (`http://127.0.0.1:5173`) and actual Google Colab execution of `SchemaSense_AI_GenAI_AAT1.ipynb`. Never use mockups or artificial graphics.

---

## 2. Web Application Screenshot Checklist

### Category A: System Overview & Architecture
- [ ] **FIG-01: Full Workspace Studio Interface**
  - *Where:* `http://127.0.0.1:5173/` (Dark Mode recommended).
  - *What must be visible:* Top navigation with **Academic Suite** badge, green **Backend Connected** indicator, active **Campus Intelligence** database selector, Natural Language Question Composer, and Model Status widget (`Qwen2.5-Coder-1.5B-Instruct`).
  - *Report Section:* Section 1 (System Architecture & User Interface).

- [ ] **FIG-02: System Capability Matrix Modal**
  - *Where:* Click the green **Backend Connected** pill in the top header.
  - *What must be visible:* The modal titled **"System Capability Matrix"**, showing Phase 8 active capabilities (Health check, schema introspection, natural language SQL, read-only execution, self-correction, history, and telemetry).
  - *Report Section:* Section 2 (System Implementation & Capability Discovery).

### Category B: Schema Grounding & Metadata Introspection
- [ ] **FIG-03: Schema Explorer Catalog Overview**
  - *Where:* `http://127.0.0.1:5173/schemas`.
  - *What must be visible:* Left sidebar showing all 7 tables (`departments`, `faculty`, `students`, `courses`, `enrollments`, `attendance`, `assessments`) with column counts and total record counts.
  - *Report Section:* Section 3 (Dynamic Database Schema Grounding).

- [ ] **FIG-04: Relational Foreign Key Graph & Data Preview**
  - *Where:* Inside Schema Explorer, click on `students` table, then switch to **Preview Data**.
  - *What must be visible:* Table columns with primary key badge (`student_id [PK]`), foreign key badge (`department_id -> departments.department_id`), and 20 sample rows populated from SQLite.
  - *Report Section:* Section 3 (Relational Integrity & Schema Grounding).

### Category C: Natural Language to SQL Generation & AST Validation
- [ ] **FIG-05: Schema-Grounded SQL Generation**
  - *Where:* Workspace Studio (`/`), query: *"Show all students enrolled in the Computer Science department (DEP-CS)."*
  - *What must be visible:* Input question, generated SQL in editor, syntax highlighting, **AST Valid & Grounded** green badge, and target dialect badge (`SQLITE`).
  - *Report Section:* Section 4 (Generative Model Inference & AST Verification).

- [ ] **FIG-06: Read-Only SQLite Execution Results Table**
  - *Where:* Results sandbox tab immediately after running Query A.
  - *What must be visible:* Query Results header with row count badge (`5 rows`), execution duration (`<2 ms`), tabular records (`Lucas Bennett`, `Aria Patel`, etc.), and **Export CSV** button.
  - *Report Section:* Section 4 (Sandboxed Query Execution & Results Rendering).

### Category D: Critical Research Finding — Semantic Accuracy Gap
- [ ] **FIG-07: Semantic Quality Advisory Warning (Multiplicative Join)**
  - *Where:* Workspace Studio, query: *"Show the top 5 students with the highest GPA."*
  - *What must be visible:* Amber advisory banner:  
    `Semantic Quality Advisory: SQL executed successfully, but results may not answer the question correctly.`  
    Expanded details showing `POTENTIALLY_MULTIPLICATIVE_JOIN` and evidence: `child_table: enrollments, parent_table: students, foreign_key: student_id`.
  - *Report Section:* Section 5 (Critical Research Finding: Execution Validity vs Semantic Correctness).

- [ ] **FIG-08: Duplicated Student Entity Output**
  - *Where:* The Results Table beneath the advisory banner.
  - *What must be visible:* The 5 returned rows showing Emma Goldberg duplicated twice and Sofia Ramirez duplicated three times, clearly illustrating the semantic duplication phenomenon.
  - *Report Section:* Section 5 (Empirical Demonstration of the Semantic Gap).

### Category E: Execution-Guided Self-Correction
- [ ] **FIG-09: Multi-Turn Correction Trace & Timeline**
  - *Where:* Workspace Studio, click **Correction Trace** tab.
  - *What must be visible:* Attempt 1 (red error badge + compiler diagnostic message: `no such column: student_name`), Attempt 2 (green success badge + repaired SQL), and repair count badge.
  - *Report Section:* Section 6 (Execution-Guided Self-Correction Algorithm).

- [ ] **FIG-10: Before / After SQL Diff Viewer**
  - *Where:* Inside Correction Trace panel, scroll to the diff viewer.
  - *What must be visible:* Color-coded diff showing red deletion of `student_name` and green addition of `first_name, last_name`.
  - *Report Section:* Section 6 (Automated Query Repair Analysis).

### Category F: Telemetry, Audit Logs & Analytics
- [ ] **FIG-11: Query History Archive**
  - *Where:* `http://127.0.0.1:5173/history`.
  - *What must be visible:* Tabular history of executed queries, status badges (`success`, `repaired`), execution durations, timestamps, and search filter bar.
  - *Report Section:* Section 7 (Audit Logging & Query Persistence).

- [ ] **FIG-12: Insights Analytics Dashboard**
  - *Where:* `http://127.0.0.1:5173/insights`.
  - *What must be visible:* Total Queries card, Average Latency card, Pass Rate card, and error category distribution charts.
  - *Report Section:* Section 7 (System Telemetry & Performance Optimization).

---

## 3. Google Colab Notebook Screenshot Checklist

### Category G: Colab Environment & Hardware Acceleration
- [ ] **FIG-13: Colab Hardware Detection Output**
  - *Where:* Google Colab, execution of Cell 2.
  - *What must be visible:* Output text:  
    `Hardware Acceleration Detected: GPU (Tesla T4)`  
    `Allocated VRAM: 15.00 GB | Precision: float16`  
    `Python Version: 3.10.x | PyTorch Version: 2.x`
  - *Report Section:* Section 8 (Google Colab Implementation & GPU Runtimes).

- [ ] **FIG-14: Transformer Model Loading in FP16**
  - *Where:* Google Colab, execution of Cell 6.
  - *What must be visible:* Model loading output for `Qwen/Qwen2.5-Coder-1.5B-Instruct`, load duration in seconds, parameter count (`1.54 Billion`), and target device (`cuda`).
  - *Report Section:* Section 8 (Model Deployment & Resource Optimization).

### Category H: Quantitative Benchmarking & Visualizations
- [ ] **FIG-15: Academic Benchmark Summary Table**
  - *Where:* Google Colab, execution of Cell 15.
  - *What must be visible:* Formatted summary table printed by Pandas showing `ID`, `Category`, `Syntax Valid`, `Exec Success`, `Exact Match`, and `Gen Latency (ms)` across benchmark test cases.
  - *Report Section:* Section 9 (Quantitative Benchmark Results & Statistical Analysis).

- [ ] **FIG-16: 4-Panel Publication-Quality Matplotlib Figure**
  - *Where:* Google Colab, execution of Cell 16 (or saved file `schemasense_evaluation_metrics.png`).
  - *What must be visible:* All 4 subplots:
    1. Subplot A: Pipeline Layer Verification Rates (Bar chart).
    2. Subplot B: Generation vs Execution Latency Breakdown (Line/Bar chart).
    3. Subplot C: Self-Correction Efficacy Target Progression.
    4. Subplot D: Failure Taxonomy Distribution (Pie chart).
  - *Report Section:* Section 9 (Empirical Visualizations & Performance Figures).

---

## 4. Student Verification Sign-Off

| Verification Item | Completed By | Date Verified | Evidence Image Path |
| :--- | :--- | :--- | :--- |
| FIG-01 to FIG-06 (Web App Foundations) | Student 1 / Student 2 | ______________ | `docs/screenshots/fig01_fig06.png` |
| FIG-07 to FIG-10 (Semantic & Correction) | Student 2 (Validation Lead) | ______________ | `docs/screenshots/fig07_fig10.png` |
| FIG-11 to FIG-12 (History & Insights) | Student 2 | ______________ | `docs/screenshots/fig11_fig12.png` |
| FIG-13 to FIG-16 (Google Colab Run) | Student 1 (GenAI Lead) | ______________ | `docs/screenshots/fig13_fig16.png` |
