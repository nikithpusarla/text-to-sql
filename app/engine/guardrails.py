from __future__ import annotations

from collections.abc import Mapping

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError


class SQLValidationError(ValueError):
    """Raised when generated SQL violates the read-only query contract."""


def validate_and_limit(sql: str, schema: Mapping[str, list[str]], limit: int = 100) -> str:
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except ParseError as exc:
        raise SQLValidationError(f"Invalid SQL: {exc}") from exc

    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise SQLValidationError("Only one SELECT statement is allowed")

    statement = statements[0]
    known_tables = set(schema)
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
