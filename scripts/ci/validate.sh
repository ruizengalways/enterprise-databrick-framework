#!/usr/bin/env bash
set -euo pipefail

test ! -e databricks.yml
test ! -d platform
test ! -d resources
test ! -d config/environments

edp validate examples/table_specs
ruff check .
mypy src/edp_framework
pytest
python -m pip wheel . --no-deps --wheel-dir dist
