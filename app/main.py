from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, HTTPException

from app.engine.ambiguity_detector import detect_ambiguity
from app.engine.clarifier import build_clarification_questions
from app.engine.guardrails import SQLValidationError, validate_and_limit
from app.engine.intent_parser import parse_with_llm
from app.engine.sql_generator import generate_with_llm
from app.audit import log_event
from app.executor import execute_sql
from app.schema import SCHEMA
from app.models.clarification import ClarificationResponse
from app.models.intent import MetricSlot, ResolvedIntent, SlotStatus
from app.models.query import ExecuteRequest, QueryRequest, QueryResponse
from app.session.state import get_session, set_session, update_session

app = FastAPI(title="Text-to-SQL Clarification Engine")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/execute")
def execute(request: ExecuteRequest) -> dict:
    try:
        validated_sql = validate_and_limit(request.sql, SCHEMA)
    except SQLValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        rows = execute_sql(validated_sql)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database execution failed") from exc
    log_event("sql_executed", {"sql": validated_sql, "row_count": len(rows)})
    return {"sql": validated_sql, "rows": rows, "row_count": len(rows)}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    session_id = request.session_id or str(uuid4())
    intent = parse_with_llm(request.query, schema_summary=str(SCHEMA))
    set_session(session_id, intent)
    unresolved = detect_ambiguity(intent)
    questions = [
        question
        for slot_name, candidates in unresolved.items()
        for question in build_clarification_questions(slot_name, candidates, intent.raw_query)
    ][:3]
    if questions:
        log_event("clarification_requested", {"session_id": session_id, "intent": intent.model_dump()})
        return QueryResponse(session_id=session_id, questions=questions)

    resolved = ResolvedIntent.model_validate(intent.model_dump())
    result = generate_with_llm(resolved, schema_summary=str(SCHEMA))
    result.sql = validate_and_limit(result.sql, SCHEMA)
    log_event("sql_generated", {"session_id": session_id, "intent": resolved.model_dump(), "sql": result.sql})
    return QueryResponse(session_id=session_id, result=result)


@app.post("/clarify", response_model=QueryResponse)
def clarify(response: ClarificationResponse) -> QueryResponse:
    intent = get_session(response.session_id)
    if intent is None:
        raise HTTPException(status_code=404, detail="Unknown session")
    slot = getattr(intent, response.slot_name, None)
    if not isinstance(slot, MetricSlot):
        raise HTTPException(status_code=400, detail="Unknown clarification slot")
    updated_slot = slot.model_copy(update={"status": SlotStatus.RESOLVED, "value": response.chosen_value})
    updated = update_session(response.session_id, **{response.slot_name: updated_slot})
    assert updated is not None
    unresolved = detect_ambiguity(updated)
    questions = [
        question
        for slot_name, candidates in unresolved.items()
        for question in build_clarification_questions(slot_name, candidates, updated.raw_query)
    ][:3]
    if questions:
        return QueryResponse(session_id=response.session_id, questions=questions)
    resolved = ResolvedIntent.model_validate(updated.model_dump())
    result = generate_with_llm(resolved, schema_summary=str(SCHEMA))
    result.sql = validate_and_limit(result.sql, SCHEMA)
    log_event("sql_generated", {"session_id": response.session_id, "intent": resolved.model_dump(), "sql": result.sql})
    return QueryResponse(session_id=response.session_id, result=result)
