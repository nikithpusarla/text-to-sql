# Project Prompt: Text-to-SQL with Clarification Engine

This file mirrors the project brief for the repository and acts as the canonical specification.

---

## 1. PROJECT STRUCTURE

```text
text2sql-clarify/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── cli.py
│   ├── config.py
│   ├── db/
│   │   ├── connection.py
│   │   ├── introspect.py
│   │   └── seed_data.sql
│   ├── glossary/
│   │   ├── metrics.yaml
│   │   └── loader.py
│   ├── models/
│   │   ├── intent.py
│   │   ├── clarification.py
│   │   └── sql_result.py
│   ├── engine/
│   │   ├── intent_parser.py
│   │   ├── ambiguity_detector.py
│   │   ├── clarifier.py
│   │   ├── sql_generator.py
│   │   └── guardrails.py
│   ├── session/
│   │   └── state.py
│   └── executor.py
├── tests/
│   ├── test_ambiguity_detector.py
│   ├── test_guardrails.py
│   ├── test_intent_parser.py
│   └── eval_set.json
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## 2. SAMPLE DATABASE SCHEMA

The sample schema includes customers, orders, employees, and sales.

## 3. PYDANTIC MODELS

...see the original project brief.

## 4. BUSINESS GLOSSARY

...see the original project brief.

## 5. ENGINE WORKFLOW

...see the original project brief.

## 6. GUARDRAILS CHECKLIST

...see the original project brief.

## 7. EVALUATION SET

...see the original project brief.

## 8. BUILD ORDER

...see the original project brief.

## 9. STARTING INSTRUCTION

...see the original project brief.
