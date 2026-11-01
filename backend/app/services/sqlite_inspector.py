"""SQLite schema introspection, security authorizer, and schema context generator.

Extracts table definitions, column types, primary keys (including composite keys),
foreign key constraints, and indices using SQLite metadata PRAGMAs.
Applies strict read-only URI mode and SQLite authorizer callbacks to prevent unsafe execution.
"""

import math
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Set, Tuple

from app.core.exceptions import SchemaSenseException
from app.core.logging import get_logger
from app.schemas.database import (
    ColumnMetadata,
    DatabaseInfo,
    DatabaseSchemaResponse,
    ForeignKeyMetadata,
    IndexMetadata,
    RelationshipMetadata,
    SchemaContextResponse,
    TableMetadata,
)

logger = get_logger("sqlite_inspector")


def quote_identifier(identifier: str) -> str:
    """Safely quote a SQLite identifier (table or column name)."""
    escaped = identifier.replace('"', '""')
    return f'"{escaped}"'


def is_safe_identifier(identifier: str) -> bool:
    """Validate that an identifier contains no control characters, null bytes, or semicolons."""
    if not identifier or len(identifier) > 128:
        return False
    if "\x00" in identifier or ";" in identifier or "--" in identifier:
        return False
    return True


def sqlite_authorizer_read_only(action_code: int, arg1: Any, arg2: Any, db_name: Any, trigger_name: Any) -> int:
    """SQLite authorizer callback that enforces strict read-only access.

    Returns:
        SQLITE_OK (0) for allowed read actions.
        SQLITE_DENY (1) for all write/DDL/attach/extension actions.
    """
    # Allowed read operations in SQLite
    # 20: SQLITE_SELECT, 21: SQLITE_READ, 19: SQLITE_PRAGMA, 31: SQLITE_FUNCTION
    ALLOWED_ACTIONS = {
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_PRAGMA,
        21,  # SQLITE_READ
        20,  # SQLITE_SELECT
        19,  # SQLITE_PRAGMA
        31,  # SQLITE_FUNCTION
    }

    if action_code in ALLOWED_ACTIONS:
        # Extra check: disallow modifying pragmas
        if action_code == sqlite3.SQLITE_PRAGMA:
            pragma_name = (str(arg1) if arg1 else "").lower()
            # Pragmas that are read-only and safe for inspection
            safe_pragmas = {
                "table_info",
                "table_xinfo",
                "foreign_key_list",
                "index_list",
                "index_info",
                "index_xinfo",
                "foreign_keys",
                "integrity_check",
                "quick_check",
                "database_list",
                "table_list",
            }
            if pragma_name in safe_pragmas:
                return sqlite3.SQLITE_OK
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    # Deny all other actions (INSERT, UPDATE, DELETE, ATTACH, DETACH, ALTER, DROP, CREATE)
    return sqlite3.SQLITE_DENY


