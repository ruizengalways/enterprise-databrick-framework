from __future__ import annotations

import re
from typing import Any

from edp_framework.operations.control_tables import ensure_control_tables
from edp_framework.reconciliation.models import ReconciliationReport

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _catalog(value: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"unsafe Unity Catalog identifier: {value!r}")
    return value


def persist_reconciliation_report(
    spark: Any,
    catalog: str,
    report: ReconciliationReport,
    *,
    ensure_schema: bool = False,
) -> None:
    """Append one completed report to the framework reconciliation control tables."""

    safe_catalog = _catalog(catalog)
    if ensure_schema:
        ensure_control_tables(spark, safe_catalog)

    run_rows = [
        {
            "reconciliation_run_id": report.reconciliation_run_id,
            "dataset_id": report.dataset_id,
            "cutoff_type": report.cutoff_type,
            "cutoff_value": report.cutoff_value,
            "started_at": report.started_at,
            "ended_at": report.ended_at,
            "status": report.status,
        }
    ]
    spark.createDataFrame(run_rows).write.mode("append").saveAsTable(
        f"{safe_catalog}.platform_control.reconciliation_run"
    )

    if not report.results:
        return

    result_rows = [
        {
            "reconciliation_run_id": report.reconciliation_run_id,
            "rule_name": result.rule_name,
            "rule_kind": result.rule_kind,
            "expected_value": result.expected_value,
            "actual_value": result.actual_value,
            "variance": result.variance,
            "severity": result.severity,
            "passed": result.passed,
            "details": result.details,
        }
        for result in report.results
    ]
    spark.createDataFrame(result_rows).write.mode("append").saveAsTable(
        f"{safe_catalog}.platform_control.reconciliation_result"
    )
