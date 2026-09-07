from __future__ import annotations

import json
from typing import Any

from app.db.connection import get_connection


def get_schema_summary() -> dict[str, list[str]]:
    query = """
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()

    schema: dict[str, list[str]] = {}
    for table_name, column_name in rows:
        schema.setdefault(table_name, []).append(column_name)

    return schema


def print_schema_summary() -> None:
    schema = get_schema_summary()
    print(json.dumps(schema, indent=2, sort_keys=True))


if __name__ == "__main__":
    print_schema_summary()
