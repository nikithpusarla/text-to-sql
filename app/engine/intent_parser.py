from __future__ import annotations

import anthropic

from app.config import settings
from app.models.intent import MetricSlot, QueryIntent, SlotStatus


INTENT_TOOL = {
    "name": "set_query_intent",
    "description": "Extract query intent and mark uncertain slots ambiguous or missing.",
    "input_schema": QueryIntent.model_json_schema(),
}


def parse_with_llm(raw_query: str, schema_summary: str = "") -> QueryIntent:
    if not settings.anthropic_api_key or settings.anthropic_api_key == "your_key_here":
        return parse_without_llm(raw_query)
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1200,
        tools=[INTENT_TOOL],
        tool_choice={"type": "tool", "name": "set_query_intent"},
        messages=[{
            "role": "user",
            "content": (
                "Extract intent from this database question. Never guess an uncertain slot. "
                "Use ambiguous or missing status instead.\n"
                f"Schema summary:\n{schema_summary}\nQuestion: {raw_query}"
            ),
        }],
    )
    tool_use = next((block for block in response.content if block.type == "tool_use"), None)
    if tool_use is None:
        raise ValueError("Anthropic response did not contain structured intent output")
    return QueryIntent.model_validate(tool_use.input)


def parse_without_llm(raw_query: str) -> QueryIntent:
    """Deterministic fallback used when no Anthropic key is configured."""
    normalized = raw_query.lower()
    employee_terms = ("employee", "sales representative", "sales rep", "staff member")
    entity_value = "employee" if any(term in normalized for term in employee_terms) else "customer"
    metric_status = SlotStatus.AMBIGUOUS if any(word in normalized for word in ("best", "top", "worst", "biggest")) else SlotStatus.MISSING
    time_range = "last_30_days" if "last 30 days" in normalized else "all_time"
    return QueryIntent(
        raw_query=raw_query,
        entity=MetricSlot(status=SlotStatus.RESOLVED, value=entity_value),
        metric=MetricSlot(status=metric_status),
        time_range=MetricSlot(
            status=SlotStatus.RESOLVED,
            value=time_range,
            candidates=["all_time", "last_30_days", "last_year"],
        ),
    )
