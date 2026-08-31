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

    def current_duplicate_key_count(
        self,
        relation: str,
        keys: tuple[str, ...],
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
            raise ValueError("distinct key reconciliation requires at least one business key")
        safe = [_column(key) for key in keys]
        return int(self.spark.table(relation).select(*safe).distinct().count())

    def missing_key_count(
        self,
        source_relation: str,
        target_relation: str,
        keys: tuple[str, ...],
    ) -> int:
        if not keys:
            raise ValueError("PK presence reconciliation requires at least one business key")
        safe = [_column(key) for key in keys]
        source = self.spark.table(source_relation).select(*safe).distinct()
        target = self.spark.table(target_relation).select(*safe).distinct()
        return int(source.join(target, safe, "left_anti").count())

    def current_duplicate_key_count(
        self,
        relation: str,
        keys: tuple[str, ...],
        end_column: str,
    ) -> int:
        if not keys:
            raise ValueError("SCD2 current uniqueness requires at least one business key")
        safe_keys = [_column(key) for key in keys]
        safe_end = _column(end_column)
        current = self.spark.table(relation).where(f"`{safe_end}` IS NULL")
        duplicates = current.groupBy(*safe_keys).count().where("count > 1")
        return int(duplicates.count())
