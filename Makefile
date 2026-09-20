.PHONY: install test eval lint coverage start db-up db-down

install:
	python -m pip install -r requirements-dev.txt

test:
	python -m pytest -q

eval:
	python tests/run_eval.py

lint:
	ruff check app tests

coverage:
	coverage run -m pytest -q
	coverage report -m

start:
	python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

db-up:
	docker compose up -d

db-down:
	docker compose down