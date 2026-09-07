from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, model_validator


class SlotStatus(str, Enum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    MISSING = "missing"


class MetricSlot(BaseModel):
    status: SlotStatus
    value: Optional[str] = None
    candidates: list[str] = []
    sql_expr: Optional[str] = None


class QueryIntent(BaseModel):
    raw_query: str
    entity: MetricSlot
    metric: MetricSlot
    time_range: MetricSlot
    top_n: Optional[int] = None
    filters: list[str] = []


class ResolvedIntent(QueryIntent):
    """All slots guaranteed RESOLVED; validation is enforced at construction time."""

    @model_validator(mode="after")
    def ensure_all_slots_resolved(self) -> "ResolvedIntent":
        slots = [self.entity, self.metric, self.time_range]
        for slot in slots:
            if slot.status != SlotStatus.RESOLVED:
                raise ValueError(f"Slot {slot!r} is not resolved")
        return self
