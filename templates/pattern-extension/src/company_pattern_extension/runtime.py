from __future__ import annotations

from edp_framework.metadata.models import TableSpec
from edp_framework.patterns.contracts import RuntimeContext


def register_runtime(spec: TableSpec, context: RuntimeContext) -> None:
    """Register the Databricks declarative graph for this extension pattern.

    Replace the body with the vendor/source-specific implementation. `context.spark` and
    `context.pipelines` are injected by the platform so this package does not need to alter
    core routing code. This template deliberately fails until an implementation is supplied;
    a new semantic pattern must never become deployable merely because validation exists.
    """

    raise NotImplementedError(
        f"Implement runtime for {spec.pattern_id} in company_pattern_extension.runtime"
    )
