from app.engine.sql_generator import generate_fallback_sql
from app.models.intent import MetricSlot, ResolvedIntent, SlotStatus


def resolved_intent(entity: str, metric: str, raw_query: str) -> ResolvedIntent:
    return ResolvedIntent(
        raw_query=raw_query,
        entity=MetricSlot(status=SlotStatus.RESOLVED, value=entity),
        metric=MetricSlot(status=SlotStatus.RESOLVED, value=metric),
        time_range=MetricSlot(status=SlotStatus.RESOLVED, value="all_time"),
    )


def test_employee_metric_choice_changes_generated_expression():
    result = generate_fallback_sql(resolved_intent("employee", "total_commission", "best performing employee"))
    assert "SUM(sales.commission) AS total_commission" in result.sql


def test_customer_order_count_uses_order_count():
    result = generate_fallback_sql(resolved_intent("customer", "order_count", "top customer by order count"))
    assert "COUNT(orders.id) AS order_count" in result.sql