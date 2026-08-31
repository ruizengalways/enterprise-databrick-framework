#!/usr/bin/env bash
set -euo pipefail
edp validate config/tables
ruff check .
mypy src/edp_framework
pytest
