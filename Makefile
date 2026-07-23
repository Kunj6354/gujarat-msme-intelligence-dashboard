.PHONY: setup validate validate-strict test lint format format-check check

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -e '.[dev]'

validate:
	python scripts/validate_source_registry.py

validate-strict:
	python scripts/validate_source_registry.py --strict

test:
	pytest -q

lint:
	ruff check src scripts tests

format:
	ruff format src scripts tests

format-check:
	ruff format --check src scripts tests

check: validate lint format-check test
