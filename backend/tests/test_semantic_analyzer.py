"""Unit tests and regression test for Semantic SQL Quality Analyzer."""

from app.db.seed_demo import DEMO_DB_ID
from app.services.database_manager import get_database_manager
from app.services.execution_service import get_execution_service
from app.services.semantic_analyzer import SemanticAnalyzer, get_semantic_analyzer
from app.services.sqlite_inspector import introspect_sqlite_database


def test_top_five_students_multiplicative_join_regression():
    """REGRESSION TEST: Critical Phase 4 Finding.

    The model generated:
    SELECT T1.first_name, T1.last_name, T1.gpa
    FROM students AS T1
    JOIN enrollments AS T2 ON T1.student_id = T2.student_id
    ORDER BY T1.gpa DESC LIMIT 5;

    This query executes successfully on SQLite, but joins 1-to-N enrollments
    without selecting any enrollment fields or applying DISTINCT/GROUP BY.
    Students with multiple enrollments will be duplicated, producing semantically incorrect output.
    """
    db_mgr = get_database_manager()
    db_info = db_mgr.get_database(DEMO_DB_ID)
    schema = introspect_sqlite_database(db_mgr.get_database_path(DEMO_DB_ID), db_info)

    analyzer = get_semantic_analyzer()
    sql = (
        "SELECT T1.first_name, T1.last_name, T1.gpa "
        "FROM students AS T1 "
        "JOIN enrollments AS T2 ON T1.student_id = T2.student_id "
        "ORDER BY T1.gpa DESC LIMIT 5;"
    )

    res = analyzer.analyze(
        sql=sql,
        schema=schema,
        natural_question="Show the top 5 students with the highest GPA",
    )

    # Must flag the potential multiplicative join anomaly
    assert res.is_semantically_sound is False
    assert "POTENTIALLY_MULTIPLICATIVE_JOIN" in res.detected_patterns
    assert any("enrollments" in w and "multiplicative" in w.lower() for w in res.warnings)
    assert res.recommendation is not None
    assert "enrollments" in res.recommendation


def test_clean_join_without_false_positive():
    """Verify that a legitimate join where child attributes ARE projected is considered semantically sound."""
    db_mgr = get_database_manager()
    db_info = db_mgr.get_database(DEMO_DB_ID)
    schema = introspect_sqlite_database(db_mgr.get_database_path(DEMO_DB_ID), db_info)

    analyzer = get_semantic_analyzer()
    sql = (
        "SELECT s.first_name, s.last_name, e.grade "
        "FROM students s "
        "JOIN enrollments e ON s.student_id = e.student_id "
        "LIMIT 10;"
    )

    res = analyzer.analyze(sql=sql, schema=schema)
    assert res.is_semantically_sound is True
    assert "POTENTIALLY_MULTIPLICATIVE_JOIN" not in res.detected_patterns
    assert len(res.warnings) == 0


def test_distinct_prevents_multiplicative_warning():
    """Verify that applying DISTINCT suppresses the multiplicative join warning."""
    db_mgr = get_database_manager()
    db_info = db_mgr.get_database(DEMO_DB_ID)
    schema = introspect_sqlite_database(db_mgr.get_database_path(DEMO_DB_ID), db_info)

    analyzer = get_semantic_analyzer()
    sql = (
        "SELECT DISTINCT T1.first_name, T1.last_name, T1.gpa "
        "FROM students AS T1 "
        "JOIN enrollments AS T2 ON T1.student_id = T2.student_id "
        "ORDER BY T1.gpa DESC LIMIT 5;"
    )

    res = analyzer.analyze(sql=sql, schema=schema)
    assert "POTENTIALLY_MULTIPLICATIVE_JOIN" not in res.detected_patterns


def test_cartesian_product_detection():
    """Verify that joins without an ON condition are flagged as suspicious Cartesian products."""
    analyzer = get_semantic_analyzer()
    sql = "SELECT s.first_name, d.department_name FROM students s CROSS JOIN departments d;"
    res = analyzer.analyze(sql=sql)
    assert res.is_semantically_sound is False
    assert "SUSPICIOUS_CARTESIAN_PRODUCT" in res.detected_patterns


