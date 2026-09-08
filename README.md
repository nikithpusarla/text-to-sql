# Queryline: Text-to-SQL with Clarification Engine

Queryline is a natural-language analytics application that lets people ask questions about company data without writing SQL. Its key behavior is deliberate clarification: when a question is ambiguous, Queryline asks the user to choose the intended definition before generating or executing a query.

For example, "Who is our best customer?" could mean the customer with the highest total spend, the most orders, or the most recent order. Queryline identifies that ambiguity, presents the choices, and only continues after the user selects one.

## What Has Been Built

- Browser-based SaaS-style dashboard named Queryline
- Natural-language question input
- Clarification questions with multiple-choice options
- Multi-turn in-memory sessions
- Structured Anthropic tool-use integration for intent parsing and SQL generation
- Deterministic fallback mode when no Anthropic API key is configured
- PostgreSQL 16 database running through Docker Compose
- Seeded sample company data
- Schema introspection through `information_schema`
- Read-only PostgreSQL role for query execution
- SQL parsing and validation with `sqlglot`
- SELECT-only enforcement
- Table and column validation against the known schema
- Automatic `LIMIT 100` injection
- Five-second PostgreSQL statement timeout
- SQL and resolved-intent audit logging
- FastAPI API and interactive Swagger documentation
- CLI workflow for local testing
- 35-case ambiguity evaluation set
- Automated test suite

## How the Workflow Works

```text
User question
      |
      v
Intent parsing
      |
      v
Ambiguity detection
      |
      +---- unresolved intent ----> clarification choices
      |                                    |
      |                                    v
      +---------------------------- resolved intent
                                           |
                                           v
                                  structured SQL generation
                                           |
                                           v
                                  SQL guardrails and LIMIT
                                           |
                                           v
                                  read-only PostgreSQL query
                                           |
                                           v
                                      answer table
```

## Browser Dashboard

The Queryline dashboard is served by FastAPI at the application root. It provides:

- Workspace-style navigation
- Database connection status
- Natural-language query composer
- Suggested example questions
- Clarification cards
- Answer table rendering
- Generated SQL inspection
- Responsive desktop and mobile layout

Open this URL after starting the API:

```text
http://127.0.0.1:8000/
```

## Database

The local database is PostgreSQL 16 running in Docker. The database is named `companies` and contains four tables:

### `customers`

- `id`
- `name`
- `signup_date`
- `status`

### `orders`

- `id`
- `customer_id`
- `order_date`
- `total_amount`
- `net_amount`

### `employees`

- `id`
- `name`
- `department`
- `hire_date`

### `sales`

- `id`
- `employee_id`
- `order_id`
- `sale_date`
- `commission`

The seed script creates approximately:

- 50 customers
- 300 orders
- 10 employees
- 300 sales records

The data intentionally has different customer and employee performance patterns so ambiguous questions produce meaningful alternatives.

The application uses the `readonly_user` PostgreSQL role for execution. The Docker database is mapped to host port `5433` because port `5432` may already be occupied by a native PostgreSQL installation.

The complete reproducible database setup is documented in [DATABASE.md](DATABASE.md). The SQL seed file is included in `app/db/seed_data.sql`, so the database is recreated automatically when the Docker volume is initialized.

## Technology Stack

- Python 3.11+
- FastAPI
- Pydantic v2
- PostgreSQL 16
- Docker Compose
- psycopg v3
- sqlglot
- Anthropic Python SDK
- Typer-compatible CLI workflow
- PyYAML
- pytest
- HTML, CSS, and vanilla JavaScript dashboard

## Project Structure

```text
text2sql-clarify/
├── app/
│   ├── main.py                  # FastAPI app and dashboard/API routes
│   ├── cli.py                   # Command-line demo
│   ├── config.py                # Pydantic settings and .env loading
│   ├── audit.py                 # JSONL pipeline logging
│   ├── executor.py              # Read-only PostgreSQL execution
│   ├── schema.py                # Known schema used by local guardrails
│   ├── static/                  # Queryline browser dashboard
│   ├── db/
│   │   ├── connection.py        # psycopg connection configuration
│   │   ├── introspect.py        # information_schema introspection
│   │   └── seed_data.sql        # Tables, data, and read-only role
│   ├── engine/
│   │   ├── intent_parser.py     # Anthropic tool output and fallback parser
│   │   ├── ambiguity_detector.py
│   │   ├── clarifier.py
│   │   ├── sql_generator.py     # Anthropic tool output and fallback SQL
│   │   └── guardrails.py        # sqlglot safety validation
│   ├── glossary/
│   │   ├── metrics.yaml         # Business metric candidates
│   │   └── loader.py
│   ├── models/                  # Pydantic request and domain models
│   └── session/                 # In-memory multi-turn session store
├── tests/
│   ├── eval_set.json            # 35 hand-labeled ambiguity cases
│   ├── run_eval.py              # Evaluation metrics runner
│   └── test_*.py                # Unit and API tests
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

### Requirements

- Windows, macOS, or Linux
- Python 3.11 or newer
- Docker Desktop with the Docker engine running
- An Anthropic API key is optional for fallback mode and required for live LLM calls

### Install and start

```powershell
cd C:\Users\nikit\OneDrive\Desktop\backend\text2sql-clarify
python -m pip install -r requirements.txt
Copy-Item .env.example .env
docker compose up -d
```

The `.env` file contains local database settings. Do not commit it because it may contain secrets.

Verify the container:

```powershell
docker compose ps
```

Verify the live schema:

```powershell
python -m app.db.introspect
```

Start the API:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Then open:

- Dashboard: `http://127.0.0.1:8000/`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/health`

