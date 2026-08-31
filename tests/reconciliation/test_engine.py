from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from edp_framework.metadata.loader import load_table_spec
from edp_framework.metadata.models import ReconciliationRule
from edp_framework.reconciliation import ReconciliationContext, evaluate_reconciliation

ROOT = Path(__file__).resolve().parents[2]


class FakeProvider:
    def __init__(self) -> None:
        self.rows = {"source.orders": 4, "silver.orders": 4}
        self.keys = {"source.orders": 3, "silver.orders": 3}
        self.missing = 0
        self.duplicates = 0

    def row_count(self, relation: str) -> int:
        return self.rows[relation]

    def distinct_key_count(self, relation: str, keys: tuple[str, ...]) -> int:
        assert keys == ("order_id",)
        return self.keys[relation]

    def missing_key_count(
        self,
        source_relation: str,
        target_relation: str,
        keys: tuple[str, ...],
    ) -> int:
        assert (source_relation, target_relation, keys) == (
            "source.orders",
            "silver.orders",
            ("order_id",),
        )
        return self.missing

    def current_duplicate_key_count(
        self,
        relation: str,
        keys: tuple[str, ...],
        end_column: str,
    ) -> int:
        assert relation == "silver.orders"
        assert keys == ("order_id",)
        assert end_column == "__END_AT"
        return self.duplicates


def context(*, position: str | None = "42") -> ReconciliationContext:
    return ReconciliationContext(
        cutoff_type="source_position",
        cutoff_value="42",
        source_relation="source.orders",
        target_relation="silver.orders",
        business_keys=("order_id",),
        observed_target_position=position,
    )


def p12_spec():
    return load_table_spec(ROOT / "examples/table_specs/order_events.yml")


def test_row_count_and_source_position_pass_at_same_cutoff() -> None:
    report = evaluate_reconciliation(
        p12_spec(),
        context(),
        FakeProvider(),
        reconciliation_run_id="recon-1",
    )
    assert report.status == "passed"
    assert report.passed is True
    assert {result.rule_kind for result in report.results} == {"row_count", "source_position"}


def test_fail_severity_mismatch_fails_report() -> None:
    provider = FakeProvider()
    provider.rows["silver.orders"] = 2
    report = evaluate_reconciliation(p12_spec(), context(), provider)
    assert report.status == "failed"
    row_count = next(result for result in report.results if result.rule_kind == "row_count")
    assert row_count.passed is False
    assert row_count.variance == 2.0


def test_warn_only_mismatch_yields_warning_not_failure() -> None:
    spec = p12_spec()
    row_rule = replace(spec.reconciliation.rules[1], severity="warn")
    spec = spec.model_copy(
        update={"reconciliation": spec.reconciliation.model_copy(update={"rules": [spec.reconciliation.rules[0], row_rule]})}
    )
    provider = FakeProvider()
    provider.rows["silver.orders"] = 3
    report = evaluate_reconciliation(spec, context(), provider)
    assert report.status == "warning"
    assert report.passed is False


def test_source_position_requires_exact_observed_cutoff() -> None:
    report = evaluate_reconciliation(p12_spec(), context(position="41"), FakeProvider())
    position = next(result for result in report.results if result.rule_kind == "source_position")
    assert position.passed is False
    assert report.status == "failed"


def test_key_and_pk_and_scd2_uniqueness_measurements_are_supported() -> None:
    spec = p12_spec()
    rules = [
        ReconciliationRule(name="keys", kind="key_count"),
        ReconciliationRule(name="presence", kind="pk_presence"),
        ReconciliationRule(name="current", kind="scd2_current_uniqueness"),
    ]
    spec = spec.model_copy(
        update={"reconciliation": spec.reconciliation.model_copy(update={"rules": rules})}
    )
    report = evaluate_reconciliation(spec, context(), FakeProvider())
    assert report.status == "passed"
    assert len(report.results) == 3


def test_unimplemented_rule_fails_explicitly_instead_of_false_pass() -> None:
    spec = p12_spec()
    rule = ReconciliationRule(name="hash", kind="hash")
    spec = spec.model_copy(
        update={"reconciliation": spec.reconciliation.model_copy(update={"rules": [rule]})}
    )
    with pytest.raises(NotImplementedError, match="not implemented"):
        evaluate_reconciliation(spec, context(), FakeProvider())


def test_reconciliation_requires_explicit_cutoff() -> None:
    with pytest.raises(ValueError, match="explicit cutoff"):
        evaluate_reconciliation(
            p12_spec(),
            ReconciliationContext(
                cutoff_type="source_position",
                cutoff_value="",
                source_relation="source.orders",
                target_relation="silver.orders",
            ),
            FakeProvider(),
        )
