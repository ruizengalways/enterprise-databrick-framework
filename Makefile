.PHONY: install validate lint typecheck test ci bundle-validate

install:
	python -m pip install -e '.[dev]'

validate:
	edp validate config/tables

lint:
	ruff check .

typecheck:
	mypy src/edp_framework

test:
	pytest

ci: validate lint typecheck test

bundle-validate:
	databricks bundle validate -t $${TARGET:-dev}
