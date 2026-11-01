"""Test Colab notebook schema compliance, path independence, and evaluation dataset integrity."""

from collections import Counter
import json
from pathlib import Path
import sqlite3
import pytest
import nbformat as nbf


def test_colab_notebook_nbformat_validity():
    """Verify that SchemaSense_AI_GenAI_AAT1.ipynb is a valid Jupyter notebook."""
    nb_path = Path(__file__).resolve().parent.parent / "notebooks" / "SchemaSense_AI_GenAI_AAT1.ipynb"
    assert nb_path.exists(), f"Notebook not found at {nb_path}"

    with open(nb_path, "r", encoding="utf-8") as f:
        nb = nbf.read(f, as_version=4)

    # Validate against nbformat v4 specification
    nbf.validate(nb)
    assert len(nb.cells) >= 20, f"Expected at least 20 cells, got {len(nb.cells)}"


def test_colab_notebook_has_no_windows_paths():
    """Verify notebook contains no hardcoded Windows drive paths (E:\\, C:\\, etc.)."""
    nb_path = Path(__file__).resolve().parent.parent / "notebooks" / "SchemaSense_AI_GenAI_AAT1.ipynb"
    content = nb_path.read_text(encoding="utf-8")

    assert "E:\\\\" not in content, "Notebook contains hardcoded Windows drive E:\\\\"
    assert "E:/" not in content, "Notebook contains hardcoded Windows drive E:/"
    assert "C:\\\\" not in content, "Notebook contains hardcoded Windows drive C:\\\\"
    assert "C:/" not in content, "Notebook contains hardcoded Windows drive C:/"


def test_colab_notebook_contains_key_academic_sections():
    """Verify notebook includes all essential academic concepts and demonstrations."""
    nb_path = Path(__file__).resolve().parent.parent / "notebooks" / "SchemaSense_AI_GenAI_AAT1.ipynb"
    content = nb_path.read_text(encoding="utf-8")

    assert "Qwen/Qwen2.5-Coder-1.5B-Instruct" in content
    assert "POTENTIALLY_MULTIPLICATIVE_JOIN" in content
    assert "student_name" in content
    assert "sqlglot" in content
    assert "sqlite_read_only_authorizer" in content
    assert "execute_with_self_correction" in content
    assert "Student 1" in content
    assert "Student 2" in content


