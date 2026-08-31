from __future__ import annotations

from pathlib import Path

import yaml

from edp_framework.metadata.models import TableSpec


def load_table_spec(path: str | Path) -> TableSpec:
    path = Path(path)
    with path.open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a YAML mapping")
    return TableSpec.model_validate(payload)


def load_table_specs(path: str | Path) -> list[TableSpec]:
    root = Path(path)
    files = [root] if root.is_file() else sorted(root.rglob("*.yml")) + sorted(root.rglob("*.yaml"))
    specs: list[TableSpec] = []
    seen: set[str] = set()
    for file in files:
        spec = load_table_spec(file)
        if spec.dataset_id in seen:
            raise ValueError(f"duplicate dataset_id: {spec.dataset_id}")
        seen.add(spec.dataset_id)
        specs.append(spec)
    return specs
