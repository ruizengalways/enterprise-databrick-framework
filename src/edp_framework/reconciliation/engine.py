from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from edp_framework.metadata.models import ReconciliationRule, TableSpec
from edp_framework.reconciliation.models import (
    ReconciliationContext,
    ReconciliationReport,
    ReconciliationResult,
)
from edp_framework.reconciliation.provider import ReconciliationMeasureProvider

SUPPORTED_RULE_KINDS = frozenset(
    {
        "row_count",
        "key_count",
        "pk_presence",
        "aggregate",
        "source_position",
        "scd2_current_uniqueness",
        "scd2_no_overlap",
    }
)


def _numeric_result(
    rule: ReconciliationRule,
    *,
    expected: float | int,
    actual: float | int,
) -> ReconciliationResult:
    variance = float(abs(actual - expected))
    tolerance_mode = str(rule.options.get("tolerance_mode", "absolute"))
    if tolerance_mode == "absolute":
        compared_variance = variance
    elif tolerance_mode == "relative":
        compared_variance = variance / max(float(abs(expected)), 1.0)
    else:
        raise ValueError(
            f"reconciliation rule {rule.name}: unsupported tolerance_mode {tolerance_mode!r}"
        )

    return ReconciliationResult(
        rule_name=rule.name,
        rule_kind=rule.kind,
        expected_value=str(expected),
        actual_value=str(actual),
        variance=variance,
        severity=rule.severity,
        passed=compared_variance <= rule.tolerance,
        details={
            "tolerance": str(rule.tolerance),
            "tolerance_mode": tolerance_mode,
            "compared_variance": str(compared_variance),
        },
    )


def _rule_keys(
    spec: TableSpec,
    context: ReconciliationContext,
    rule: ReconciliationRule,
) -> tuple[str, ...]:
    configured = rule.options.get("keys")
    if configured is not None:
        if (
            not isinstance(configured, list)
            or not configured
            or not all(isinstance(value, str) and value.strip() for value in configured)
        ):
            raise ValueError(
                f"{spec.dataset_id}: reconciliation rule {rule.name} options.keys must be "
                "a non-empty list of column names"
            )
        return tuple(configured)

    keys = context.business_keys or tuple(spec.identity.business_keys)
    if not keys:
        raise ValueError(
            f"{spec.dataset_id}: reconciliation rule {rule.name} requires keys; declare "
            "rule.options.keys when reconciliation identity differs from business identity"
        )
    return keys


def _required_expression(spec: TableSpec, rule: ReconciliationRule) -> str:
    expression = rule.options.get("expression")
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError(
            f"{spec.dataset_id}: aggregate reconciliation rule {rule.name} requires "
            "options.expression"
        )
    return expression


def _evaluate_rule(
    spec: TableSpec,
    context: ReconciliationContext,
    provider: ReconciliationMeasureProvider,
    rule: ReconciliationRule,
) -> ReconciliationResult:
    if rule.kind not in SUPPORTED_RULE_KINDS:
        raise NotImplementedError(
            f"reconciliation rule kind {rule.kind!r} is declared in metadata but is not "
            "implemented by the reusable v2 engine; use an extension/runner rather than "
            "silently treating it as passed"
        )

    if rule.kind == "row_count":
        return _numeric_result(
            rule,
            expected=provider.row_count(context.source_relation),
            actual=provider.row_count(context.target_relation),
        )

    if rule.kind == "key_count":
        keys = _rule_keys(spec, context, rule)
        return _numeric_result(
            rule,
            expected=provider.distinct_key_count(context.source_relation, keys),
            actual=provider.distinct_key_count(context.target_relation, keys),
        )

    if rule.kind == "pk_presence":
        keys = _rule_keys(spec, context, rule)
        return _numeric_result(
            rule,
            expected=0,
            actual=provider.missing_key_count(
                context.source_relation,
                context.target_relation,
                keys,
            ),
        )

    if rule.kind == "aggregate":
        expression = _required_expression(spec, rule)
        return _numeric_result(
            rule,
            expected=provider.numeric_scalar(context.source_relation, expression),
            actual=provider.numeric_scalar(context.target_relation, expression),
        )

    if rule.kind == "scd2_current_uniqueness":
        keys = _rule_keys(spec, context, rule)
        end_column = str(rule.options.get("end_column", "__END_AT"))
        return _numeric_result(
            rule,
            expected=0,
            actual=provider.current_duplicate_key_count(
                context.target_relation,
                keys,
                end_column,
            ),
        )

    if rule.kind == "scd2_no_overlap":
        keys = _rule_keys(spec, context, rule)
        start_column = str(rule.options.get("start_column", "__START_AT"))
        end_column = str(rule.options.get("end_column", "__END_AT"))
        return _numeric_result(
            rule,
            expected=0,
            actual=provider.scd2_overlap_count(
                context.target_relation,
                keys,
                start_column,
                end_column,
            ),
        )

    actual_position = context.observed_target_position
    passed = actual_position is not None and actual_position == context.cutoff_value
    return ReconciliationResult(
        rule_name=rule.name,
        rule_kind=rule.kind,
        expected_value=context.cutoff_value,
        actual_value=actual_position,
        variance=None,
        severity=rule.severity,
        passed=passed,
        details={"cutoff_type": context.cutoff_type},
    )


def evaluate_reconciliation(
    spec: TableSpec,
    context: ReconciliationContext,
    provider: ReconciliationMeasureProvider,
    *,
    reconciliation_run_id: str | None = None,
) -> ReconciliationReport:
    """Evaluate enabled metadata rules against relations aligned to one explicit cutoff.

    The framework deliberately does not discover or advance source positions here. The consuming
    workload must first materialize/resolve source and target views representing the same cutoff.
    """

    started = datetime.now(timezone.utc)
    if not context.cutoff_type.strip() or not context.cutoff_value.strip():
        raise ValueError(f"{spec.dataset_id}: reconciliation requires an explicit cutoff")

    run_id = reconciliation_run_id or str(uuid4())
    if not spec.reconciliation.enabled:
        ended = datetime.now(timezone.utc)
        return ReconciliationReport(
            reconciliation_run_id=run_id,
            dataset_id=spec.dataset_id,
            cutoff_type=context.cutoff_type,
            cutoff_value=context.cutoff_value,
            started_at=started,
            ended_at=ended,
            status="skipped",
            results=(),
        )

    results = tuple(
        _evaluate_rule(spec, context, provider, rule) for rule in spec.reconciliation.rules
    )
    fail_results = [result for result in results if not result.passed and result.severity == "fail"]
    warn_results = [result for result in results if not result.passed and result.severity == "warn"]
    status: Literal["passed", "warning", "failed", "skipped"]
    if fail_results:
        status = "failed"
    elif warn_results:
        status = "warning"
    else:
        status = "passed"

    ended = datetime.now(timezone.utc)
    return ReconciliationReport(
        reconciliation_run_id=run_id,
        dataset_id=spec.dataset_id,
        cutoff_type=context.cutoff_type,
        cutoff_value=context.cutoff_value,
        started_at=started,
        ended_at=ended,
        status=status,
        results=results,
    )
