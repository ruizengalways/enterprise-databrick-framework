from __future__ import annotations

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
        self.scalars = {"source.orders": 2.0, "silver.orders": 2.0}
        self.categories = {
            "source.orders": {"c": 1, "u": 2, "d": 1},
            "silver.orders": {"c": 1, "u": 2, "d": 1},
        }
        self.missing = 0
        self.duplicates = 0
        self.overlaps = 0
        self.seen_keys: list[tuple[str, ...]] = []
        self.seen_expression: str | None = None
        self.seen_category_column: str | None = None

    def row_count(self, relation: str) -> int:
        return self.rows[relation]

    def distinct_key_count(self, relation: str, keys: tuple[str, ...]) -> int:
        self.seen_keys.append(keys)
        return self.keys[relation]

    def missing_key_count(
        self,
        source_relation: str,
        target_relation: str,
        keys: tuple[str, ...],
    ) -> int:
        assert (source_relation, target_relation) == ("source.orders", "silver.orders")
        self.seen_keys.append(keys)
        return self.missing

    def numeric_scalar(self, relation: str, expression: str) -> float:
        self.seen_expression = expression
        return self.scalars[relation]

    def categorical_counts(self, relation: str, column: str) -> dict[str, int]:
        self.seen_category_column = column
        return self.categories[relation]

    def current_duplicate_key_count(
        self,
        relation: str,
        keys: tuple[str, ...],
        end_column: str,
    ) -> int:
        assert relation == "silver.orders"
        assert end_column == "__END_AT"
        self.seen_keys.append(keys)
        return self.duplicates

    def scd2_overlap_count(
        self,
        relation: str,
        keys: tuple[str, ...],
        start_column: str,
        end_column: str,
    ) -> int:
        assert relation == "silver.orders"
        assert start_column == "__START_AT"
        assert end_column == "__END_AT"
        self.seen_keys.append(keys)
        return self.overlaps


def context(
    *,
    position: str | None = "42",
    business_keys: tuple[str, ...] = ("order_id",),
) -> ReconciliationContext:
    return ReconciliationContext(
        cutoff_type="source_position",
        cutoff_value="42",
        source_relation="source.orders",
        target_relation="silver.orders",
        business_keys=business_keys,
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
    row_rule = spec.reconciliation.rules[1].model_copy(update={"severity": "warn"})
    spec = spec.model_copy(
        update={
            "reconciliation": spec.reconciliation.model_copy(
                update={"rules": [spec.reconciliation.rules[0], row_rule]}
            )
        }
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


def test_key_pk_and_scd2_measurements_are_supported() -> None:
    spec = p12_spec()
    rules = [
        ReconciliationRule(name="keys", kind="key_count"),
        ReconciliationRule(name="presence", kind="pk_presence"),
        ReconciliationRule(name="current", kind="scd2_current_uniqueness"),
        ReconciliationRule(name="overlap", kind="scd2_no_overlap"),
    ]
    spec = spec.model_copy(
        update={"reconciliation": spec.reconciliation.model_copy(update={"rules": rules})}
    )
    provider = FakeProvider()
    report = evaluate_reconciliation(spec, context(), provider)
    assert report.status == "passed"
    assert len(report.results) == 4
    assert provider.seen_keys == [("order_id",)] * 5


def test_aggregate_compares_same_reviewed_expression_at_same_cutoff() -> None:
    spec = p12_spec()
    rule = ReconciliationRule(
        name="deleted_count",
        kind="aggregate",
        options={"expression": "sum(case when is_deleted then 1 else 0 end)"},
    )
    spec = spec.model_copy(
        update={"reconciliation": spec.reconciliation.model_copy(update={"rules": [rule]})}
    )
    provider = FakeProvider()
    report = evaluate_reconciliation(spec, context(), provider)
    assert report.status == "passed"
    assert provider.seen_expression == "sum(case when is_deleted then 1 else 0 end)"


def test_operation_count_compares_normalized_category_distribution() -> None:
    spec = p12_spec()
    rule = ReconciliationRule(
        name="operations",
        kind="operation_count",
        options={"operation_column": "_operation"},
    )
    spec = spec.model_copy(
        update={"reconciliation": spec.reconciliation.model_copy(update={"rules": [rule]})}
    )
    provider = FakeProvider()
    report = evaluate_reconciliation(spec, context(), provider)
    result = report.results[0]
    assert report.status == "passed"
    assert provider.seen_category_column == "_operation"
    assert result.expected_value == '{"c":1,"d":1,"u":2}'
    assert result.actual_value == '{"c":1,"d":1,"u":2}'
    assert result.variance == 0.0


def test_operation_count_reports_per_category_drift() -> None:
    spec = p12_spec()
    rule = ReconciliationRule(
        name="operations",
        kind="operation_count",
        options={"operation_column": "_operation"},
    )
    spec = spec.model_copy(
        update={"reconciliation": spec.reconciliation.model_copy(update={"rules": [rule]})}
    )
    provider = FakeProvider()
    provider.categories["silver.orders"] = {"c": 1, "u": 1, "d": 2}
    report = evaluate_reconciliation(spec, context(), provider)
    result = report.results[0]
    assert report.status == "failed"
    assert result.variance == 2.0
    assert result.details["category_variance"] == '{"c":0,"d":1,"u":-1}'


def test_rule_specific_keys_do_not_require_business_identity() -> None:
    spec = load_table_spec(ROOT / "examples/table_specs/country.yml")
    provider = FakeProvider()
    report = evaluate_reconciliation(spec, context(business_keys=()), provider)
    assert report.status == "passed"
    assert provider.seen_keys == [("country_code",), ("country_code",)]


def test_scd2_overlap_violation_fails_report() -> None:
    spec = p12_spec()
    rule = ReconciliationRule(name="overlap", kind="scd2_no_overlap")
    spec = spec.model_copy(
        update={"reconciliation": spec.reconciliation.model_copy(update={"rules": [rule]})}
    )
    provider = FakeProvider()
    provider.overlaps = 1
    report = evaluate_reconciliation(spec, context(), provider)
    assert report.status == "failed"
    assert report.results[0].actual_value == "1"


def test_unimplemented_hash_rule_fails_explicitly_instead_of_false_pass() -> None:
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
