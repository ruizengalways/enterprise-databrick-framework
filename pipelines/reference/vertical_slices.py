from __future__ import annotations

from pathlib import Path

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

registry = PatternRegistry()
for spec in load_table_specs(bundle_root / "config" / "tables" / "reference"):
    if not spec.enabled or spec.pattern_id not in implemented_builtin_patterns():
        continue
    registry.validate(spec)
    build_builtin_runtime(
        spec,
        RuntimeContext(
            spark=spark,
            pipelines=dp,
            environment=environment,
            catalog=catalog,
        ),
    )
