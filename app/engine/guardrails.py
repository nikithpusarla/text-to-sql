from __future__ import annotations

import re
from collections.abc import Mapping

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.config import settings


class SQLValidationError(ValueError):
    """Raised when generated SQL violates the read-only query contract."""


def validate_and_limit(
    sql: str,
    schema: Mapping[str, list[str]],
    limit: int = 100,
    *,
    max_length: int = settings.max_query_length,
    max_joins: int = settings.max_query_joins,
    max_functions: int = settings.max_query_functions,
) -> str:
    normalized = sql.strip()
    if not normalized:
        raise SQLValidationError("Query is empty")
    if len(normalized) > max_length:
        raise SQLValidationError(f"Query exceeds the {max_length}-character limit")
    if "--" in normalized or "/*" in normalized or "*/" in normalized:
        raise SQLValidationError("SQL comments are not allowed")
    if re.search(r"\bpg_sleep\s*\(", normalized, flags=re.IGNORECASE):
        raise SQLValidationError("Function pg_sleep is not allowed")
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except ParseError as exc:
        raise SQLValidationError(f"Invalid SQL: {exc}") from exc

    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise SQLValidationError("Only one SELECT statement is allowed")

    statement = statements[0]
    known_tables = set(schema)
    if len(list(statement.find_all(exp.Join))) > max_joins:
        raise SQLValidationError(f"Query exceeds the {max_joins}-join complexity limit")
    if len(list(statement.find_all(exp.Func))) > max_functions:
        raise SQLValidationError(f"Query exceeds the {max_functions}-function complexity limit")
    for table in statement.find_all(exp.Table):
        if table.db or table.catalog:
            raise SQLValidationError("System or cross-schema table access is not allowed")
    aliases: dict[str, str] = {}
    output_aliases = {alias.alias for alias in statement.find_all(exp.Alias)}
    for table in statement.find_all(exp.Table):
        table_name = table.name
        if table_name not in known_tables:
            raise SQLValidationError(f"Unknown table: {table_name}")
        alias = table.alias_or_name
        aliases[alias] = table_name

    for column in statement.find_all(exp.Column):
        table_name = column.table
        if table_name:
            resolved_table = aliases.get(table_name, table_name)
            if resolved_table not in known_tables:
                raise SQLValidationError(f"Unknown table: {table_name}")
            if column.name not in schema[resolved_table] and column.name != "*":
                raise SQLValidationError(f"Unknown column: {table_name}.{column.name}")
        elif column.name not in output_aliases and column.name != "*":
            if not any(column.name in columns for columns in schema.values()):
                raise SQLValidationError(f"Unknown column: {column.name}")

    if statement.args.get("limit") is None:
        statement = statement.limit(limit)
    return statement.sql(dialect="postgres")
