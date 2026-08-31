.PHONY: install validate lint typecheck test build ci

install:
	python -m pip install -e '.[dev]'

validate:
	edp validate examples/table_specs

lint:
	ruff check .

typecheck:
	mypy src/edp_framework

test:
	pytest

build:
	python -m pip wheel . --no-deps --wheel-dir dist

ci: validate lint typecheck test build