@contextmanager
def get_read_only_connection(db_path: Path, timeout: float = 5.0) -> Generator[sqlite3.Connection, None, None]:
    """Context manager that opens a SQLite connection in read-only URI mode with authorizer."""
    resolved_path = Path(db_path).resolve()
    if not resolved_path.exists():
        raise FileNotFoundError(f"Database file not found: {resolved_path}")

    # Use URI mode with mode=ro for kernel-level read-only guarantee
    uri_path = resolved_path.as_posix()
    conn_uri = f"file:{uri_path}?mode=ro"

    conn = sqlite3.connect(
        conn_uri,
        uri=True,
        timeout=timeout,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row

    # Defensive configuration
    try:
        conn.set_authorizer(sqlite_authorizer_read_only)
    except Exception as e:
        logger.warning(f"Could not set SQLite authorizer: {e}")

    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass


def parse_check_constraints(ddl: Optional[str]) -> Dict[str, Dict[str, Any]]:
    """Parse column-level and table-level CHECK constraints from SQLite DDL.

    Extracts declared constraints and ranges (e.g. CHECK(gpa >= 0.0 AND gpa <= 4.0)).
    """
    if not ddl:
        return {}

    import re

    results: Dict[str, Dict[str, Any]] = {}

    check_matches = re.finditer(r"CHECK\s*\((.*?)\)", ddl, re.IGNORECASE | re.DOTALL)
    for m in check_matches:
        expr = m.group(1).strip()
        # Look for range: col >= min AND col <= max
        range_match = re.search(
            r"([a-zA-Z0-9_]+)\s*(?:>=?|>)\s*([0-9.]+)\s+(?:AND|and)\s+\1\s*(?:<=?|<)\s*([0-9.]+)",
            expr,
            re.IGNORECASE,
        )
        if range_match:
            c_name = range_match.group(1).lower()
            min_v = float(range_match.group(2))
            max_v = float(range_match.group(3))
            results[c_name] = {
                "constraint": expr,
                "min_value": min_v,
                "max_value": max_v,
                "bound_type": "declared",
            }
            continue

        # Reverse range: col <= max AND col >= min
        rev_range_match = re.search(
            r"([a-zA-Z0-9_]+)\s*(?:<=?|<)\s*([0-9.]+)\s+(?:AND|and)\s+\1\s*(?:>=?|>)\s*([0-9.]+)",
            expr,
            re.IGNORECASE,
        )
        if rev_range_match:
            c_name = rev_range_match.group(1).lower()
            max_v = float(rev_range_match.group(2))
            min_v = float(rev_range_match.group(3))
            results[c_name] = {
                "constraint": expr,
                "min_value": min_v,
                "max_value": max_v,
                "bound_type": "declared",
            }
            continue

        # Single lower bound
        min_only_match = re.search(r"([a-zA-Z0-9_]+)\s*(?:>=?|>)\s*([0-9.]+)", expr, re.IGNORECASE)
        if min_only_match:
            c_name = min_only_match.group(1).lower()
            results[c_name] = {
                "constraint": expr,
                "min_value": float(min_only_match.group(2)),
                "max_value": None,
                "bound_type": "declared",
            }
            continue

        # Single upper bound
        max_only_match = re.search(r"([a-zA-Z0-9_]+)\s*(?:<=?|<)\s*([0-9.]+)", expr, re.IGNORECASE)
        if max_only_match:
            c_name = max_only_match.group(1).lower()
            results[c_name] = {
                "constraint": expr,
                "min_value": None,
                "max_value": float(max_only_match.group(2)),
                "bound_type": "declared",
            }
            continue

    return results


def introspect_sqlite_database(db_path: Path, db_info: DatabaseInfo) -> DatabaseSchemaResponse:
    """Introspect tables, columns, constraints, and relationships of a SQLite database.

    Args:
        db_path: Path to the SQLite file.
        db_info: Registered database metadata.

    Returns:
        DatabaseSchemaResponse with full metadata.
    """
    resolved_path = Path(db_path).resolve()
    if not resolved_path.exists():
        raise FileNotFoundError(f"Database file does not exist: {resolved_path}")

    tables: List[TableMetadata] = []
    relationships: List[RelationshipMetadata] = []
    total_columns = 0

    with get_read_only_connection(resolved_path) as conn:
        cursor = conn.cursor()

        # 1. Fetch all user tables and views along with creation DDL sql
        cursor.execute("""
            SELECT name, type, sql
            FROM sqlite_master
            WHERE type IN ('table', 'view')
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name ASC;
        """)
        db_objects = cursor.fetchall()

        for obj in db_objects:
            obj_name = obj["name"]
            obj_type = obj["type"]
            table_ddl = obj["sql"] or ""

            if not is_safe_identifier(obj_name):
                logger.warning(f"Skipping table with unsafe identifier: {obj_name}")
                continue

            quoted_name = quote_identifier(obj_name)
            check_constraints_map = parse_check_constraints(table_ddl)

            # 2. Extract column metadata via PRAGMA table_xinfo (fallback to table_info)
            try:
                cursor.execute(f"PRAGMA table_xinfo({quoted_name});")
                raw_cols = cursor.fetchall()
            except Exception:
                cursor.execute(f"PRAGMA table_info({quoted_name});")
                raw_cols = cursor.fetchall()

            columns: List[ColumnMetadata] = []
            primary_keys: List[str] = []

            for col in raw_cols:
                col_name = col["name"]
                col_type = col["type"] or "TEXT"
                notnull = bool(col["notnull"])
                dflt_val = str(col["dflt_value"]) if col["dflt_value"] is not None else None
                pk_val = col["pk"]

                is_pk = pk_val > 0
                pk_pos = pk_val if is_pk else None
                if is_pk:
                    primary_keys.append(col_name)

                check_info = check_constraints_map.get(col_name.lower(), {})

                columns.append(
                    ColumnMetadata(
                        name=col_name,
                        data_type=col_type.upper(),
                        nullable=not notnull,
                        primary_key=is_pk,
                        pk_position=pk_pos,
                        default_value=dflt_val,
                        check_constraint=check_info.get("constraint"),
                        min_value=check_info.get("min_value"),
                        max_value=check_info.get("max_value"),
                        value_bound_type=check_info.get("bound_type"),
                    )
                )

            total_columns += len(columns)

            # 3. Extract Foreign Keys via PRAGMA foreign_key_list
            cursor.execute(f"PRAGMA foreign_key_list({quoted_name});")
            raw_fks = cursor.fetchall()

            foreign_keys: List[ForeignKeyMetadata] = []
            # Group composite foreign keys by id
            fks_by_id: Dict[int, List[sqlite3.Row]] = {}
            for fk in raw_fks:
                cid = fk["id"]
                if cid not in fks_by_id:
                    fks_by_id[cid] = []
                fks_by_id[cid].append(fk)

                from_col = fk["from"]
                to_table = fk["table"]
                to_col = fk["to"]

                foreign_keys.append(
                    ForeignKeyMetadata(
                        constraint_id=cid,
                        from_column=from_col,
                        to_table=to_table,
                        to_column=to_col,
                        on_update=fk["on_update"] or "NO ACTION",
                        on_delete=fk["on_delete"] or "NO ACTION",
                    )
                )

                # Mark column as foreign key in column list
                for c in columns:
                    if c.name == from_col:
                        c.is_foreign_key = True
                        c.fk_target_table = to_table
                        c.fk_target_column = to_col

            # 4. Extract Indices via PRAGMA index_list
            indices: List[IndexMetadata] = []
            try:
                cursor.execute(f"PRAGMA index_list({quoted_name});")
                raw_indices = cursor.fetchall()
                for idx in raw_indices:
                    idx_name = idx["name"]
                    is_unique = bool(idx["unique"])
                    # Get indexed columns
                    quoted_idx = quote_identifier(idx_name)
                    cursor.execute(f"PRAGMA index_info({quoted_idx});")
                    idx_cols = [r["name"] for r in cursor.fetchall() if r["name"]]
                    indices.append(
                        IndexMetadata(
                            name=idx_name,
                            columns=idx_cols,
                            unique=is_unique,
                        )
                    )
            except Exception as e:
                logger.debug(f"Index fetch failed for {obj_name}: {e}")

            # 5. Get Row Count safely
            row_count = 0
            if obj_type == "table":
                try:
                    cursor.execute(f"SELECT COUNT(*) AS total FROM {quoted_name};")
                    row_count = cursor.fetchone()["total"]
                except Exception as e:
                    logger.debug(f"Could not count rows for {obj_name}: {e}")

            tables.append(
                TableMetadata(
                    name=obj_name,
                    type=obj_type,
                    column_count=len(columns),
                    row_count=row_count,
                    columns=columns,
                    primary_keys=primary_keys,
                    foreign_keys=foreign_keys,
                    indices=indices,
                )
            )

            # Register discovered relationships
            for cid, fk_rows in fks_by_id.items():
                if len(fk_rows) == 1:
                    row = fk_rows[0]
                    rel_id = f"{obj_name}.{row['from']}->{row['table']}.{row['to']}"
                    relationships.append(
                        RelationshipMetadata(
                            id=rel_id,
                            source_table=obj_name,
                            source_column=row["from"],
                            target_table=row["table"],
                            target_column=row["to"],
                            is_composite=False,
                        )
                    )
                else:
                    # Composite foreign key
                    pairs = [{"from": r["from"], "to": r["to"]} for r in fk_rows]
                    rel_id = f"{obj_name}->{fk_rows[0]['table']}:{cid}"
                    relationships.append(
                        RelationshipMetadata(
                            id=rel_id,
                            source_table=obj_name,
                            source_column=",".join(r["from"] for r in fk_rows),
                            target_table=fk_rows[0]["table"],
                            target_column=",".join(r["to"] for r in fk_rows),
                            is_composite=True,
                            composite_pairs=pairs,
                        )
                    )

    # Sort tables alphabetically for deterministic output
    tables.sort(key=lambda t: t.name)
    relationships.sort(key=lambda r: r.id)

    return DatabaseSchemaResponse(
        database=db_info,
        dialect="sqlite",
        tables=tables,
        relationships=relationships,
        total_tables=len(tables),
        total_columns=total_columns,
        total_relationships=len(relationships),
    )


def generate_deterministic_schema_context(
    schema: DatabaseSchemaResponse,
) -> SchemaContextResponse:
    """Serialize the introspected schema into a compact, deterministic LLM-ready prompt context."""
    lines: List[str] = [
        f"### Database: {schema.database.name} ({schema.dialect})",
        f"Description: {schema.database.description or 'Relational SQLite Database'}",
        f"Total Tables: {schema.total_tables} | Total Columns: {schema.total_columns}",
        "",
        "#### Tables & Columns Definition:",
    ]

    for table in schema.tables:
        lines.append(f"- **{table.name}** ({table.type}, {table.row_count} rows):")
        for col in table.columns:
            traits: List[str] = [col.data_type]
            if col.primary_key:
                if col.pk_position and col.pk_position > 1:
                    traits.append(f"PRIMARY KEY (pos {col.pk_position})")
                else:
                    traits.append("PRIMARY KEY")
            if not col.nullable:
                traits.append("NOT NULL")
            if col.default_value is not None:
                traits.append(f"DEFAULT {col.default_value}")
            if col.is_foreign_key and col.fk_target_table:
                traits.append(f"REFERENCES {col.fk_target_table}({col.fk_target_column})")
            if col.check_constraint:
                traits.append(f"CHECK({col.check_constraint})")
            elif col.min_value is not None and col.max_value is not None:
                traits.append(f"RANGE[{col.min_value}..{col.max_value}]")

            lines.append(f"    - `{col.name}`: {', '.join(traits)}")

    if schema.relationships:
        lines.append("")
        lines.append("#### Relational Foreign Key Graph:")
        for rel in schema.relationships:
            if rel.is_composite:
                pairs = ", ".join(f"{p['from']}={p['to']}" for p in (rel.composite_pairs or []))
                lines.append(f"  - `{rel.source_table}` -> `{rel.target_table}` [{pairs}]")
            else:
                lines.append(f"  - `{rel.source_table}.{rel.source_column}` -> `{rel.target_table}.{rel.target_column}`")

    prompt_context = "\n".join(lines)
    # Estimate tokens: standard approximation ~4 chars per token
    token_est = max(1, math.ceil(len(prompt_context) / 4))

    return SchemaContextResponse(
        database_id=schema.database.id,
        database_name=schema.database.name,
        dialect=schema.dialect,
        prompt_schema_context=prompt_context,
        token_estimate=token_est,
    )
