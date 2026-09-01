from __future__ import annotations

from pathlib import Path

import pytest

from edp_framework.metadata.loader import load_table_spec
from edp_framework.metadata.models import ReconciliationRule
from edp_framework.patterns.registry import PatternRegistry

ROOT = Path(__file__).resolve().parents[2]


def validate(spec) -> None:
    PatternRegistry(load_plugins=False).validate(spec)


def test_p01_rule_specific_key_validates_without_business_identity() -> None:
    spec = load_table_spec(ROOT / "examples/table_specs/country.yml")
    validate(spec)


def test_key_rule_without_business_or_rule_keys_fails_before_runtime() -> None:
    spec = load_table_spec(ROOT / "examples/table_specs/country.yml")
    key_rule = spec.reconciliation.rules[1].model_copy(update={"options": {}})
    spec = spec.model_copy(
        update={
            "reconciliation": spec.reconciliation.model_copy(
                update={"rules": [spec.reconciliation.rules[0], key_rule]}
            )
        }
    )
    with pytest.raises(ValueError, match="requires keys"):
        validate(spec)


def test_aggregate_rule_requires_expression_before_runtime() -> None:
    spec = load_table_spec(ROOT / "examples/table_specs/order_events.yml")
    rule = ReconciliationRule(name="aggregate", kind="aggregate")
    spec = spec.model_copy(
        update={"reconciliation": spec.reconciliation.model_copy(update={"rules": [rule]})}
    )
    with pytest.raises(ValueError, match="options.expression"):
        validate(spec)


def test_operation_count_rule_requires_explicit_operation_column() -> None:
    spec = load_table_spec(ROOT / "examples/table_specs/order_events.yml")
    rule = ReconciliationRule(name="operations", kind="operation_count")
    spec = spec.model_copy(
        update={"reconciliation": spec.reconciliation.model_copy(update={"rules": [rule]})}
    )
    with pytest.raises(ValueError, match="options.operation_column"):
        validate(spec)


def test_operation_count_rule_validates_with_normalized_operation_column() -> None:
    spec = load_table_spec(ROOT / "examples/table_specs/order_events.yml")
    rule = ReconciliationRule(
        name="operations",
        kind="operation_count",
        options={"operation_column": "_operation"},
    )
    spec = spec.model_copy(
        update={"reconciliation": spec.reconciliation.model_copy(update={"rules": [rule]})}
    )
    validate(spec)


def test_invalid_tolerance_mode_fails_before_runtime() -> None:
    spec = load_table_spec(ROOT / "examples/table_specs/order_events.yml")
    rule = ReconciliationRule(
        name="count",
        kind="row_count",
        options={"tolerance_mode": "approximately"},
    )
    spec = spec.model_copy(
        update={"reconciliation": spec.reconciliation.model_copy(update={"rules": [rule]})}
    )
    with pytest.raises(ValueError, match="unsupported tolerance_mode"):
        validate(spec)
