import pytest

from app.engine.guardrails import SQLValidationError, validate_and_limit

SCHEMA = {
    "customers": ["id", "name", "status"],
    "orders": ["id", "customer_id", "total_amount"],
}


def test_select_gets_limit_injected():
    result = validate_and_limit("SELECT name FROM customers", SCHEMA)
    assert "LIMIT 100" in result.upper()


def test_write_statements_are_rejected():
    with pytest.raises(SQLValidationError):
        validate_and_limit("DELETE FROM customers", SCHEMA)


def test_unknown_columns_are_rejected():
    with pytest.raises(SQLValidationError, match="Unknown column"):
        validate_and_limit("SELECT secret FROM customers", SCHEMA)


def test_multiple_statements_are_rejected():
    with pytest.raises(SQLValidationError):
        validate_and_limit("SELECT name FROM customers; SELECT id FROM orders", SCHEMA)


@pytest.mark.parametrize(
    "query, reason",
    [
        ("DROP TABLE customers", "Only one SELECT"),
        ("DELETE FROM customers", "Only one SELECT"),
        ("UPDATE customers SET name = 'x'", "Only one SELECT"),
        ("SELECT pg_sleep(5)", "pg_sleep"),
        ("SELECT name FROM customers -- bypass", "comments"),
        ("SELECT name FROM pg_catalog.pg_tables", "cross-schema"),
    ],
)
def test_adversarial_sql_is_rejected(query, reason):
    with pytest.raises(SQLValidationError, match=reason):
        validate_and_limit(query, SCHEMA)


def test_query_complexity_limit_is_enforced():
    query = "SELECT customers.name FROM customers JOIN orders ON orders.customer_id = customers.id"
    with pytest.raises(SQLValidationError, match="join complexity"):
        validate_and_limit(query, SCHEMA, max_joins=0)
