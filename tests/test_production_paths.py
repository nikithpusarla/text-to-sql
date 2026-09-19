import sys
from pathlib import Path

from fastapi.testclient import TestClient

from app import cli
from app.config import settings
from app.db.connection import get_admin_connection_kwargs, get_connection_kwargs
from app.main import app
from app.models.sql_result import SQLGenerationResult


def test_application_connection_uses_readonly_role():
    kwargs = get_connection_kwargs()
    assert kwargs["user"] == settings.postgres_readonly_user
    assert kwargs["autocommit"] is True


def test_admin_connection_uses_configured_bootstrap_credentials():
    kwargs = get_admin_connection_kwargs()
    assert kwargs["user"] == settings.postgres_user
    assert kwargs["password"] == settings.postgres_password


def test_schema_file_contains_indexes_for_foreign_keys():
    schema = Path(__file__).parents[1] / "app" / "db" / "schema.sql"
    text = schema.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS customers" in text
    assert "orders_customer_id_idx" in text
    assert "sales_employee_id_idx" in text


def test_startup_initializes_schema_when_enabled(monkeypatch):
    called = []
    monkeypatch.setattr("app.main.initialize_schema", lambda: called.append(True))
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "database_init_on_startup", True)

    with TestClient(app):
        pass

    assert called == [True]


def test_cli_resolves_and_executes_a_question(monkeypatch, capsys):
    monkeypatch.setattr(cli, "parse_with_llm", lambda *_args, **_kwargs: cli.build_demo_intent("best customer"))
    monkeypatch.setattr(
        cli,
        "generate_with_llm",
        lambda *_args, **_kwargs: SQLGenerationResult(
            sql="SELECT name FROM customers", explanation="test", tables_used=["customers"]
        ),
    )
    monkeypatch.setattr(cli, "execute_sql", lambda _sql: [{"name": "Customer 1"}])
    answers = iter(["1", "1"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    monkeypatch.setattr(sys, "argv", ["queryline", "best customer"])

    cli.main()

    output = capsys.readouterr().out
    assert "SELECT name FROM customers LIMIT 100" in output
    assert "Customer 1" in output


def test_execute_endpoint_returns_guarded_rows(monkeypatch):
    monkeypatch.setattr("app.main.execute_sql", lambda _sql: [{"name": "Customer 1"}])

    response = TestClient(app).post("/execute", json={"sql": "SELECT name FROM customers"})

    assert response.status_code == 200
    assert response.json()["rows"] == [{"name": "Customer 1"}]