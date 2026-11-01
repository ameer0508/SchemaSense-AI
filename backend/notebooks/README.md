# SchemaSense AI — Notebooks Directory

This directory contains the standalone Google Colab implementation and notebook build tooling for **SchemaSense AI**.

## Deliverables

1. **`SchemaSense_AI_GenAI_AAT1.ipynb`**:
   - The primary standalone Jupyter notebook for the **Generative AI Academic Assignment (AAT-1)** (7th Semester B.Tech Computer Science and Engineering).
   - Fully independent of the local Windows workspace (`E:\SchemaSense AI`), FastAPI server, or React frontend.
   - Self-contained: deterministically generates the synthetic **Campus Intelligence** SQLite database (7 relational tables, foreign key constraints, indices, check constraints).
   - Validated against `nbformat` v4.
   - Automatically detects GPU hardware acceleration (`torch.cuda.is_available()`), configuring `torch.float16` on CUDA (Google Colab T4/V100/A100) or `torch.float32` on CPU.
   - Employs the genuine `Qwen/Qwen2.5-Coder-1.5B-Instruct` model for zero-shot text-to-SQL inference and execution-guided self-correction.
   - Incorporates SQLGlot AST validation, read-only sandboxed execution via SQLite authorizers, conservative semantic integrity analysis (multiplicative join detection), quantitative benchmark evaluation, and publication-quality Matplotlib visualizations.
   - Includes editable contributions for Student 1 and Student 2.

2. **`build_colab_notebook.py`**:
   - Programmatic Python builder that generates and validates `SchemaSense_AI_GenAI_AAT1.ipynb` using `nbformat.v4`.
   - Run via: `python backend/notebooks/build_colab_notebook.py`.

## Running in Google Colab

1. Open [Google Colab](https://colab.research.google.com/).
2. Select **Upload** and upload `SchemaSense_AI_GenAI_AAT1.ipynb`.
3. In the top menu, select **Runtime > Change runtime type** and choose **T4 GPU** (or CPU if GPU quota is exhausted).
4. Run all cells: **Runtime > Run all** (or `Ctrl+F9`).
5. All synthetic database files and generated visualization charts (`schemasense_evaluation_metrics.png`) are saved directly in Colab's local directory without requiring any manual file uploads or API keys.
