from __future__ import annotations

import re

_RELATION_PART = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def qualify_relation(catalog: str, relation: str) -> str:
    """Return a safe three-part Unity Catalog relation.

    Table metadata intentionally stores `schema.table` so the same Git commit can be promoted
    to a different environment catalog without rewriting table contracts.
    """

    parts = relation.split(".")
    if len(parts) != 2:
        raise ValueError(f"relation must be schema.table, got {relation!r}")
    if not _RELATION_PART.fullmatch(catalog) or not all(_RELATION_PART.fullmatch(p) for p in parts):
        raise ValueError(f"unsafe Unity Catalog relation: {catalog}.{relation}")
    return ".".join((catalog, *parts))


def runtime_name(dataset_id: str, suffix: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]", "_", f"{dataset_id}_{suffix}")
    if not value or value[0].isdigit():
        value = f"edp_{value}"
    return value
