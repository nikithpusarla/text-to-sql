from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_query_returns_clarification_questions():
    response = client.post("/query", json={"query": "who is our best customer"})
    assert response.status_code == 200
    body = response.json()
    assert body["session_id"]
    assert {question["slot_name"] for question in body["questions"]} == {"metric"}


def test_clarification_can_resolve_the_session():
    initial = client.post("/query", json={"query": "who is our best customer"}).json()
    session_id = initial["session_id"]
    next_response = client.post(
        "/clarify",
        json={"session_id": session_id, "slot_name": "metric", "chosen_value": "total_spend"},
    )
    assert next_response.status_code == 200
    assert next_response.json()["result"]["sql"].startswith("SELECT")


def test_execute_rejects_non_select_sql_before_database_access():
    response = client.post("/execute", json={"sql": "DELETE FROM customers"})
    assert response.status_code == 422
