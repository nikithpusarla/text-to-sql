from __future__ import annotations

from pydantic import BaseModel


class ClarificationQuestion(BaseModel):
    slot_name: str
    question_text: str
    options: list[str]


class ClarificationResponse(BaseModel):
    session_id: str
    slot_name: str
    chosen_value: str
