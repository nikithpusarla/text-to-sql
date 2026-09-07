from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.clarification import ClarificationQuestion
from app.models.sql_result import SQLGenerationResult


class QueryRequest(BaseModel):
    query: str = Field(min_length=1)
    session_id: str | None = None


class QueryResponse(BaseModel):
    session_id: str
    questions: list[ClarificationQuestion] = []
    result: SQLGenerationResult | None = None


class ExecuteRequest(BaseModel):
    sql: str = Field(min_length=1)
