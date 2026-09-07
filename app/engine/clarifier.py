from __future__ import annotations

from app.models.clarification import ClarificationQuestion


def build_clarification_questions(slot_name: str, candidates: list[str], query: str) -> list[ClarificationQuestion]:
    if not candidates:
        return []
    question_map = {
        "metric": "Which definition of the metric do you mean?",
        "entity": "Which entity are you asking about?",
        "time_range": "Which time period should we include?",
    }
    return [
        ClarificationQuestion(
            slot_name=slot_name,
            question_text=question_map.get(slot_name, "Please choose the intended option."),
            options=candidates[:5],
        )
    ]
