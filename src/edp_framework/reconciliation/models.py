from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class ReconciliationContext:
    """Comparable source/target relations materialized at one explicit cutoff."""

    cutoff_type: str
    cutoff_value: str
    source_relation: str
    target_relation: str
    business_keys: tuple[str, ...] = ()
    observed_target_position: str | None = None


@dataclass(frozen=True)
class ReconciliationResult:
    rule_name: str
    rule_kind: str
    expected_value: str | None
    actual_value: str | None
    variance: float | None
    severity: Literal["warn", "fail"]
    passed: bool
    details: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ReconciliationReport:
    reconciliation_run_id: str
    dataset_id: str
    cutoff_type: str
    cutoff_value: str
    started_at: datetime
    ended_at: datetime
    status: Literal["passed", "warning", "failed", "skipped"]
    results: tuple[ReconciliationResult, ...]

    @property
    def passed(self) -> bool:
        return self.status in {"passed", "skipped"}
