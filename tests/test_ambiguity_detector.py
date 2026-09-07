from app.engine.ambiguity_detector import detect_ambiguity
from app.engine.intent_parser import parse_without_llm


def test_best_customer_stays_ambiguous_with_glossary_candidates():
    intent = parse_without_llm("who is our best customer")
    unresolved = detect_ambiguity(intent)
    assert unresolved["metric"] == ["total_spend", "order_count", "recency"]


def test_employee_query_uses_employee_entity():
    intent = parse_without_llm("who is our best employee")
    assert intent.entity.value == "employee"