def test_ranking_without_limit_detection():
    """Verify that ranking/ordering queries lacking a LIMIT clause are warned."""
    analyzer = get_semantic_analyzer()
    sql = "SELECT first_name, gpa FROM students ORDER BY gpa DESC;"
    res = analyzer.analyze(sql=sql, natural_question="Show students ranked by GPA")
    assert res.is_semantically_sound is False
    assert "RANKING_WITHOUT_LIMIT" in res.detected_patterns


def test_multitable_wildcard_projection_detection():
    """Verify that SELECT * across multiple joined tables is flagged."""
    analyzer = get_semantic_analyzer()
    sql = "SELECT * FROM students s JOIN departments d ON s.department_id = d.department_id;"
    res = analyzer.analyze(sql=sql)
    assert res.is_semantically_sound is False
    assert "MULTITABLE_WILDCARD" in res.detected_patterns


def test_aggregation_correctness_reference_query():
    """Verify that aggregation query execution matches verified reference truth in Campus Intelligence.

    Validates that each department has exactly 5 students and 25 total students exist.
    """
    exec_svc = get_execution_service()
    sql = "SELECT department_id, COUNT(*) AS student_count FROM students GROUP BY department_id ORDER BY department_id;"

    res = exec_svc.execute_query(
        database_id=DEMO_DB_ID,
        sql=sql,
    )
    assert res.status == "success"
    assert res.columns == ["department_id", "student_count"]
    assert res.row_count == 5

    # Deterministic verified ground truth from seed_demo.py
    expected_dept_counts = {
        "DEP-CS": 5,
        "DEP-DS": 5,
        "DEP-EE": 5,
        "DEP-MATH": 5,
        "DEP-PHYS": 5,
    }
    actual_counts = {row[0]: row[1] for row in res.rows}
    assert actual_counts == expected_dept_counts
    assert sum(actual_counts.values()) == 25


def test_gpa_scale_mismatch_warning():
    """Verify Phase 5 Finding A: Flag queries comparing GPA against 8.5 when max constraint is 4.0."""
    db_mgr = get_database_manager()
    db_info = db_mgr.get_database(DEMO_DB_ID)
    schema = introspect_sqlite_database(db_mgr.get_database_path(DEMO_DB_ID), db_info)

    analyzer = get_semantic_analyzer()
    sql = "SELECT * FROM students WHERE gpa > 8.5;"
    res = analyzer.analyze(sql=sql, schema=schema, natural_question="Show students with GPA above 8.5")

    assert res.is_semantically_sound is False
    assert "POSSIBLE_SCALE_MISMATCH" in res.detected_patterns
    assert any("8.5" in w for w in res.warnings)

    # Check structured warning item
    mismatch_item = next((item for item in res.structured_warnings if item.code == "POSSIBLE_SCALE_MISMATCH"), None)
    assert mismatch_item is not None
    assert mismatch_item.severity == "warning"
    assert mismatch_item.evidence["column"] == "students.gpa"
    assert mismatch_item.evidence["constraint_type"] == "declared"
    assert mismatch_item.evidence["threshold"] == 8.5
    assert mismatch_item.evidence["bound_max"] == 4.0


def test_gpa_scale_valid_bound():
    """Verify that a valid GPA threshold (e.g. 3.5) does not trigger scale mismatch."""
    db_mgr = get_database_manager()
    db_info = db_mgr.get_database(DEMO_DB_ID)
    schema = introspect_sqlite_database(db_mgr.get_database_path(DEMO_DB_ID), db_info)

    analyzer = get_semantic_analyzer()
    sql = "SELECT * FROM students WHERE gpa > 3.5;"
    res = analyzer.analyze(sql=sql, schema=schema)

    assert "POSSIBLE_SCALE_MISMATCH" not in res.detected_patterns
    assert res.is_semantically_sound is True


def test_empty_result_advisory_preserves_soundness():
    """Verify that a query returning zero records receives an info-level advisory and is not treated as an error."""
    analyzer = get_semantic_analyzer()
    sql = "SELECT first_name, last_name FROM students WHERE first_name = 'NonexistentStudent';"
    res = analyzer.analyze(sql=sql, row_count=0)

    # Empty result should NOT make the query semantically unsound (Section 5 requirement)
    assert res.is_semantically_sound is True
    assert "EMPTY_RESULT_SET" in res.detected_patterns
    zero_item = next((item for item in res.structured_warnings if item.code == "EMPTY_RESULT_SET"), None)
    assert zero_item is not None
    assert zero_item.severity == "info"
    assert zero_item.evidence["row_count"] == 0

