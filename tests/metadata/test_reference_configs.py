from pathlib import Path

from edp_framework.metadata.loader import load_table_specs
from edp_framework.patterns.registry import PatternRegistry


def test_all_reference_table_configs_are_valid() -> None:
    root = Path(__file__).parents[2] / "config" / "tables"
    specs = load_table_specs(root)
    registry = PatternRegistry(load_plugins=False)

    assert len(specs) >= 5
    for spec in specs:
        registry.validate(spec)
