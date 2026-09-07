from pydantic import ValidationError
import pytest

from app.models.intent import MetricSlot, ResolvedIntent, SlotStatus
from app.engine.intent_parser import parse_without_llm


def test_parser_returns_pydantic_intent():
    intent = parse_without_llm("show customers from the last 30 days")
    assert intent.raw_query.startswith("show customers")
    assert intent.time_range.value == "last_30_days"


def test_resolved_intent_rejects_unresolved_slots():
    with pytest.raises(ValidationError):
        ResolvedIntent(
            raw_query="best customer",
            entity=MetricSlot(status=SlotStatus.RESOLVED, value="customer"),
            metric=MetricSlot(status=SlotStatus.AMBIGUOUS),
            time_range=MetricSlot(status=SlotStatus.RESOLVED, value="all_time"),
        )
