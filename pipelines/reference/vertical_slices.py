from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from pyspark import pipelines as dp
from pyspark.sql import SparkSession

from edp_framework.metadata.loader import load_table_specs
from edp_framework.patterns.contracts import RuntimeContext
from edp_framework.patterns.registry import PatternRegistry
from edp_framework.runtime.builtin import build_builtin_runtime, implemented_builtin_patterns

spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
catalog = spark.conf.get("edp.catalog")
environment = spark.conf.get("edp.environment")
bundle_root = Path(spark.conf.get("edp.bundle_root"))


def transform_order_events(frame: Any) -> Any:
    """Reference business mapping.

    This stays outside core because deciding the canonical order-event payload is domain logic,
    not a reusable P12 mechanism.
    """

    return frame.select("event_id", "order_id", "event_type", "event_time", "payload")


DOMAIN_TRANSFORMS: dict[str, Callable[[Any], Any]] = {
    "commerce.order_events": transform_order_events,
}

registry = PatternRegistry()
for spec in load_table_specs(bundle_root / "config" / "tables" / "reference"):
    if not spec.enabled or spec.pattern_id not in implemented_builtin_patterns():
        continue
    registry.validate(spec)
    options: dict[str, Any] = {}
    transform = DOMAIN_TRANSFORMS.get(spec.dataset_id)
    if transform is not None:
        options["transform"] = transform
    build_builtin_runtime(
        spec,
        RuntimeContext(
            spark=spark,
            pipelines=dp,
            environment=environment,
            catalog=catalog,
            options=options,
        ),
    )
