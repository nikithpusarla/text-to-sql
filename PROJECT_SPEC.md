# Queryline Project Specification

## 1. Product intent

Queryline is a clarification-first business intelligence assistant. It accepts a natural-language question about a company database, converts the question into a structured intent, resolves underspecified business terms with a multiple-choice clarification, generates one read-only PostgreSQL query, and shows the resulting data with the SQL visible.

The primary product promise is semantic transparency: the system should make an uncertain definition visible before it makes an irreversible query decision.

## 2. Architecture summary

```text
Browser / CLI
    -> FastAPI routes
    -> intent parser
    -> ambiguity detector and glossary
    -> clarification session repository
    -> SQL generator
    -> sqlglot guardrails
    -> read-only PostgreSQL executor
    -> rows, SQL, explanation, audit event
```

The API and CLI share the same engine modules. Anthropic is optional. Without an API key, deterministic parser and generator implementations provide a repeatable local path.

## 3. Domain model

### `QueryIntent`

- `raw_query`: original user question.
- `entity`: customer or employee slot.
- `metric`: business measure such as `total_spend`, `order_count`, `recency`, `total_commission`, or `sales_count`.
- `time_range`: current supported period representation.
- `top_n`: optional requested result size.
- `filters`: optional structured filter strings.

### `MetricSlot`

- `status`: `resolved`, `ambiguous`, or `missing`.
- `value`: selected canonical value when resolved.
- `candidates`: choices shown to the user when uncertain.
- `sql_expr`: optional glossary expression.

### `ResolvedIntent`

A `QueryIntent` subtype whose Pydantic validator requires every slot to be resolved before SQL generation.

### `ClarificationQuestion`

Contains a slot name, a human-readable question, and canonical option values. The UI renders these values as selectable cards.

### `SQLGenerationResult`

Contains the generated SQL, a short explanation, and the tables used. The SQL is still untrusted until it passes `validate_and_limit`.

## 4. Engine pipeline

1. `parse_with_llm` uses Anthropic structured tool output when configured.
2. `parse_without_llm` supplies deterministic fallback behavior for local use.
3. `detect_ambiguity` checks unresolved slots against `metrics.yaml`.
4. `build_clarification_questions` converts candidates into user-facing choices.
5. `SessionRepository` stores the current intent between API requests.
6. `generate_with_llm` or `generate_fallback_sql` creates a candidate statement.
7. `validate_and_limit` parses the statement with sqlglot and enforces the safety contract.
8. `execute_sql` runs the statement using a read-only PostgreSQL role and a five-second timeout.
9. `audit.log_event` records query lifecycle events without exposing credentials.

## 5. Business glossary

The current glossary is in `app/glossary/metrics.yaml`.

| Entity | Ambiguous phrase | Candidate definitions |
|---|---|---|
| Customer | best, top, biggest, worst | total spend, order count, most recent order |
| Employee | best, top, worst | total commission, sales count |

Glossary values are canonical identifiers. Display labels can change without changing generated SQL contracts.

## 6. Database contract

The sample database contains:

- `customers(id, name, signup_date, status)`
- `orders(id, customer_id, order_date, total_amount, net_amount)`
- `employees(id, name, department, hire_date)`
- `sales(id, employee_id, order_id, sale_date, commission)`

See `DATABASE.md` for setup, roles, seed behavior, and verification commands.

## 7. Guardrail checklist

Every SQL statement must satisfy all of the following:

- Exactly one statement.
- Top-level statement is `SELECT`.
- No SQL comments.
- No `pg_sleep`.
- No system or cross-schema table access.
- Every table is in the known schema.
- Every referenced column is in the known schema.
- Join, function, and character-count complexity are within configured limits.
- A `LIMIT 100` is added when no limit exists.
- Execution uses the read-only role and a five-second PostgreSQL timeout.
- Rejections include a human-readable reason and an audit event.

This is defense in depth, not a substitute for database permissions, network controls, authentication, or tenant isolation.

## 8. Session strategy

The default `SessionRepository` stores JSON in `SESSION_STORE_PATH`, writes atomically through a temporary file, and reloads state for every operation. This makes local restarts less surprising while avoiding a new service dependency for the portfolio demo.

The repository is intentionally abstracted behind `set`, `get`, and `update`. A production multi-instance deployment should provide the same interface using PostgreSQL or Redis with TTL, optimistic concurrency, encryption policy, and tenant ownership checks.

## 9. Evaluation methodology

The evaluation runner combines:

- `tests/eval_set.json`: original ambiguity-focused cases.
- `tests/evaluation_cases.json`: structured cases with expected entity and candidate metrics.

Reported metrics:

- Intent classification accuracy: predicted entity equals labeled entity.
- Ambiguity precision and recall: predicted unresolved slot set versus labels.
- Clarification candidate recall: expected candidate definitions present in offered choices.
- Average clarification turns: unresolved slot count capped at three.
- Average parser latency: local deterministic parser wall-clock time.
- SQL semantic correctness: generated fallback SQL contains the expected entity table and metric alias for resolved fixtures.
- SQL execution success rate: intentionally reserved for PostgreSQL integration runs.
- Unsafe query rejection rate: verified by adversarial guardrail tests.

These metrics are scoped to the checked-in fixtures. They are not a benchmark of an external model or a hosted production workload.

## 10. Build order

1. Define schema, glossary, and Pydantic contracts.
2. Implement deterministic intent parsing and ambiguity detection.
3. Add structured Anthropic adapters behind the same contracts.
4. Implement fallback and model-backed SQL generation.
5. Add AST validation, complexity limits, read-only execution, and audit events.
6. Add persistent session repository abstraction.
7. Expose API, CLI, and dashboard workflows.
8. Add unit, API, adversarial, persistence, and evaluation tests.
9. Document deployment and explicitly record remaining limitations.

## 11. Assumptions

- The sample database is PostgreSQL 16.
- A single company workspace is used locally.
- The glossary is authoritative for fallback metric choices.
- Users are trusted to access the workspace; authentication is outside the current scope.
- The API process can write to the configured session and audit directories in local mode.

## 12. Known limitations

- Multi-tenant isolation and authentication are not implemented.
- JSON persistence is not suitable for concurrent multi-instance deployment.
- The evaluator does not execute every generated query against a live database.
- Date-range parsing and filters remain intentionally small in fallback mode.
- Schema migrations, rate limiting, and hosted observability need a deployment-specific implementation.
