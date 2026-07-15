.PHONY: setup validate test lint check

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -e '.[dev]'

validate:
	.venv/bin/python scripts/validate_source_registry.py

test:
	.venv/bin/pytest -q

lint:
	.venv/bin/ruff check src scripts tests

check: validate lint test
