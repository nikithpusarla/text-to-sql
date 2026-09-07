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
