from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Any

from app.models.intent import QueryIntent


class SessionRepository:
    """Small local repository; replaceable with Redis/PostgreSQL in production."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._lock = RLock()

    def _read(self) -> dict[str, QueryIntent]:
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            return {key: QueryIntent.model_validate(value) for key, value in payload.items()}
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return {}

    def _write(self, sessions: dict[str, QueryIntent]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        payload = {key: value.model_dump(mode="json") for key, value in sessions.items()}
        temporary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temporary_path.replace(self.path)

    def set(self, session_id: str, intent: QueryIntent) -> None:
        with self._lock:
            sessions = self._read()
            sessions[session_id] = intent
            self._write(sessions)

    def get(self, session_id: str) -> QueryIntent | None:
        with self._lock:
            return self._read().get(session_id)

    def update(self, session_id: str, **updates: Any) -> QueryIntent | None:
        with self._lock:
            sessions = self._read()
            current = sessions.get(session_id)
            if current is None:
                return None
            updated = current.model_copy(update=updates)
            sessions[session_id] = updated
            self._write(sessions)
            return updated


from app.config import settings

SESSION_REPOSITORY = SessionRepository(settings.session_store_path)


def set_session(session_id: str, intent: QueryIntent) -> None:
    SESSION_REPOSITORY.set(session_id, intent)


def get_session(session_id: str) -> QueryIntent | None:
    return SESSION_REPOSITORY.get(session_id)


def update_session(session_id: str, **updates: Any) -> QueryIntent | None:
    return SESSION_REPOSITORY.update(session_id, **updates)
