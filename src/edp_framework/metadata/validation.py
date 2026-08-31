from __future__ import annotations

from pathlib import Path

from edp_framework.metadata.loader import load_table_specs
from edp_framework.patterns.registry import PatternRegistry


def validate_path(path: str | Path) -> int:
    registry = PatternRegistry()
    specs = load_table_specs(path)
    for spec in specs:
        registry.validate(spec)
    return len(specs)
