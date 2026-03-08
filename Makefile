PYTHON ?= python3

.PHONY: dev test lint

dev:
	docker compose up --build

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check .
