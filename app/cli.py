from __future__ import annotations

import argparse

from app.engine.ambiguity_detector import detect_ambiguity
from app.models.intent import MetricSlot, QueryIntent, SlotStatus


def build_demo_intent(raw_query: str) -> QueryIntent:
    return QueryIntent(
        raw_query=raw_query,
        entity=MetricSlot(status=SlotStatus.RESOLVED, value="customer"),
        metric=MetricSlot(status=SlotStatus.AMBIGUOUS, candidates=["total_spend", "order_count", "recency"]),
        time_range=MetricSlot(status=SlotStatus.MISSING, candidates=["all_time", "last_30_days", "last_year"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Demo text-to-SQL clarifier")
    parser.add_argument("query", nargs="?", default="who is our best customer")
    args = parser.parse_args()

    intent = build_demo_intent(args.query)
    print(detect_ambiguity(intent))


if __name__ == "__main__":
    main()
