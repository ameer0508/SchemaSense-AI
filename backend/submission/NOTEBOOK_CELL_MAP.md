# SchemaSense AI — Authoritative Google Colab Notebook Cell Map
## Academic Assignment (AAT-1) — Cell Index to Section Mapping Register

**Authoritative Notebook:** [`backend/notebooks/SchemaSense_AI_GenAI_AAT1.ipynb`](file:///e:/SchemaSense%20AI/backend/notebooks/SchemaSense_AI_GenAI_AAT1.ipynb)  
**Submission Notebook:** [`backend/submission/SchemaSense_AI_GenAI_AAT1.ipynb`](file:///e:/SchemaSense%20AI/backend/submission/SchemaSense_AI_GenAI_AAT1.ipynb)  
**Target Runtime:** Google Colab (Free-tier T4 GPU or CPU fallback)  
**Total Sequential Cells:** **38 Cells** (21 Markdown Cells, 17 Executable Code Cells)  
**SHA-256 Consistency:** Verified identical across both paths.

---

## 1. Authoritative Cell Index & Output Register

| Cell Index | Section / Step | Type | Purpose & Implementation | Expected Observable Output in Colab | Evidence / Screenshot Role |
| :---: | :--- | :---: | :--- | :--- | :--- |
| **Cell 00** | Title & Header | Markdown | Project title, academic context, course metadata, student author placeholders. | Rendered title banner, topic description, and author table. | Initial notebook header view. |
| **Cell 01** | Section 1 | Markdown | Problem definition, Text-to-SQL challenges, and motivation. | Section text and architectural goals. | Reference documentation. |
| **Cell 02** | Section 2 | Markdown | Multi-tier defensive architecture breakdown and technology stack. | Technology stack overview table. | Architecture overview. |
| **Cell 03** | Section 3 | Markdown | Environment prerequisites, library dependencies, and GPU detection. | Setup guidance. | Setup header. |
| **Cell 04** | **Step 1** | **Code** | Quiet installation of dependencies (`transformers`, `torch`, `sqlglot`, `pandas`, `tabulate`, `matplotlib`). | `[SUCCESS] All dependencies installed.` | Runtime environment setup. |
| **Cell 05** | **Step 2** | **Code** | Hardware detection (`torch.cuda.is_available()`) and seed initialization (`seed=42`). | `Hardware Acceleration: GPU (Tesla T4)` or `CPU`, active device, and precision (`float16` or `float32`). | **FIGURE 6 EVIDENCE** (Connected GPU badge + hardware confirmation). |
| **Cell 06** | Section 4 | Markdown | Generative model selection justification (`Qwen2.5-Coder-1.5B-Instruct` vs alternatives). | Model comparison table. | Academic justification. |
| **Cell 07** | Section 5 | Markdown | Synthetic dataset design (Campus Intelligence, 7 relational tables, 135 rows). | Dataset topology and integrity rules. | Schema reference. |
| **Cell 08** | **Step 3** | **Code** | Self-contained SQLite database seeder creating 135 rows with deterministic relations. | `[SUCCESS] Seeded campus_intelligence.db (7 tables, 135 records)` + table record summary. | Dataset creation log. |
| **Cell 09** | Auxiliary | **Code** | Inspects and displays sample records from `departments`, `faculty`, `students`, `courses`. | Formatted tabular previews of relational records. | Data preview validation. |
| **Cell 10** | Section 6 | Markdown | Dynamic SQLite schema introspection methodology using `sqlite_master` and `PRAGMA`. | Introspection principles. | Dynamic catalog notes. |
| **Cell 11** | **Step 4** | **Code** | `DynamicSchemaIntrospector` querying tables, primary keys, foreign keys, and column types. | `Dynamic SQLite Schema Introspection Report` displaying catalog table. | Dynamic introspection verification. |
| **Cell 12** | Section 7 | Markdown | ChatML structured prompt engineering with negative constraints and output contract. | Prompt format documentation. | Prompt design notes. |
| **Cell 13** | **Step 5** | **Code** | `build_structured_prompt()` formatting natural language query + dynamic schema context. | Prints full ChatML prompt string for a sample question. | Prompt serialization preview. |
| **Cell 14** | Section 8 | Markdown | Model architecture, Hugging Face ingestion, and greedy autoregressive generation. | Model loading specifications. | Model architecture notes. |
| **Cell 15** | **Step 6** | **Code** | Ingests `Qwen/Qwen2.5-Coder-1.5B-Instruct` and tokenizer directly from Hugging Face Hub. | `[SUCCESS] Model loaded in X.XXs. Parameters: 1.54B | Device: cuda/cpu | Precision: float16/float32`. | **FIGURE 6 EVIDENCE** (Model loading and device allocation). |
| **Cell 16** | **Step 7** | **Code** | `generate_sql()` performing greedy autoregressive forward passes and SQL extraction. | Generates and executes test query; prints generated SQL and latency in milliseconds. | Generation sanity check. |
| **Cell 17** | Section 9 | Markdown | Abstract Syntax Tree (AST) validation principles using SQLGlot. | Multi-tier guardrail specifications. | AST validation notes. |
| **Cell 18** | **Step 8** | **Code** | `SQLGlotASTValidator` enforcing single-statement, read-only AST, and schema compliance. | Tests valid SELECT, multi-statement injection (`BLOCKED`), and mutating CTE (`BLOCKED`). | AST guardrail verification. |
| **Cell 19** | Section 10 | Markdown | In-process SQLite C-authorizer callback and instruction progress handler limits. | Security sandbox boundaries. | Defense-in-depth notes. |
| **Cell 20** | **Step 9** | **Code** | `SandboxedSQLiteExecutor` executing queries via read-only URI with authorizer hook. | Tests clean query (`success`), destructive write (`AUTHORIZER_DENIED`), and recursive timeout (`TIMEOUT`). | Execution security verification. |
| **Cell 21** | Section 11 | Markdown | Multi-turn execution-guided self-correction algorithm and error feedback loop. | Algorithm description. | Self-correction notes. |
| **Cell 22** | **Step 10** | **Code** | `SelfCorrectionEngine` orchestrating generate $\to$ validate $\to$ execute $\to$ diagnose $\to$ repair. | Helper function definitions and repair loop structure. | Correction engine setup. |
| **Cell 23** | Section 12 | Markdown | End-to-end demonstrations across simple, aggregate, and multi-table questions. | Demonstration protocol. | Pipeline demonstration notes. |
| **Cell 24** | **Step 11** | **Code** | Runs end-to-end multi-turn pipeline across representative academic questions. | Prints attempt history, generated SQL, validation status, duration, and execution output rows. | Pipeline live trace. |
| **Cell 25** | Section 13 | Markdown | Critical academic finding: execution validity vs. semantic answer correctness. | Semantic correctness gap discussion. | Theory & case study notes. |
| **Cell 26** | **Step 12** | **Code** | Controlled correction experiment: repairs `student_name` $\to$ reveals duplicate 1-to-N JOIN. | `Attempt 1: FAILED` $\to$ `Attempt 2: REPAIRED (0.58 ms)` $\to$ `DUPLICATE ROWS DETECTED (2 distinct of 5)`. | **FIGURE 4 & 5 EVIDENCE** (Correction trace & semantic duplicate phenomenon). |
| **Cell 27** | **Step 13** | **Code** | `ConservativeSemanticAnalyzer` detecting `POTENTIALLY_MULTIPLICATIVE_JOIN`. | `[ADVISORY WARNING] POTENTIALLY_MULTIPLICATIVE_JOIN detected` with corrective advice. | **FIGURE 5 EVIDENCE** (Semantic advisory banner). |
| **Cell 28** | Section 14 | Markdown | Quantitative benchmark evaluation principles (16 questions, exact denominators). | Benchmark methodology. | Methodology documentation. |
| **Cell 29** | **Step 14** | **Code** | `BENCHMARK_QUESTIONS`: 16 curated queries (`EVAL-01` to `EVAL-16`) with category and reference SQL. | Prints benchmark dataset summary (16 total questions, 15 with reference queries). | Benchmark inventory log. |
| **Cell 30** | **Step 15** | **Code** | `run_benchmark_evaluation()` evaluating questions, computing metrics, and formatting results. | `BENCHMARK EVALUATION SUMMARY TABLE` displaying per-question pass status and generation latency. | **FIGURE 7 EVIDENCE** (Model evaluation results table). |
| **Cell 31** | Section 15 | Markdown | Results visualization design and statistical chart specifications. | Visualization methodology. | Chart methodology. |
| **Cell 32** | **Step 16** | **Code** | Generates 4-panel Matplotlib plot and saves `schemasense_evaluation_metrics.png` (300 DPI). | Renders 4 charts: A. Pass Rates, B. Latency, C. Execution vs Correction, D. Outcome Breakdown. | **FIGURE 7 EVIDENCE** (Rendered 4-panel evaluation plot). |
| **Cell 33** | Section 16 | Markdown | Comprehensive academic research discussion, model scalability, and findings. | Research analysis. | Academic discussion. |
| **Cell 34** | Section 17 | Markdown | Conclusion, key findings, and recommendations for enterprise deployments. | Concluding remarks. | Academic conclusion. |
| **Cell 35** | Section 18 | Markdown | Individual project team contributions and two-student work distribution. | Formal student contribution breakdown. | Contribution breakdown. |
| **Cell 36** | Section 19 | Markdown | Export measured evaluation evidence instructions and ZIP archive overview. | Evidence export guidance. | Export instructions. |
| **Cell 37** | **Step 17** | **Code** | Serializes run manifest, model results JSON, metrics JSON, and bundles into ZIP archive. | `SUCCESS: Exported genuine evaluation evidence archive: SchemaSense_AI_Colab_Evidence_<run_id>.zip`. | **MEASURED EVIDENCE ARTIFACT** for local ingestion. |

---

## 2. Critical Disambiguation: Section Numbers vs. Cell Indices

To eliminate confusion during oral examinations, viva presentations, and report referencing, note the exact distinction:

- **Hardware Acceleration Check:** Referenced as Section 3 / Step 2 $\implies$ **Actual Code Cell 05**.
- **Model Ingestion & VRAM Allocation:** Referenced as Section 8 / Step 6 $\implies$ **Actual Code Cell 15**.
- **Natural Language Inference:** Referenced as Section 8 / Step 7 $\implies$ **Actual Code Cell 16**.
- **Controlled Self-Correction & Semantic Duplication:** Referenced as Section 13 / Step 12 $\implies$ **Actual Code Cell 26**.
- **Quantitative Benchmark Runner:** Referenced as Section 14 / Step 15 $\implies$ **Actual Code Cell 30**.
- **Publication Matplotlib Visualizations:** Referenced as Section 15 / Step 16 $\implies$ **Actual Code Cell 32**.
- **Evidence Export Archive Generator:** Referenced as Section 19 / Step 17 $\implies$ **Actual Code Cell 37**.

---

*End of SchemaSense AI Authoritative Notebook Cell Map*
