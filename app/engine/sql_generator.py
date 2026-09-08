from __future__ import annotations

import anthropic

from app.config import settings
from app.models.intent import ResolvedIntent
from app.models.sql_result import SQLGenerationResult


SQL_TOOL = {
    "name": "generate_sql",
    "description": "Generate one read-only PostgreSQL SELECT statement for the resolved intent.",
    "input_schema": SQLGenerationResult.model_json_schema(),
}


def generate_with_llm(intent: ResolvedIntent, schema_summary: str) -> SQLGenerationResult:
    if not settings.anthropic_api_key or settings.anthropic_api_key == "your_key_here":
        return generate_fallback_sql(intent)
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1200,
        tools=[SQL_TOOL],
        tool_choice={"type": "tool", "name": "generate_sql"},
        messages=[{
            "role": "user",
            "content": (
                "Generate SQL only for this fully resolved intent. Use only tables and columns in the schema. "
                "The query must be a single SELECT statement.\n"
                f"Schema: {schema_summary}\nIntent: {intent.model_dump()}"
            ),
        }],
    )
    tool_use = next((block for block in response.content if block.type == "tool_use"), None)
    if tool_use is None:
        raise ValueError("Anthropic response did not contain structured SQL output")
    return SQLGenerationResult.model_validate(tool_use.input)


def generate_fallback_sql(intent: ResolvedIntent) -> SQLGenerationResult:
    descending = not any(word in intent.raw_query.lower().split() for word in ("worst", "lowest", "least"))
    order_direction = "DESC" if descending else "ASC"
    if intent.entity.value == "employee":
        metric = intent.metric.value or "sales_count"
        expression = {
            "total_commission": "SUM(sales.commission)",
            "sales_count": "COUNT(sales.id)",
        }.get(metric, "COUNT(sales.id)")
        sql = (
            f"SELECT employees.name, {expression} AS {metric} "
            "FROM employees JOIN sales ON sales.employee_id = employees.id "
            f"GROUP BY employees.id, employees.name ORDER BY {metric} {order_direction} LIMIT 100"
        )
        tables = ["employees", "sales"]
    else:
        metric = intent.metric.value or "total_spend"
        expression = {
            "total_spend": "SUM(orders.total_amount)",
            "order_count": "COUNT(orders.id)",
            "recency": "MAX(orders.order_date)",
        }.get(metric, "SUM(orders.total_amount)")
        sql = (
            f"SELECT customers.name, {expression} AS {metric} "
            "FROM customers JOIN orders ON orders.customer_id = customers.id "
            f"GROUP BY customers.id, customers.name ORDER BY {metric} {order_direction} LIMIT 100"
        )
        tables = ["customers", "orders"]
    return SQLGenerationResult(sql=sql, explanation="Fallback SQL generated without an LLM key.", tables_used=tables)
