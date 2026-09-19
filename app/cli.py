from __future__ import annotations

import argparse

from app.engine.guardrails import validate_and_limit
from app.engine.ambiguity_detector import detect_ambiguity
from app.engine.clarifier import build_clarification_questions
from app.engine.intent_parser import parse_with_llm
from app.engine.sql_generator import generate_with_llm
from app.executor import execute_sql
from app.schema import SCHEMA
from app.models.intent import MetricSlot, QueryIntent, SlotStatus


def build_demo_intent(raw_query: str) -> QueryIntent:
    return QueryIntent(
        raw_query=raw_query,
        entity=MetricSlot(status=SlotStatus.RESOLVED, value="customer"),
        metric=MetricSlot(status=SlotStatus.AMBIGUOUS, candidates=["total_spend", "order_count", "recency"]),
        time_range=MetricSlot(status=SlotStatus.MISSING, candidates=["all_time", "last_30_days", "last_year"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a question and run guarded read-only SQL")
    parser.add_argument("query", nargs="?", default="who is our best customer")
    args = parser.parse_args()

    intent = parse_with_llm(args.query, schema_summary=str(SCHEMA))
    while True:
        unresolved = detect_ambiguity(intent)
        if not unresolved:
            break
        slot_name, candidates = next(iter(unresolved.items()))
        questions = build_clarification_questions(slot_name, candidates, intent.raw_query)
        question = questions[0]
        print(question.question_text)
        for index, option in enumerate(question.options, start=1):
            print(f"{index}. {option}")
        answer = input("Choose an option: ").strip()
        try:
            chosen = question.options[int(answer) - 1]
        except (ValueError, IndexError) as exc:
            raise SystemExit("Please choose a valid option number.") from exc
        intent = intent.model_copy(update={
            slot_name: getattr(intent, slot_name).model_copy(update={
                "status": SlotStatus.RESOLVED,
                "value": chosen,
            })
        })

    result = generate_with_llm(intent, schema_summary=str(SCHEMA))
    result.sql = validate_and_limit(result.sql, SCHEMA)
    rows = execute_sql(result.sql)
    print(f"\nSQL:\n{result.sql}\n")
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