## Example User Flow

1. Open the dashboard.
2. Ask: `Who is our best customer?`
3. Choose `total_spend`, `order_count`, or `recency`.
4. Queryline generates one guarded PostgreSQL `SELECT` statement.
5. The read-only executor runs the query.
6. The dashboard displays the answer rows and generated SQL.

## API Endpoints

### `GET /health`

Returns the service status.

### `POST /query`

Starts a query session.

```json
{
  "query": "Who is our best customer?"
}
```

If the question is ambiguous, the response contains a `session_id` and clarification questions.

### `POST /clarify`

Resolves one slot in an existing session.

```json
{
  "session_id": "your-session-id",
  "slot_name": "metric",
  "chosen_value": "total_spend"
}
```

When all required slots are resolved, the response contains generated SQL.

### `POST /execute`

Validates and executes a SQL statement against PostgreSQL.

```json
{
  "sql": "SELECT name FROM customers LIMIT 10"
}
```

The endpoint rejects write statements, unknown tables, unknown columns, and multiple SQL statements.

## Anthropic Integration

When `ANTHROPIC_API_KEY` contains a real key, the application uses Anthropic tool-based structured output for:

1. Converting a natural-language question into a `QueryIntent`
2. Generating an `SQLGenerationResult` from a resolved intent

The application does not ask the model to return unstructured JSON text. It uses tool schemas validated by Pydantic.

Without a real key, the application uses a deterministic parser and fallback SQL generator. This makes local development and automated tests possible without external API access.

Configure live LLM mode in `.env`:

```env
ANTHROPIC_API_KEY=your_real_key
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
```

## Testing

Run the automated tests:

```powershell
python -m pytest -q
```

The current suite covers:

- Glossary ambiguity detection
- Deterministic intent parsing
- Pydantic resolved-intent validation
- SELECT-only SQL enforcement
- Unknown table and column rejection
- Multiple-statement rejection
- Automatic `LIMIT 100`
- API health and dashboard delivery
- Multi-turn clarification
- Seed schema and read-only role configuration

Run the evaluation set:

```powershell
python tests\run_eval.py
```

The current evaluation set contains 35 examples and reports:

- Ambiguity detection percentage
- False positives
- False negatives
- Average clarification turns

Latest verified results:

```text
18 passed
ambiguity detection: 100.0% (35/35)
false positives: 0
false negatives: 0
average clarification turns: 1.00
```

## Safety and Guardrails

- Database access uses a read-only PostgreSQL role.
- Queries are parsed with `sqlglot` using the PostgreSQL dialect.
- Only one `SELECT` statement is accepted.
- Referenced tables and columns are checked against the schema.
- Missing limits are automatically capped at 100 rows.
- PostgreSQL `statement_timeout` is set to five seconds per execution.
- Generated SQL and resolved intent are written to `logs/pipeline.jsonl`.
- `.env`, runtime logs, caches, and virtual environments are excluded from Git.

## Current Prototype Limitations

- Sessions are stored in memory and are lost when the API restarts.
- The current workspace uses one database configuration.
- Authentication and billing are not included yet.
- Multi-tenant isolation needs to be added before connecting multiple companies.
- The evaluation set is hand-labeled and intentionally small.
- Production deployment, HTTPS, rate limiting, and secret management still need to be configured for a hosted SaaS release.

## Roadmap

- Add user authentication and organization workspaces
- Add tenant-specific database connections and glossaries
- Persist sessions and query history in PostgreSQL or Redis
- Add streaming answer generation
- Add saved reports and scheduled queries
- Add usage limits, billing, and admin analytics
- Add connectors for MySQL, Snowflake, BigQuery, and SQL Server
- Add a production deployment configuration
