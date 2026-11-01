"""Semantic SQL Quality Analyzer.

Provides objective static and contextual checks for potential semantic anomalies:
- Numeric thresholds outside declared or observed column constraints (e.g. GPA > 8.5 on a 4.0 scale)
- Multiplicative 1-to-N JOINs that produce duplicate rows without DISTINCT/GROUP BY
- Cartesian products (cross joins without join predicates)
- Ranking queries lacking LIMIT clauses
- Multi-table wildcard projections
- Zero-row execution result advisories
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
import sqlglot
from sqlglot import exp

from app.core.logging import get_logger
from app.schemas.database import DatabaseSchemaResponse
from app.schemas.execution import SemanticAnalysisResult, SemanticWarningItem

logger = get_logger("semantic_analyzer")


class SemanticAnalyzer:
    """Analyzes SQL queries for semantic hazards, scale discrepancies, and questionable relational patterns."""

    def __init__(self, dialect: str = "sqlite"):
        self.dialect = dialect

    def analyze(
        self,
        sql: str,
        schema: Optional[DatabaseSchemaResponse] = None,
        natural_question: Optional[str] = None,
        row_count: Optional[int] = None,
    ) -> SemanticAnalysisResult:
        """Analyze a valid SQL query against relational schema, constraints, and question intent."""
        warnings: List[str] = []
        structured_warnings: List[SemanticWarningItem] = []
        detected_patterns: List[str] = []
        recommendations: List[str] = []

        try:
            ast = sqlglot.parse_one(sql, read=self.dialect)
        except Exception as e:
            item = SemanticWarningItem(
                code="PARSE_ERROR",
                severity="warning",
                message=f"Could not parse query for semantic analysis: {str(e)}",
                evidence={"raw_error": str(e)},
            )
            return SemanticAnalysisResult(
                is_semantically_sound=False,
                warnings=[item.message],
                structured_warnings=[item],
                detected_patterns=["PARSE_ERROR"],
            )

        # 1. Numeric Scale and Range Mismatches (Finding A & Section 5)
        if schema:
            scale_warnings, scale_items, scale_patterns, scale_recs = self._check_numeric_scale_and_range_mismatches(
                ast, schema
            )
            warnings.extend(scale_warnings)
            structured_warnings.extend(scale_items)
            detected_patterns.extend(scale_patterns)
            recommendations.extend(scale_recs)

        # 2. Inspect JOINs and check for Multiplicative Joins (Finding B)
        if schema and isinstance(ast, exp.Select):
            multi_join_warning, rec, evidence = self._check_multiplicative_joins(ast, schema)
            if multi_join_warning:
                warnings.append(multi_join_warning)
                detected_patterns.append("POTENTIALLY_MULTIPLICATIVE_JOIN")
                structured_warnings.append(
                    SemanticWarningItem(
                        code="POTENTIALLY_MULTIPLICATIVE_JOIN",
                        severity="advisory",
                        message=multi_join_warning,
                        evidence=evidence or {},
                    )
                )
                if rec:
                    recommendations.append(rec)

        # 3. Check for Cartesian Products (joins without join conditions)
        cartesian_warning = self._check_cartesian_products(ast)
        if cartesian_warning:
            warnings.append(cartesian_warning)
            detected_patterns.append("SUSPICIOUS_CARTESIAN_PRODUCT")
            structured_warnings.append(
                SemanticWarningItem(
                    code="SUSPICIOUS_CARTESIAN_PRODUCT",
                    severity="warning",
                    message=cartesian_warning,
                    evidence={},
                )
            )
            recommendations.append("Specify explicit ON or WHERE join conditions to prevent exponential row expansion.")

        # 4. Check for Ranking queries lacking LIMIT
        if isinstance(ast, exp.Select):
            has_order_by = bool(ast.args.get("order"))
            has_limit = bool(ast.args.get("limit"))
            q_lower = (natural_question or "").lower()
            ranking_keywords = ["top", "highest", "lowest", "best", "worst", "rank"]
            has_ranking_intent = any(re.search(rf"\b{kw}\b", q_lower) for kw in ranking_keywords)

            if (has_ranking_intent or has_order_by) and not has_limit:
                rank_msg = "Query orders records but lacks a LIMIT clause, which may return an unbounded result set."
                warnings.append(rank_msg)
                detected_patterns.append("RANKING_WITHOUT_LIMIT")
                structured_warnings.append(
                    SemanticWarningItem(
                        code="RANKING_WITHOUT_LIMIT",
                        severity="advisory",
                        message=rank_msg,
                        evidence={"has_order_by": has_order_by, "has_ranking_intent": has_ranking_intent},
                    )
                )
                recommendations.append("Add an appropriate LIMIT clause (e.g. LIMIT 5 or LIMIT 50).")

        # 5. Check for Wildcard Projections across Multiple Tables
        tables_referenced = [t.name.lower() for t in ast.find_all(exp.Table) if t.name]
        has_projected_star = False
        if isinstance(ast, exp.Select) and ast.expressions:
            for expr in ast.expressions:
                if isinstance(expr, exp.Star):
                    has_projected_star = True
                    break
                if isinstance(expr, exp.Column) and (getattr(expr, "is_star", False) or isinstance(expr.this, exp.Star)):
                    has_projected_star = True
                    break

        if len(set(tables_referenced)) > 1 and has_projected_star:
            star_msg = "Wildcard SELECT * across multiple joined tables returns all columns from all tables."
            warnings.append(star_msg)
            detected_patterns.append("MULTITABLE_WILDCARD")
            structured_warnings.append(
                SemanticWarningItem(
                    code="MULTITABLE_WILDCARD",
                    severity="advisory",
                    message=star_msg,
                    evidence={"tables_count": len(set(tables_referenced))},
                )
            )
            recommendations.append("Explicitly project only the specific required columns.")

        # 6. Check for Zero-Row Execution Result (Advisory, not an automatic error)
        if row_count is not None and row_count == 0:
            zero_msg = "The query executed successfully but returned 0 rows. Verify that the filtering criteria match the actual values in the database."
            structured_warnings.append(
                SemanticWarningItem(
                    code="EMPTY_RESULT_SET",
                    severity="info",
                    message=zero_msg,
                    evidence={"row_count": 0},
                )
            )
            detected_patterns.append("EMPTY_RESULT_SET")

        # Soundness: any static/schema warning makes it semantically unsound; info-level advisories (like EMPTY_RESULT_SET) preserve soundness
        is_sound = len(warnings) == 0
        primary_rec = " ".join(recommendations) if recommendations else None

        return SemanticAnalysisResult(
            is_semantically_sound=is_sound,
            warnings=warnings,
            structured_warnings=structured_warnings,
            detected_patterns=detected_patterns,
            recommendation=primary_rec,
        )

    def _check_numeric_scale_and_range_mismatches(
        self,
        ast: exp.Expression,
        schema: DatabaseSchemaResponse,
    ) -> Tuple[List[str], List[SemanticWarningItem], List[str], List[str]]:
        """Identify comparisons where numerical literals fall outside declared or observed column ranges."""
        warnings: List[str] = []
        structured_items: List[SemanticWarningItem] = []
        patterns: List[str] = []
        recs: List[str] = []

        # Map column metadata: (table_lower, col_lower) -> ColumnMetadata
        col_lookup: Dict[Tuple[str, str], Any] = {}
        # Also by col_lower if unique across tables
        col_by_name: Dict[str, List[Tuple[str, Any]]] = {}

        for table in schema.tables:
            t_name = table.name.lower()
            for col in table.columns:
                c_name = col.name.lower()
                col_lookup[(t_name, c_name)] = col
                col_by_name.setdefault(c_name, []).append((t_name, col))

        # Build alias map
        alias_map: Dict[str, str] = {}
        for tbl in ast.find_all(exp.Table):
            if tbl.name:
                t_lower = tbl.name.lower()
                alias_map[t_lower] = t_lower
                if tbl.alias:
                    alias_map[tbl.alias.lower()] = t_lower

        # Inspect binary comparison operations
        comparison_types = (exp.GT, exp.GTE, exp.LT, exp.LTE, exp.EQ)
        for comp in ast.find_all(*comparison_types):
            left = comp.left
            right = comp.right

            col_node: Optional[exp.Column] = None
            lit_node: Optional[exp.Literal] = None
            col_on_left = True

            if isinstance(left, exp.Column) and isinstance(right, exp.Literal) and right.is_number:
                col_node = left
                lit_node = right
                col_on_left = True
            elif isinstance(right, exp.Column) and isinstance(left, exp.Literal) and left.is_number:
                col_node = right
                lit_node = left
                col_on_left = False

            if not col_node or not lit_node:
                continue

            try:
                num_val = float(lit_node.this)
            except (ValueError, TypeError):
                continue

            c_name = col_node.name.lower()
            t_qual = col_node.table.lower() if col_node.table else None

            # Resolve table
            target_col_meta = None
            resolved_tbl_name = ""

            if t_qual and t_qual in alias_map:
                real_tbl = alias_map[t_qual]
                if (real_tbl, c_name) in col_lookup:
                    target_col_meta = col_lookup[(real_tbl, c_name)]
                    resolved_tbl_name = real_tbl
            elif not t_qual:
                candidates = col_by_name.get(c_name, [])
                if len(candidates) == 1:
                    resolved_tbl_name, target_col_meta = candidates[0]
                elif len(candidates) > 1:
                    # Ambiguous column reference across tables, pick if only one table in query
                    tables_in_query = list(alias_map.values())
                    for c_tbl, c_meta in candidates:
                        if c_tbl in tables_in_query:
                            resolved_tbl_name = c_tbl
                            target_col_meta = c_meta
                            break

            if not target_col_meta:
                continue

            # Determine comparison direction relative to column:
            # If col_on_left:
            #   col > num  =>  we are looking for values strictly above num_val
            #   col >= num =>  values >= num_val
            #   col < num  =>  values strictly below num_val
            #   col <= num =>  values <= num_val
            #   col = num  =>  values == num_val
            # If col on right:
            #   num < col  <=> col > num
            #   num <= col <=> col >= num
            #   num > col  <=> col < num
            #   num >= col <=> col <= num
            #   num = col  <=> col = num
            is_greater = (
                (col_on_left and isinstance(comp, (exp.GT, exp.GTE)))
                or (not col_on_left and isinstance(comp, (exp.LT, exp.LTE)))
            )
            is_less = (
                (col_on_left and isinstance(comp, (exp.LT, exp.LTE)))
                or (not col_on_left and isinstance(comp, (exp.GT, exp.GTE)))
            )
            is_eq = isinstance(comp, exp.EQ)

            max_v = target_col_meta.max_value
            min_v = target_col_meta.min_value
            bound_type = target_col_meta.value_bound_type or "observed"

            # Check upper bound violation: threshold exceeds maximum bound
            if max_v is not None and (is_greater or is_eq) and num_val > max_v:
                code = "POSSIBLE_SCALE_MISMATCH" if bound_type == "declared" else "OBSERVED_RANGE_DISCREPANCY"
                severity = "warning" if bound_type == "declared" else "advisory"
                qual_col = f"{resolved_tbl_name}.{target_col_meta.name}" if resolved_tbl_name else target_col_meta.name
                
                msg = (
                    f"The query compares '{qual_col}' against {num_val}, but the database specifies a "
                    f"{bound_type} maximum of {max_v}."
                )
                warnings.append(msg)
                patterns.append(code)
                evidence = {
                    "column": qual_col,
                    "constraint_type": bound_type,
                    "threshold": num_val,
                    "bound_max": max_v,
                    "bound_min": min_v,
                    "check_constraint": target_col_meta.check_constraint,
                }
                structured_items.append(
                    SemanticWarningItem(
                        code=code,
                        severity=severity,
                        message=msg,
                        evidence=evidence,
                    )
                )
                recs.append(
                    f"Verify the scale for '{qual_col}' (e.g. 4.0 GPA scale vs 10-point scale). "
                    f"Comparing against {num_val} will match zero records."
                )

            # Check lower bound violation: threshold is below minimum bound
            elif min_v is not None and (is_less or is_eq) and num_val < min_v:
                code = "POSSIBLE_SCALE_MISMATCH" if bound_type == "declared" else "OBSERVED_RANGE_DISCREPANCY"
                severity = "warning" if bound_type == "declared" else "advisory"
                qual_col = f"{resolved_tbl_name}.{target_col_meta.name}" if resolved_tbl_name else target_col_meta.name

                msg = (
                    f"The query compares '{qual_col}' against {num_val}, but the database specifies a "
                    f"{bound_type} minimum of {min_v}."
                )
                warnings.append(msg)
                patterns.append(code)
                evidence = {
                    "column": qual_col,
                    "constraint_type": bound_type,
                    "threshold": num_val,
                    "bound_min": min_v,
                    "bound_max": max_v,
                    "check_constraint": target_col_meta.check_constraint,
                }
                structured_items.append(
                    SemanticWarningItem(
                        code=code,
                        severity=severity,
                        message=msg,
                        evidence=evidence,
                    )
                )
                recs.append(
                    f"Verify the scale for '{qual_col}'. Comparing against {num_val} falls below the {bound_type} minimum of {min_v}."
                )

        return warnings, structured_items, patterns, recs

    def _check_multiplicative_joins(
        self,
        ast: exp.Select,
        schema: DatabaseSchemaResponse,
    ) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        """Detect when a 1-to-N child table is joined but none of its attributes are selected or aggregated,

        and no DISTINCT or GROUP BY is used, risking duplicate rows.
        Example: joining students with enrollments when only students columns are selected.
        """
        joins = ast.args.get("joins") or []
        if not joins:
            return None, None, None

        # Check if query already deduplicates
        has_distinct = bool(ast.args.get("distinct"))
        has_group_by = bool(ast.args.get("group"))
        if has_distinct or has_group_by:
            return None, None, None

        # Build map of table aliases to table names
        table_aliases: Dict[str, str] = {}
        for tbl in ast.find_all(exp.Table):
            if tbl.name:
                tname = tbl.name.lower()
                table_aliases[tname] = tname
                if tbl.alias:
                    table_aliases[tbl.alias.lower()] = tname

        # Build foreign-key relationship map from schema:
        # child_table -> (parent_table, foreign_key_col)
        child_to_parent: Dict[Tuple[str, str], str] = {}
        for rel in schema.relationships:
            child = rel.source_table.lower()
            parent = rel.target_table.lower()
            child_to_parent[(child, parent)] = rel.source_column.lower()

        # Extract columns projected in the SELECT expressions
        projected_expressions = ast.expressions or []
        projected_columns: Set[Tuple[str, str]] = set()  # (table_or_alias, col_name)

        for expr in projected_expressions:
            for col in expr.find_all(exp.Column):
                table_qual = col.table.lower() if col.table else ""
                col_name = col.name.lower() if col.name else ""
                projected_columns.add((table_qual, col_name))

        # Check each joined table
        for j in joins:
            for tbl_node in j.find_all(exp.Table):
                joined_tbl_name = (tbl_node.name or "").lower()
                joined_alias = (tbl_node.alias or tbl_node.name or "").lower()

                # Check if this joined table is a child of any other table in the query
                for other_alias, other_tbl_name in table_aliases.items():
                    if other_alias == joined_alias:
                        continue

                    # If joined table is a child of other table (1-to-N)
                    if (joined_tbl_name, other_tbl_name) in child_to_parent:
                        fk_col = child_to_parent[(joined_tbl_name, other_tbl_name)]

                        # Check if any projected column comes from joined child table
                        child_cols_projected = [
                            col_name
                            for (t_qual, col_name) in projected_columns
                            if (t_qual == joined_alias or (not t_qual and t_qual == joined_tbl_name))
                            and col_name != fk_col  # Projection of other attributes
                        ]

                        # Check if any aggregate functions use child columns
                        has_child_aggregation = False
                        for expr in projected_expressions:
                            if expr.find(exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max):
                                for col in expr.find_all(exp.Column):
                                    if col.table and col.table.lower() == joined_alias:
                                        has_child_aggregation = True

                        # If no child attributes are projected and no child aggregation, this is an unnecessary multiplicative join!
                        if not child_cols_projected and not has_child_aggregation:
                            warning_msg = (
                                f"Potentially multiplicative JOIN detected: Table '{joined_tbl_name}' "
                                f"is joined with '{other_tbl_name}', but no columns from '{joined_tbl_name}' "
                                f"are projected or aggregated, and DISTINCT is not used. "
                                f"If '{other_tbl_name}' has multiple '{joined_tbl_name}' records, duplicate rows will occur."
                            )
                            rec_msg = (
                                f"Remove the unnecessary JOIN on '{joined_tbl_name}', "
                                f"or add DISTINCT if unique '{other_tbl_name}' records are intended."
                            )
                            evidence = {
                                "child_table": joined_tbl_name,
                                "parent_table": other_tbl_name,
                                "foreign_key": fk_col,
                            }
                            return warning_msg, rec_msg, evidence

        return None, None, None

    def _check_cartesian_products(self, ast: exp.Expression) -> Optional[str]:
        """Check for tables joined without an ON condition or matching WHERE filter."""
        joins = ast.args.get("joins") or []
        for j in joins:
            on_clause = j.args.get("on")
            kind = (j.args.get("kind") or "").upper()
            if kind == "CROSS" or (not on_clause and "NATURAL" not in kind):
                return "Join lacks an ON condition, creating a potential Cartesian product."
        return None


_semantic_analyzer_instance: Optional[SemanticAnalyzer] = None


def get_semantic_analyzer() -> SemanticAnalyzer:
    """Return singleton SemanticAnalyzer instance."""
    global _semantic_analyzer_instance
    if _semantic_analyzer_instance is None:
        _semantic_analyzer_instance = SemanticAnalyzer(dialect="sqlite")
    return _semantic_analyzer_instance

