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
    if intent.entity.value == "employee":
        sql = (
            "SELECT employees.name, COUNT(sales.id) AS sales_count "
            "FROM employees JOIN sales ON sales.employee_id = employees.id "
            "GROUP BY employees.id, employees.name ORDER BY sales_count DESC LIMIT 100"
        )
        tables = ["employees", "sales"]
    else:
        sql = (
            "SELECT customers.name, SUM(orders.total_amount) AS total_spend "
            "FROM customers JOIN orders ON orders.customer_id = customers.id "
            "GROUP BY customers.id, customers.name ORDER BY total_spend DESC LIMIT 100"
        )
        tables = ["customers", "orders"]
    return SQLGenerationResult(sql=sql, explanation="Fallback SQL generated without an LLM key.", tables_used=tables)
