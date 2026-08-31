from __future__ import annotations

from edp_framework.metadata.models import ReconciliationRule, TableSpec

_KEY_RULE_KINDS = frozenset(
    {
        "key_count",
        "pk_presence",
        "scd2_current_uniqueness",
        "scd2_no_overlap",
    }
)


def rule_keys(rule: ReconciliationRule) -> tuple[str, ...] | None:
    configured = rule.options.get("keys")
    if configured is None:
        return None
    if (
        not isinstance(configured, list)
        or not configured
        or not all(isinstance(value, str) and value.strip() for value in configured)
    ):
        raise ValueError(
            f"reconciliation rule {rule.name}: options.keys must be a non-empty list of column names"
        )
    return tuple(configured)


def validate_reconciliation_contract(spec: TableSpec) -> None:
    """Fail metadata validation before runtime for executable reconciliation mistakes."""

    if not spec.reconciliation.enabled:
        return

    for rule in spec.reconciliation.rules:
        keys = rule_keys(rule)
        if rule.kind in _KEY_RULE_KINDS and not (keys or spec.identity.business_keys):
            raise ValueError(
                f"{spec.dataset_id}: reconciliation rule {rule.name} requires keys; declare "
                "rule.options.keys when reconciliation identity differs from business identity"
            )

        tolerance_mode = rule.options.get("tolerance_mode", "absolute")
        if tolerance_mode not in {"absolute", "relative"}:
            raise ValueError(
                f"{spec.dataset_id}: reconciliation rule {rule.name} has unsupported "
                f"tolerance_mode {tolerance_mode!r}"
            )

        if rule.kind == "aggregate":
            expression = rule.options.get("expression")
            if not isinstance(expression, str) or not expression.strip():
                raise ValueError(
                    f"{spec.dataset_id}: aggregate reconciliation rule {rule.name} requires "
                    "options.expression"
                )

        if rule.kind in {"scd2_current_uniqueness", "scd2_no_overlap"}:
            for option_name in ("start_column", "end_column"):
                if option_name not in rule.options:
                    continue
                value = rule.options[option_name]
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f"{spec.dataset_id}: reconciliation rule {rule.name} "
                        f"options.{option_name} must be a non-empty column name"
                    )
