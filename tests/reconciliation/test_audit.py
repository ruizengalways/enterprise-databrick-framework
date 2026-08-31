from __future__ import annotations

from datetime import datetime, timezone

import pytest

from edp_framework.reconciliation import (
    ReconciliationReport,
    ReconciliationResult,
    persist_reconciliation_report,
)


class FakeWriter:
    def __init__(self, spark: FakeSpark) -> None:
        self.spark = spark
        self.mode_name: str | None = None

    def mode(self, value: str) -> FakeWriter:
        self.mode_name = value
        return self

    def saveAsTable(self, table: str) -> None:
        self.spark.writes.append((self.mode_name, table))


class FakeFrame:
    def __init__(self, spark: FakeSpark) -> None:
        self.write = FakeWriter(spark)


class FakeSpark:
    def __init__(self) -> None:
        self.created_rows: list[list[dict[str, object]]] = []
        self.writes: list[tuple[str | None, str]] = []

    def createDataFrame(self, rows: list[dict[str, object]]) -> FakeFrame:
        self.created_rows.append(rows)
        return FakeFrame(self)


def report() -> ReconciliationReport:
    now = datetime.now(timezone.utc)
    return ReconciliationReport(
        reconciliation_run_id="recon-1",
        dataset_id="orders",
        cutoff_type="source_position",
        cutoff_value="42",
        started_at=now,
        ended_at=now,
        status="passed",
        results=(
            ReconciliationResult(
                rule_name="row_count",
                rule_kind="row_count",
                expected_value="4",
                actual_value="4",
                variance=0.0,
                severity="fail",
                passed=True,
                details={"tolerance": "0"},
            ),
        ),
    )


def test_audit_writes_only_fixed_control_tables() -> None:
    spark = FakeSpark()
    persist_reconciliation_report(spark, "edp_dev", report())

    assert spark.writes == [
        ("append", "edp_dev.platform_control.reconciliation_run"),
        ("append", "edp_dev.platform_control.reconciliation_result"),
    ]
    assert spark.created_rows[0][0]["dataset_id"] == "orders"
    assert spark.created_rows[1][0]["rule_name"] == "row_count"


def test_audit_rejects_unsafe_catalog_identifier() -> None:
    with pytest.raises(ValueError, match="unsafe Unity Catalog identifier"):
        persist_reconciliation_report(FakeSpark(), "edp_dev; DROP TABLE x", report())
