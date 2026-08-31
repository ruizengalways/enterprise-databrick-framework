from __future__ import annotations

from collections.abc import Callable
from typing import Any

from edp_framework.metadata.models import DQAction, QualityRule


def rules_for_action(rules: list[QualityRule], action: DQAction) -> list[QualityRule]:
    return [rule for rule in rules if rule.action is action]


def valid_expression(rules: list[QualityRule]) -> str | None:
    """Return a SQL predicate retaining rows that satisfy all supplied rules."""

    if not rules:
        return None
    return " AND ".join(f"({rule.expression})" for rule in rules)


def invalid_expression(rules: list[QualityRule]) -> str | None:
    """Return a SQL predicate selecting rows that violate any supplied rule."""

    if not rules:
        return None
    return " OR ".join(f"NOT ({rule.expression})" for rule in rules)


def decorate_expectations(
    dp: Any,
    function: Callable[[], Any],
    rules: list[QualityRule],
) -> Callable[[], Any]:
    """Attach WARN and FAIL expectations without changing quarantine semantics."""

    decorated = function
    for rule in rules_for_action(rules, DQAction.WARN):
        decorated = dp.expect(rule.name, rule.expression)(decorated)
    for rule in rules_for_action(rules, DQAction.FAIL):
        decorated = dp.expect_or_fail(rule.name, rule.expression)(decorated)
    return decorated
