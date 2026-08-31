from __future__ import annotations

import re
from typing import Any, Protocol

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _column(value: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"unsafe reconciliation column: {value!r}")
    return value


class ReconciliationMeasureProvider(Protocol):
    """Measurement boundary used by the pure reconciliation decision engine."""

    def row_count(self, relation: str) -> int: ...

    def distinct_key_count(self, relation: str, keys: tuple[str, ...]) -> int: ...

    def missing_key_count(
        self,
        source_relation: str,
        target_relation: str,
        keys: tuple[str, ...],
    ) -> int: ...

    def numeric_scalar(self, relation: str, expression: str) -> float: ...

    def current_duplicate_key_count(
        self,
        relation: str,
        keys: tuple[str, ...],
        end_column: str,
    ) -> int: ...

    def scd2_overlap_count(
        self,
        relation: str,
        keys: tuple[str, ...],
        start_column: str,
        end_column: str,
    ) -> int: ...


class SparkMeasureProvider:
    """Spark-backed measurements over relations already aligned to the same cutoff."""

    def __init__(self, spark: Any) -> None:
        self.spark = spark

    def row_count(self, relation: str) -> int:
        return int(self.spark.table(relation).count())

    def distinct_key_count(self, relation: str, keys: tuple[str, ...]) -> int:
        if not keys:
            raise ValueError("distinct key reconciliation requires at least one key")
        safe = [_column(key) for key in keys]
        return int(self.spark.table(relation).select(*safe).distinct().count())

    def missing_key_count(
        self,
        source_relation: str,
        target_relation: str,
        keys: tuple[str, ...],
    ) -> int:
        if not keys:
            raise ValueError("PK presence reconciliation requires at least one key")
        safe = [_column(key) for key in keys]
        source = self.spark.table(source_relation).select(*safe).distinct()
        target = self.spark.table(target_relation).select(*safe).distinct()
        return int(source.join(target, safe, "left_anti").count())

    def numeric_scalar(self, relation: str, expression: str) -> float:
        if not expression.strip():
            raise ValueError("aggregate reconciliation requires a non-empty expression")
        # Reconciliation expressions are reviewed Git metadata, not end-user input. The provider
        # intentionally evaluates them through Spark SQL after the relation/cutoff is fixed.
        row = self.spark.table(relation).selectExpr(
            f"CAST(({expression}) AS DOUBLE) AS _reconciliation_value"
        ).first()
        if row is None or row[0] is None:
            raise ValueError(
                f"aggregate reconciliation expression returned NULL for relation {relation!r}"
            )
        return float(row[0])

    def current_duplicate_key_count(
        self,
        relation: str,
        keys: tuple[str, ...],
        end_column: str,
    ) -> int:
        if not keys:
            raise ValueError("SCD2 current uniqueness requires at least one key")
        safe_keys = [_column(key) for key in keys]
        safe_end = _column(end_column)
        current = self.spark.table(relation).where(f"`{safe_end}` IS NULL")
        duplicates = current.groupBy(*safe_keys).count().where("count > 1")
        return int(duplicates.count())

    def scd2_overlap_count(
        self,
        relation: str,
        keys: tuple[str, ...],
        start_column: str,
        end_column: str,
    ) -> int:
        if not keys:
            raise ValueError("SCD2 overlap reconciliation requires at least one key")
        safe_keys = [_column(key) for key in keys]
        safe_start = _column(start_column)
        safe_end = _column(end_column)

        from pyspark.sql import Window
        from pyspark.sql.functions import col, lag, row_number

        window = Window.partitionBy(*safe_keys).orderBy(col(safe_start))
        ordered = (
            self.spark.table(relation)
            .select(*safe_keys, safe_start, safe_end)
            .withColumn("_reconciliation_row_number", row_number().over(window))
            .withColumn("_reconciliation_previous_end", lag(col(safe_end)).over(window))
        )
        overlaps = ordered.where(
            (col("_reconciliation_row_number") > 1)
            & (
                col("_reconciliation_previous_end").isNull()
                | (col("_reconciliation_previous_end") > col(safe_start))
            )
        )
        return int(overlaps.count())
