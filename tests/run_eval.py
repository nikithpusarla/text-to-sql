from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.engine.ambiguity_detector import detect_ambiguity
from app.engine.intent_parser import parse_without_llm
from app.engine.sql_generator import generate_fallback_sql
from app.models.intent import MetricSlot, ResolvedIntent, SlotStatus

ROOT = Path(__file__).parent


def resolved_intent(entity: str, metric: str, query: str) -> ResolvedIntent:
    return ResolvedIntent(
        raw_query=query,
        entity=MetricSlot(status=SlotStatus.RESOLVED, value=entity),
        metric=MetricSlot(status=SlotStatus.RESOLVED, value=metric),
        time_range=MetricSlot(status=SlotStatus.RESOLVED, value="all_time"),
    )


def run() -> None:
    cases = json.loads((ROOT / "eval_set.json").read_text(encoding="utf-8"))
    cases += json.loads((ROOT / "evaluation_cases.json").read_text(encoding="utf-8"))
    intent_correct = 0
    ambiguity_tp = ambiguity_fp = ambiguity_fn = 0
    candidate_hits = 0
    candidate_total = 0
    clarification_turns = 0
    latencies = []
    for case in cases:
        started = time.perf_counter()
        intent = parse_without_llm(case["query"])
        detected = detect_ambiguity(intent)
        latencies.append((time.perf_counter() - started) * 1000)
        actual_slots = set(detected)
        expected_slots = set(case["expected_ambiguous_slots"])
        expected_entity = case.get("expected_entity")
        if expected_entity is None:
            expected_entity = "employee" if "employee" in case["query"].lower() or "sales representative" in case["query"].lower() else "customer"
        intent_correct += int(intent.entity.value == expected_entity)
        ambiguity_tp += len(actual_slots & expected_slots)
        ambiguity_fp += len(actual_slots - expected_slots)
        ambiguity_fn += len(expected_slots - actual_slots)
        expected_candidates = set(case.get("expected_candidates", []))
        actual_candidates = set(detected.get("metric", []))
        candidate_hits += len(expected_candidates & actual_candidates)
        candidate_total += len(expected_candidates)
        clarification_turns += min(3, len(actual_slots))
    precision = ambiguity_tp / (ambiguity_tp + ambiguity_fp) if ambiguity_tp + ambiguity_fp else 1
    recall = ambiguity_tp / (ambiguity_tp + ambiguity_fn) if ambiguity_tp + ambiguity_fn else 1
    intent_accuracy = intent_correct / len(cases) if cases else 0
    candidate_recall = candidate_hits / candidate_total if candidate_total else 0
    print(f"intent classification accuracy: {intent_accuracy:.1%} ({intent_correct}/{len(cases)})")
    print(f"ambiguity precision: {precision:.1%}; recall: {recall:.1%}")
    print(f"clarified question candidate recall: {candidate_recall:.1%}")
    average_turns = clarification_turns / len(cases) if cases else 0
    print(f"average clarification turns: {average_turns:.2f}")
    print(f"average parser latency: {sum(latencies) / len(latencies):.2f} ms")

    semantic_cases = [
        ("customer", "total_spend", "best customer"),
        ("customer", "order_count", "customers with most orders"),
        ("customer", "recency", "most recent customer order"),
        ("employee", "total_commission", "employee by commission"),
        ("employee", "sales_count", "employee with most sales"),
    ]
    semantic_correct = 0
    for entity, metric, query in semantic_cases:
        result = generate_fallback_sql(resolved_intent(entity, metric, query))
        semantic_correct += int(metric in result.sql and entity + "s" in result.sql)
    print(f"SQL semantic correctness: {semantic_correct / len(semantic_cases):.1%} ({semantic_correct}/{len(semantic_cases)})")
    print("SQL execution success rate: offline harness; run integration tests with PostgreSQL for live results")
    print("unsafe query rejection rate: covered by tests/test_guardrails.py")


if __name__ == "__main__":
    run()
