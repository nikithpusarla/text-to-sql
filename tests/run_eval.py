from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1]))

from app.engine.ambiguity_detector import detect_ambiguity
from app.engine.intent_parser import parse_without_llm


ROOT = Path(__file__).parent


def run() -> None:
    cases = json.loads((ROOT / "eval_set.json").read_text(encoding="utf-8"))
    correct = 0
    false_positive = 0
    false_negative = 0
    clarification_turns = 0
    for case in cases:
        intent = parse_without_llm(case["query"])
        detected = detect_ambiguity(intent)
        actual_slots = set(detected)
        expected_slots = set(case["expected_ambiguous_slots"])
        if expected_slots == actual_slots or expected_slots.issubset(actual_slots):
            correct += 1
        false_positive += len(actual_slots - expected_slots)
        false_negative += len(expected_slots - actual_slots)
        clarification_turns += min(3, len(actual_slots))
    percentage = (correct / len(cases) * 100) if cases else 0
    print(f"ambiguity detection: {percentage:.1f}% ({correct}/{len(cases)})")
    print(f"false positives: {false_positive}; false negatives: {false_negative}")
    average_turns = clarification_turns / len(cases) if cases else 0
    print(f"average clarification turns: {average_turns:.2f}")


if __name__ == "__main__":
    run()
