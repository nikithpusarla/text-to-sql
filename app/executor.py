from __future__ import annotations

from typing import Any

from app.db.connection import get_connection


def execute_sql(sql: str) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = '5s'")
            cur.execute(sql)
            columns = [description.name for description in cur.description or []]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
