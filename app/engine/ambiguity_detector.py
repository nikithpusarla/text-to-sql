from __future__ import annotations

from app.glossary.loader import candidates_for_entity, match_metric_candidates
from app.models.intent import MetricSlot, QueryIntent, SlotStatus


def detect_ambiguity(intent: QueryIntent) -> dict[str, list[str]]:
    unresolved: dict[str, list[str]] = {}
    for slot_name in ["entity", "metric", "time_range"]:
        slot = getattr(intent, slot_name)
        if slot.status in {SlotStatus.AMBIGUOUS, SlotStatus.MISSING}:
            if slot_name == "metric":
                candidates = match_metric_candidates(intent.raw_query)
                if not candidates and intent.entity.value:
                    candidates = candidates_for_entity(intent.entity.value)
                if candidates:
                    slot.candidates = [item.get("name", "") for item in candidates]
            unresolved[slot_name] = slot.candidates or []
    return unresolved
