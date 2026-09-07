# Text-to-SQL with Clarification Engine

A Python 3.11+ project for generating SQL from natural-language questions while explicitly asking clarifying questions when intent is ambiguous.

## Stack

- Python 3.11+
- PostgreSQL
- FastAPI
- Pydantic v2
- psycopg v3
- sqlglot
- Anthropic SDK
- Typer

## Setup

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Copy `.env.example` to `.env` and fill in values.
4. Start PostgreSQL via Docker Compose or a local database.
5. Run the CLI or API.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.cli
```

## Notes

This project follows the build order from the project brief:

1. Docker/Postgres + sample data
2. Schema introspection
3. Pydantic models
4. Glossary and ambiguity detection
5. Intent parsing and clarifying questions
6. SQL generation and validation
7. Executor and API wrapping
8. Eval harness