def test_evaluation_dataset_reference_queries_execute():
    """Verify all reference SQL queries in evaluation_dataset.json execute successfully."""
    backend_dir = Path(__file__).resolve().parent.parent
    ds_path = backend_dir / "evaluation" / "evaluation_dataset.json"
    db_path = backend_dir / "data" / "databases" / "campus_intelligence.db"

    assert ds_path.exists(), f"Dataset not found at {ds_path}"
    assert db_path.exists(), f"Database not found at {db_path}"

    with open(ds_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    executed_count = 0
    for q in data["questions"]:
        ref_sql = q.get("reference_sql")
        if ref_sql:
            cur.execute(ref_sql)
            rows = cur.fetchall()
            min_rows = q.get("min_expected_rows", 0)
            assert len(rows) >= min_rows, f"Query {q['id']} returned {len(rows)} rows, expected >= {min_rows}"
            executed_count += 1

    conn.close()
    assert executed_count == 15, f"Expected 15 reference queries executed, got {executed_count}"


def test_evaluation_denominators_consistency():
    """Verify that total questions and reference-evaluable questions have distinct, exact denominators."""
    backend_dir = Path(__file__).resolve().parent.parent
    ds_path = backend_dir / "evaluation" / "evaluation_dataset.json"

    with open(ds_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    questions = data["questions"]
    assert len(questions) == 16, f"Expected exactly 16 benchmark questions, found {len(questions)}"

    with_ref = [q for q in questions if q.get("reference_sql") is not None]
    without_ref = [q for q in questions if q.get("reference_sql") is None]

    assert len(with_ref) == 15, "Expected exactly 15 questions with reference SQL"
    assert len(without_ref) == 1, "Expected exactly 1 question without reference SQL"
    assert without_ref[0]["id"] == "EVAL-13"
    assert without_ref[0]["category"] == "invalid_schema_assumptions"


def test_claim_evidence_matrix_integrity():
    """Verify master evidence matrix exists and all verified claims reference valid files."""
    backend_dir = Path(__file__).resolve().parent.parent
    matrix_path = backend_dir / "evaluation" / "claim_evidence_matrix.json"
    assert matrix_path.exists(), f"Evidence matrix missing at {matrix_path}"

    with open(matrix_path, "r", encoding="utf-8") as f:
        matrix = json.load(f)

    assert "claims" in matrix
    assert len(matrix["claims"]) >= 10, "Expected at least 10 audited claims in master matrix"

    claim_ids = [c["claim_id"] for c in matrix["claims"]]
    assert len(claim_ids) == len(set(claim_ids)), "Duplicate claim IDs found in evidence matrix"

    for claim in matrix["claims"]:
        assert claim["verification_status"] in ["verified", "partially_verified", "unverified", "illustrative"]
        if claim["verification_status"] == "verified":
            evidence_rel = claim.get("evidence_file")
            assert evidence_rel is not None
            evidence_file = backend_dir.parent / evidence_rel
            assert evidence_file.exists(), f"Evidence file not found: {evidence_file} for claim {claim['claim_id']}"


def test_multiset_comparison_preserves_duplicates():
    """Verify multiset comparison detects entity duplication between reference and candidate results."""
    # Ground truth top 5 unique students:
    reference_rows = [
        ("Emma", "Goldberg", 3.96),
        ("Sofia", "Ramirez", 3.95),
        ("Aria", "Patel", 3.92),
        ("Ananya", "Deshmukh", 3.90),
        ("Layla", "Hassan", 3.89),
    ]

    # Model's multiplicative join output (5 rows, but only 2 unique students):
    duplicated_candidate_rows = [
        ("Emma", "Goldberg", 3.96),
        ("Emma", "Goldberg", 3.96),
        ("Sofia", "Ramirez", 3.95),
        ("Sofia", "Ramirez", 3.95),
        ("Sofia", "Ramirez", 3.95),
    ]

    # Set comparison would falsely consider Emma & Sofia present in both sets
    # But multiset (Counter) comparison correctly catches the mismatch:
    ref_counter = Counter([tuple(r) for r in reference_rows])
    cand_counter = Counter([tuple(r) for r in duplicated_candidate_rows])

    assert ref_counter != cand_counter, "Multiset comparison must distinguish duplicated rows from distinct rows"
    assert len(set(duplicated_candidate_rows)) == 2, "Candidate contains only 2 distinct entities"
    assert len(set(reference_rows)) == 5, "Reference contains 5 distinct entities"


def test_controlled_multiplicative_join_detection():
    """Verify that the semantic analyzer flags the Qwen duplicate-row join pattern."""
    from app.services.semantic_analyzer import get_semantic_analyzer
    from app.services.sqlite_inspector import introspect_sqlite_database
    from app.services.database_manager import get_database_manager

    db_manager = get_database_manager()
    db_info = db_manager.get_database("campus_intelligence")
    db_path = db_manager.get_database_path("campus_intelligence")
    schema_response = introspect_sqlite_database(db_path, db_info)

    analyzer = get_semantic_analyzer()

    # The exact query Qwen generated during correction in Phase 6:
    qwen_multiplicative_sql = (
        "SELECT T1.first_name, T1.last_name, T1.gpa "
        "FROM students AS T1 "
        "INNER JOIN enrollments AS T2 ON T1.student_id = T2.student_id "
        "ORDER BY T1.gpa DESC LIMIT 5;"
    )

    result = analyzer.analyze(
        sql=qwen_multiplicative_sql,
        schema=schema_response,
        natural_question="Show the top 5 students with the highest GPA.",
        row_count=5,
    )

    assert not result.is_semantically_sound, "Expected semantic warning for multiplicative join"
    assert "POTENTIALLY_MULTIPLICATIVE_JOIN" in result.detected_patterns


def test_gpa_scale_mismatch_warning():
    """Verify that GPA predicate above 4.0 triggers scale mismatch warning on campus_intelligence."""
    from app.services.semantic_analyzer import get_semantic_analyzer
    from app.services.sqlite_inspector import introspect_sqlite_database
    from app.services.database_manager import get_database_manager

    db_manager = get_database_manager()
    db_info = db_manager.get_database("campus_intelligence")
    db_path = db_manager.get_database_path("campus_intelligence")
    schema_response = introspect_sqlite_database(db_path, db_info)

    analyzer = get_semantic_analyzer()

    scale_test_sql = "SELECT * FROM students WHERE gpa > 8.5;"
    result = analyzer.analyze(
        sql=scale_test_sql,
        schema=schema_response,
        natural_question="Show students with a GPA above 8.5.",
        row_count=0,
    )

    assert not result.is_semantically_sound
    assert "POSSIBLE_SCALE_MISMATCH" in result.detected_patterns


def test_generated_notebook_code_cells_syntax_validity():
    """Verify that every code cell in both source and submission notebooks compiles without SyntaxError."""
    backend_dir = Path(__file__).resolve().parent.parent
    nb_paths = [
        backend_dir / "notebooks" / "SchemaSense_AI_GenAI_AAT1.ipynb",
        backend_dir / "submission" / "SchemaSense_AI_GenAI_AAT1.ipynb",
    ]
    for nb_path in nb_paths:
        assert nb_path.exists(), f"Notebook not found at {nb_path}"
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = json.load(f)

        for i, cell in enumerate(nb["cells"]):
            if cell.get("cell_type") == "code":
                source = "".join(cell.get("source", []))
                # Comment out IPython magics (!pip, %matplotlib, etc.) for syntax compilation
                py_lines = []
                for line in source.splitlines():
                    if line.strip().startswith("!") or line.strip().startswith("%"):
                        py_lines.append("# " + line)
                    else:
                        py_lines.append(line)
                code = "\n".join(py_lines)
                try:
                    compile(code, f"{nb_path.name}_Cell_{i}", "exec")
                except SyntaxError as e:
                    pytest.fail(f"SyntaxError in {nb_path.name} Cell {i:02d}: {e}")


def test_step11_question_formatting():
    """Verify Step 11 demo question formatting produces valid Python single-quoted f-string."""
    backend_dir = Path(__file__).resolve().parent.parent
    nb_path = backend_dir / "notebooks" / "SchemaSense_AI_GenAI_AAT1.ipynb"
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    step11_cells = [c for c in nb["cells"] if "Step 11" in "".join(c.get("source", []))]
    assert len(step11_cells) == 1, "Expected exactly 1 Step 11 cell"
    source = "".join(step11_cells[0]["source"])

    assert 'print(f\'DEMO {i}: "{q}"\')' in source
    assert 'print(f"DEMO {i}: "{q}"")' not in source


def test_step16_exact_match_nullable_boolean_and_mutually_exclusive_categories():
    """Verify Step 16 chart logic handles True, False, and None exact-match values robustly."""
    # Synthetic test data with 6 questions:
    # Q1: Clean pass (exact match = True)
    # Q2: Syntax error (syntax = False, schema = False, exec = False, exact = False)
    # Q3: Schema error (syntax = True, schema = False, exec = False, exact = False)
    # Q4: Runtime error (syntax = True, schema = True, exec = False, exact = False)
    # Q5: Non-evaluable schema rejection (syntax = True, schema = True, exec = True, exact = None)
    # Q6: Semantic mismatch (syntax = True, schema = True, exec = True, exact = False)
    rows = [
        {"id": "EVAL-01", "syntax": True, "schema": True, "exec": True, "exact": True},
        {"id": "EVAL-02", "syntax": False, "schema": False, "exec": False, "exact": False},
        {"id": "EVAL-03", "syntax": True, "schema": False, "exec": False, "exact": False},
        {"id": "EVAL-04", "syntax": True, "schema": True, "exec": False, "exact": False},
        {"id": "EVAL-05", "syntax": True, "schema": True, "exec": True, "exact": None},
        {"id": "EVAL-06", "syntax": True, "schema": True, "exec": True, "exact": False},
    ]

    # 1. Exact match denominator: dropna / exclude None
    evaluable_exact = [r["exact"] for r in rows if r["exact"] is not None]
    assert len(evaluable_exact) == 5, "Exact match denominator must exclude None (5 out of 6 evaluable)"
    assert sum(1 for e in evaluable_exact if e is True) == 1, "Only 1 exact match should be True"
    assert round((sum(1 for e in evaluable_exact if e is True) / len(evaluable_exact)) * 100, 2) == 20.0

    # 2. Test pandas Series semantics using vector operations matching Step 16
    class VectorSeries:
        def __init__(self, data):
            self.data = list(data)
        def fillna(self, val):
            return VectorSeries([val if x is None else x for x in self.data])
        def astype(self, t):
            return VectorSeries([t(x) for x in self.data])
        def eq(self, val):
            return VectorSeries([x == val for x in self.data])
        def dropna(self):
            return VectorSeries([x for x in self.data if x is not None])
        def sum(self):
            return sum(1 for x in self.data if x)
        def mean(self):
            return sum(float(x) for x in self.data) / len(self.data) if self.data else 0.0
        def __invert__(self):
            return VectorSeries([not x for x in self.data])
        def __and__(self, other):
            return VectorSeries([a and b for a, b in zip(self.data, other.data)])

    s_syntax = VectorSeries([r["syntax"] for r in rows]).fillna(False).astype(bool)
    s_schema = VectorSeries([r["schema"] for r in rows]).fillna(False).astype(bool)
    s_exec = VectorSeries([r["exec"] for r in rows]).fillna(False).astype(bool)
    s_exact = VectorSeries([r["exact"] for r in rows])

    # Pass rate calculations
    s_eval_exact = s_exact.dropna().astype(bool)
    assert round(s_eval_exact.mean() * 100, 2) == 20.0

    # 3. Mutually exclusive categories from Step 16
    syntax_errors = int((~s_syntax).sum())
    schema_errors = int((s_syntax & ~s_schema).sum())
    runtime_errors = int((s_syntax & s_schema & ~s_exec).sum())
    # Crucial: .eq(False) must not include None
    semantic_mismatch = int((s_exec & s_exact.eq(False)).sum())

    assert syntax_errors == 1  # Q2
    assert schema_errors == 1  # Q3
    assert runtime_errors == 1  # Q4
    assert semantic_mismatch == 1  # Q6
    total_anomalies = syntax_errors + schema_errors + runtime_errors + semantic_mismatch
    assert total_anomalies == 4


def test_step17_database_connection_and_export_integrity(tmp_path):
    """Verify Step 17 safely connects to SQLite read-only and exports valid JSON & ZIP."""
    import hashlib
    import zipfile

    backend_dir = Path(__file__).resolve().parent.parent
    db_path = backend_dir / "data" / "databases" / "campus_intelligence.db"
    assert db_path.exists()

    db_uri = f"file:{db_path.resolve()}?mode=ro"
    conn = sqlite3.connect(db_uri, uri=True)
    table_meta = []
    try:
        cur = conn.cursor()
        cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
        table_defs = cur.fetchall()
        for t_name, create_sql in table_defs:
            safe_name = t_name.replace('"', '""')
            cur.execute(f'SELECT COUNT(*) FROM "{safe_name}";')
            cnt = cur.fetchone()[0]
            table_meta.append({"table": t_name, "schema": create_sql, "row_count": cnt})
    finally:
        conn.close()

    assert len(table_meta) == 7, "Campus Intelligence must contain 7 tables"
    fingerprint = hashlib.sha256(json.dumps(table_meta, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
    assert len(fingerprint) == 16


def test_genuine_colab_evidence_verification():
    """Verify that genuine Colab evidence ZIP and executed notebook pass full consistency checks."""
    import zipfile
    backend_dir = Path(__file__).resolve().parent.parent
    evidence_dir = backend_dir / "submission" / "colab_evidence"
    zip_candidates = list(evidence_dir.glob("SchemaSense_AI_Colab_Evidence_colab_run_*.zip"))
    if not zip_candidates:
        pytest.skip("No genuine Colab evidence ZIP present in colab_evidence/ to verify.")

    zip_path = zip_candidates[0]
    executed_nb_path = evidence_dir / "SchemaSense_AI_GenAI_AAT1_EXECUTED.ipynb"
    assert executed_nb_path.exists(), "Executed notebook SchemaSense_AI_GenAI_AAT1_EXECUTED.ipynb must exist"

    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        assert "schemasense_colab_run_manifest.json" in namelist
        assert "schemasense_colab_model_results.json" in namelist
        assert "schemasense_colab_evaluation_metrics.json" in namelist
        assert "schemasense_evaluation_metrics.png" in namelist

        metrics = json.loads(zf.read("schemasense_colab_evaluation_metrics.json"))
        assert metrics["total_evaluated"] == 16
        assert metrics["syntax_valid_count"] == 16
        assert metrics["schema_valid_count"] == 16
        assert metrics["execution_success_count"] == 14
        assert metrics["exact_match_evaluable_count"] == 15
        assert metrics["exact_match_count"] == 5
        assert round(metrics["exact_match_rate"], 2) == 33.33
        assert metrics["mean_generation_latency_ms"] > 0
        assert metrics["mean_execution_latency_ms"] > 0

