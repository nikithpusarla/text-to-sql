from __future__ import annotations

from pydantic import BaseModel


class SQLGenerationResult(BaseModel):
    sql: str
    explanation: str
    tables_used: list[str]
