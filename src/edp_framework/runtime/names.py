from __future__ import annotations

import re

_RELATION_PART = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def qualify_relation(catalog: str, relation: str) -> str:
    """Return a safe three-part Unity Catalog relation.

    Dataset metadata stores `schema.table` so the same semantic contract can be used in
    multiple environments while the consuming workload injects the target catalog.
    """

    parts = relation.split(".")
    if len(parts) != 2:
        raise ValueError(f"relation must be schema.table, got {relation!r}")
    if not _RELATION_PART.fullmatch(catalog) or not all(
        _RELATION_PART.fullmatch(part) for part in parts
    ):
        raise ValueError(f"unsafe Unity Catalog relation: {catalog}.{relation}")
    return ".".join((catalog, *parts))


def runtime_name(dataset_id: str, suffix: str) -> str:
    """Build a deterministic pipeline object/function name from a dataset id."""

    value = re.sub(r"[^A-Za-z0-9_]", "_", f"{dataset_id}_{suffix}")
    if not value or value[0].isdigit():
        value = f"edp_{value}"
    return value
