from __future__ import annotations

import pytest

from edp_framework.metadata.models import DQAction, QualityRule
from edp_framework.runtime.builtin import implemented_builtin_patterns
from edp_framework.runtime.names import qualify_relation, runtime_name
from edp_framework.runtime.quality import invalid_expression, valid_expression


def test_qualify_relation_is_environment_portable() -> None:
    assert qualify_relation("edp_prod", "silver.crm_customer") == "edp_prod.silver.crm_customer"
    with pytest.raises(ValueError, match="schema.table"):
        qualify_relation("edp_prod", "crm_customer")
    with pytest.raises(ValueError, match="unsafe"):
        qualify_relation("edp_prod;DROP", "silver.crm_customer")


def test_runtime_name_is_safe() -> None:
    assert runtime_name("sales.customer_history", "scd2") == "sales_customer_history_scd2"


def test_first_vertical_slice_runtime_handlers_are_explicit() -> None:
    assert implemented_builtin_patterns() == frozenset({"P01", "P02", "P07", "P10", "P12"})


def test_quality_expressions_are_composed_without_rewriting_rules() -> None:
    rules = [
        QualityRule(name="email", expression="email LIKE '%@%'", action=DQAction.QUARANTINE),
        QualityRule(name="status", expression="status IN ('A','B')", action=DQAction.QUARANTINE),
    ]
    assert valid_expression(rules) == "(email LIKE '%@%') AND (status IN ('A','B'))"
    assert invalid_expression(rules) == "NOT (email LIKE '%@%') OR NOT (status IN ('A','B'))"
