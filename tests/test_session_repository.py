from app.models.intent import MetricSlot, QueryIntent, SlotStatus
from app.session.state import SessionRepository


def test_file_session_repository_survives_a_new_instance(tmp_path):
    intent = QueryIntent(
        raw_query="best customer",
        entity=MetricSlot(status=SlotStatus.RESOLVED, value="customer"),
        metric=MetricSlot(status=SlotStatus.AMBIGUOUS, candidates=["total_spend"]),
        time_range=MetricSlot(status=SlotStatus.RESOLVED, value="all_time"),
    )
    path = tmp_path / "sessions.json"
    SessionRepository(path).set("session-1", intent)

    restored = SessionRepository(path).get("session-1")

    assert restored is not None
    assert restored.raw_query == intent.raw_query
    assert restored.metric.status == SlotStatus.AMBIGUOUS