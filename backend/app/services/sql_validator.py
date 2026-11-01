"""SQL AST inspection and static security validation service using SQLGlot.

Performs:
- SQLite dialect parsing
- AST syntax validation
- Rejection of multiple statements, DDL, DML, PRAGMA, ATTACH, transactions
- Recursive search for forbidden expressions inside subqueries, CTEs, and unions
- Schema reference verification against introspected SQLite tables and columns
- Handling of table aliases and CTE scopes
- Categorized status reporting: valid, invalid, unsafe, schema_mismatch, unsupported, unverified
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.core.logging import get_logger
from app.schemas.ai import SQLValidationResult, ValidationStatus
from app.schemas.database import DatabaseSchemaResponse

logger = get_logger("sql_validator")

# Forbidden AST types that violate read-only query policy
FORBIDDEN_AST_NODES: Tuple[Any, ...] = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Create,
    exp.Alter,
    exp.Command,
    exp.Transaction,
    exp.Commit,
    exp.Rollback,
    exp.Attach,
    exp.Detach,
    exp.Pragma,
    exp.TruncateTable,
    exp.Grant,
    exp.Revoke,
)

# Forbidden functions that could compromise system integrity
DANGEROUS_FUNCTIONS: Set[str] = {
    "load_extension",
    "writefile",
    "readfile",
    "edit",
}

# System metadata tables in SQLite
INTERNAL_SQLITE_TABLES: Set[str] = {
    "sqlite_master",
    "sqlite_schema",
    "sqlite_temp_master",
    "sqlite_temp_schema",
    "sqlite_sequence",
    "sqlite_stat1",
    "sqlite_stat4",
}


class SQLValidator:
    """Validates generated SQL queries using SQLGlot static AST inspection."""

    def __init__(self, dialect: str = "sqlite"):
        self.dialect = dialect

    def validate(
        self,
        sql: str,
        schema: Optional[DatabaseSchemaResponse] = None,
    ) -> SQLValidationResult:
        """Statically inspect and validate a SQL query against security policies and schema."""
        raw_sql = sql.strip()

        # 1. Check for empty or whitespace-only input
        if not raw_sql:
            return SQLValidationResult(
                status="invalid",
                is_valid=False,
                syntax_valid=False,
                schema_valid=False,
                issues=["Query is empty or contains only whitespace."],
            )

        # 2. Check for multiple statements
        try:
            statements = sqlglot.parse(raw_sql, read=self.dialect)
        except ParseError as e:
            return SQLValidationResult(
                status="invalid",
                is_valid=False,
                syntax_valid=False,
                schema_valid=False,
                issues=[f"SQLite syntax error: {str(e)}"],
            )
        except Exception as e:
            return SQLValidationResult(
                status="invalid",
                is_valid=False,
                syntax_valid=False,
                schema_valid=False,
                issues=[f"Failed to parse SQL query: {str(e)}"],
            )

        # Disallow empty statement parse or multiple statements separated by semicolons
        valid_statements = [s for s in statements if s is not None]
        if not valid_statements:
            return SQLValidationResult(
                status="invalid",
                is_valid=False,
                syntax_valid=False,
                schema_valid=False,
                issues=["No valid SQL statements found."],
            )

        if len(valid_statements) > 1:
            return SQLValidationResult(
                status="unsafe",
                is_valid=False,
                syntax_valid=True,
                schema_valid=False,
                issues=[
                    f"Multiple SQL statements detected ({len(valid_statements)} statements). "
                    "Only single read-only statements are permitted."
                ],
            )

        ast = valid_statements[0]
        ast_type_name = type(ast).__name__

        # 3. Security Inspection: Check AST nodes for DDL, DML, and dangerous constructs
        unsafe_issues: List[str] = []

        # Check top-level statement type
        if not isinstance(ast, (exp.Select, exp.Union)):
            unsafe_issues.append(
                f"Forbidden statement type: '{ast_type_name}'. Only SELECT queries are permitted."
            )

        # Recursively walk the entire AST (including CTEs, subqueries, expressions)
        for node in ast.walk():
            node_type = type(node)
            if issubclass(node_type, FORBIDDEN_AST_NODES):
                unsafe_issues.append(
                    f"Forbidden operation '{node_type.__name__}' detected within SQL structure."
                )

            # Check function calls for dangerous extensions
            if isinstance(node, (exp.Anonymous, exp.Func)):
                func_name = ""
                raw_name = getattr(node, "name", None)
                if isinstance(raw_name, str):
                    func_name = raw_name
                elif hasattr(node, "key") and isinstance(node.key, str):
                    func_name = node.key

                if func_name and func_name.lower() in DANGEROUS_FUNCTIONS:
                    unsafe_issues.append(
                        f"Forbidden function '{func_name}' is not permitted."
                    )

        if unsafe_issues:
            return SQLValidationResult(
                status="unsafe",
                is_valid=False,
                syntax_valid=True,
                schema_valid=False,
                ast_type=ast_type_name,
                issues=unsafe_issues,
            )

        # 4. Extract CTE aliases to avoid false positive schema mismatches
        cte_aliases: Set[str] = set()
        for cte in ast.find_all(exp.CTE):
            alias = cte.alias
            if alias:
                cte_aliases.add(alias.lower())

        # 5. Extract referenced tables
        tables_referenced: List[str] = []
        internal_tables_found: List[str] = []

        for table_node in ast.find_all(exp.Table):
            t_name = table_node.name
            if t_name and t_name.strip():
                clean_name = t_name.strip().strip('"').strip("`").strip("'")
                # Do not register CTE names as physical tables
                if clean_name.lower() not in cte_aliases:
                    if clean_name not in tables_referenced:
                        tables_referenced.append(clean_name)
                    if clean_name.lower() in INTERNAL_SQLITE_TABLES:
                        internal_tables_found.append(clean_name)

        if internal_tables_found:
            return SQLValidationResult(
                status="unsafe",
                is_valid=False,
                syntax_valid=True,
                schema_valid=False,
                ast_type=ast_type_name,
                tables_referenced=tables_referenced,
                issues=[
                    f"Direct access to internal SQLite metadata tables is forbidden: {', '.join(internal_tables_found)}"
                ],
            )

        # 6. Extract referenced columns
        columns_referenced: List[str] = []
        for col_node in ast.find_all(exp.Column):
            c_name = col_node.name
            if c_name and c_name.strip() and c_name != "*":
                clean_c = c_name.strip().strip('"').strip("`").strip("'")
                table_qualifier = col_node.table
                full_col = f"{table_qualifier}.{clean_c}" if table_qualifier else clean_c
                if full_col not in columns_referenced:
                    columns_referenced.append(full_col)

        # 7. Schema Validation (if schema is provided)
        if schema is None:
            # No schema provided for verification
            return SQLValidationResult(
                status="unverified",
                is_valid=True,
                syntax_valid=True,
                schema_valid=False,
                ast_type=ast_type_name,
                tables_referenced=tables_referenced,
                columns_referenced=columns_referenced,
                warnings=["Query syntax is valid, but no database schema was provided to verify object references."],
            )

        # Build schema lookup maps
        known_tables: Dict[str, Set[str]] = {}
        all_known_columns: Set[str] = set()

        for t in schema.tables:
            t_lower = t.name.lower()
            cols = {c.name.lower() for c in t.columns}
            known_tables[t_lower] = cols
            all_known_columns.update(cols)

        schema_issues: List[str] = []
        schema_warnings: List[str] = []

        # Validate tables against schema
        for tbl in tables_referenced:
            if tbl.lower() not in known_tables:
                schema_issues.append(
                    f"Referenced table '{tbl}' does not exist in database schema '{schema.database.name}'."
                )

        if schema_issues:
            return SQLValidationResult(
                status="schema_mismatch",
                is_valid=False,
                syntax_valid=True,
                schema_valid=False,
                ast_type=ast_type_name,
                tables_referenced=tables_referenced,
                columns_referenced=columns_referenced,
                issues=schema_issues,
            )

        # Validate columns where identifiable
        # (qualified columns like table.col or alias.col)
        # Build table alias map from query
        table_aliases: Dict[str, str] = {}
        for tbl_node in ast.find_all(exp.Table):
            t_name = tbl_node.name
            t_alias = tbl_node.alias
            if t_name and t_alias:
                table_aliases[t_alias.lower()] = t_name.lower()

        unresolved_columns: List[str] = []
        for col_ref in columns_referenced:
            if "." in col_ref:
                qualifier, col_name = col_ref.split(".", 1)
                qual_lower = qualifier.lower()
                col_lower = col_name.lower()

                # Check if qualifier is a known table or alias
                resolved_table = table_aliases.get(qual_lower, qual_lower)
                if resolved_table in known_tables:
                    if col_lower not in known_tables[resolved_table]:
                        schema_issues.append(
                            f"Column '{col_name}' does not exist in table '{resolved_table}'."
                        )
                elif qual_lower in cte_aliases:
                    # Column from CTE; cannot statically resolve without running CTE
                    pass
                else:
                    schema_warnings.append(
                        f"Could not resolve table qualifier '{qualifier}' for column '{col_name}'."
                    )
            else:
                # Unqualified column
                col_lower = col_ref.lower()
                # If only 1 table is referenced, check if column belongs to it
                if len(tables_referenced) == 1:
                    single_tbl = tables_referenced[0].lower()
                    if single_tbl in known_tables and col_lower not in known_tables[single_tbl]:
                        schema_issues.append(
                            f"Column '{col_ref}' does not exist in table '{tables_referenced[0]}'."
                        )
                else:
                    # Multi-table query: check if column exists in ANY of the referenced tables
                    found = False
                    for t_name in tables_referenced:
                        if t_name.lower() in known_tables and col_lower in known_tables[t_name.lower()]:
                            found = True
                            break
                    if not found and col_lower not in all_known_columns and col_lower != "*":
                        unresolved_columns.append(col_ref)

        if schema_issues:
            return SQLValidationResult(
                status="schema_mismatch",
                is_valid=False,
                syntax_valid=True,
                schema_valid=False,
                ast_type=ast_type_name,
                tables_referenced=tables_referenced,
                columns_referenced=columns_referenced,
                issues=schema_issues,
                warnings=schema_warnings,
            )

        if unresolved_columns:
            schema_warnings.append(
                f"Unresolved column references in multi-table scope: {', '.join(unresolved_columns)}."
            )

        return SQLValidationResult(
            status="valid",
            is_valid=True,
            syntax_valid=True,
            schema_valid=True,
            ast_type=ast_type_name,
            tables_referenced=tables_referenced,
            columns_referenced=columns_referenced,
            issues=[],
            warnings=schema_warnings,
        )


_sql_validator_instance: Optional[SQLValidator] = None


def get_sql_validator() -> SQLValidator:
    """Return singleton SQL validator instance."""
    global _sql_validator_instance
    if _sql_validator_instance is None:
        _sql_validator_instance = SQLValidator(dialect="sqlite")
    return _sql_validator_instance
