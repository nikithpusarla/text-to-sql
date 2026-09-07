from __future__ import annotations

from typing import Any

from app.models.intent import QueryIntent


SESSION_STORE: dict[str, QueryIntent] = {}


def set_session(session_id: str, intent: QueryIntent) -> None:
    SESSION_STORE[session_id] = intent


def get_session(session_id: str) -> QueryIntent | None:
    return SESSION_STORE.get(session_id)


def update_session(session_id: str, **updates: Any) -> QueryIntent | None:
    current = SESSION_STORE.get(session_id)
    if current is None:
        return None
    updated = current.model_copy(update=updates)
    SESSION_STORE[session_id] = updated
    return updated
