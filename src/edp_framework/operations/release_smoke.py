from __future__ import annotations

import re
from typing import Any

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_REQUIRED_TABLES = (
    "release_history",
    "pipeline_run",
    "table_run",
    "source_state",
    "reconciliation_run",
    "reconciliation_result",
    "quality_result",
    "repair_request",
    "repair_run",
    "schema_change_event",
    "incident_event",
)


def assert_control_plane_ready(spark: Any, catalog: str) -> tuple[str, ...]:
    if not _IDENTIFIER.fullmatch(catalog):
        raise ValueError(f"unsafe Unity Catalog identifier: {catalog!r}")

    missing = tuple(
        table
        for table in _REQUIRED_TABLES
        if not spark.catalog.tableExists(f"{catalog}.platform_control.{table}")
    )
    if missing:
        raise RuntimeError(f"control plane smoke check failed; missing tables: {', '.join(missing)}")
    return _REQUIRED_TABLES
