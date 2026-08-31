from __future__ import annotations

import argparse
import re
from typing import Any

from pyspark.sql import SparkSession

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _scalar(spark: Any, sql: str) -> Any:
    return spark.sql(sql).first()[0]


def verify_reference_verticals(spark: Any, catalog: str) -> None:
    if not _IDENTIFIER.fullmatch(catalog):
        raise ValueError(f"unsafe catalog identifier: {catalog!r}")

    checks: list[tuple[str, Any, Any]] = [
        ("P01 country row count", _scalar(spark, f"SELECT count(*) FROM {catalog}.silver.reference_country"), 3),
        ("P07 current customer count", _scalar(spark, f"SELECT count(*) FROM {catalog}.silver.crm_customer_current"), 2),
        ("P07 latest customer", _scalar(spark, f"SELECT name FROM {catalog}.silver.crm_customer_current WHERE customer_id=100"), "Alice Smith"),
        ("P07 soft delete", _scalar(spark, f"SELECT is_deleted FROM {catalog}.silver.crm_customer_current WHERE customer_id=200"), True),
        ("P07 quarantine", _scalar(spark, f"SELECT count(*) FROM {catalog}.quarantine.crm_customer"), 1),
        ("P10 current SCD2 row", _scalar(spark, f"SELECT status FROM {catalog}.silver.sales_customer_history WHERE customer_id=100 AND __END_AT IS NULL"), "GOLD"),
        ("P10 deleted customer closed", _scalar(spark, f"SELECT count(*) FROM {catalog}.silver.sales_customer_history WHERE customer_id=200 AND __END_AT IS NULL"), 0),
        ("P10 quarantine", _scalar(spark, f"SELECT count(*) FROM {catalog}.quarantine.sales_customer_cdc"), 1),
        ("P12 canonical dedup", _scalar(spark, f"SELECT count(*) FROM {catalog}.silver.commerce_order_events"), 3),
        ("P12 quarantine", _scalar(spark, f"SELECT count(*) FROM {catalog}.quarantine.commerce_order_events"), 1),
        ("P02 SCD2 rows", _scalar(spark, f"SELECT count(*) FROM {catalog}.silver.legacy_customer_history"), 5),
        ("P02 current rows", _scalar(spark, f"SELECT count(*) FROM {catalog}.silver.legacy_customer_history WHERE __END_AT IS NULL"), 2),
        ("P02 snapshot delete closed", _scalar(spark, f"SELECT count(*) FROM {catalog}.silver.legacy_customer_history WHERE customer_id=2 AND __END_AT IS NULL"), 0),
    ]
    failures = [f"{name}: expected={expected!r}, actual={actual!r}" for name, actual, expected in checks if actual != expected]
    if failures:
        raise RuntimeError("reference vertical slice verification failed:\n" + "\n".join(failures))
    print(f"[PASS] {len(checks)} reference vertical slice assertions passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    args = parser.parse_args()
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    verify_reference_verticals(spark, args.catalog)


if __name__ == "__main__":
    main()
