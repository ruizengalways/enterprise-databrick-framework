from __future__ import annotations

from collections.abc import Callable
from typing import Any

from edp_framework.metadata.models import DQAction, TableSpec
from edp_framework.patterns.contracts import RuntimeContext
from edp_framework.runtime.names import qualify_relation, runtime_name
from edp_framework.runtime.quality import (
    decorate_expectations,
    invalid_expression,
    rules_for_action,
    valid_expression,
)

RuntimeHandler = Callable[[TableSpec, RuntimeContext, str], None]


def _source_relation(spec: TableSpec, context: RuntimeContext) -> str:
    configured = context.options.get("source_relation") or spec.capture.options.get(
        "reference_source_relation"
    )
    if not isinstance(configured, str) or not configured:
        raise ValueError(
            f"{spec.dataset_id}: runtime source_relation is required; source/capture packages must supply it"
        )
    return qualify_relation(context.catalog, configured)


def _sequence_by(spec: TableSpec) -> Any:
    if spec.ordering is None:
        raise ValueError(f"{spec.dataset_id}: authoritative ordering is required")
    from pyspark.sql.functions import col, struct

    columns = spec.ordering.columns
    if len(columns) == 1:
        return col(columns[0])
    return struct(*columns)


def _register_stream_from_relation(
    spec: TableSpec,
    context: RuntimeContext,
    *,
    target: str,
    source: str,
    quality_rules: bool = False,
) -> None:
    dp = context.pipelines
    spark = context.spark

    def stream() -> Any:
        return spark.readStream.table(source)

    stream.__name__ = runtime_name(spec.dataset_id, target.split(".")[-1])
    function = decorate_expectations(dp, stream, spec.quality.rules) if quality_rules else stream
    dp.table(name=target)(function)


def _register_quarantine(spec: TableSpec, context: RuntimeContext, bronze: str) -> None:
    quarantine_rules = rules_for_action(spec.quality.rules, DQAction.QUARANTINE)
    if not quarantine_rules or not spec.quality.quarantine_table:
        return
    expression = invalid_expression(quarantine_rules)
    assert expression is not None
    target = qualify_relation(context.catalog, spec.quality.quarantine_table)
    dp = context.pipelines
    spark = context.spark

    def quarantine() -> Any:
        return spark.readStream.table(bronze).filter(expression)

    quarantine.__name__ = runtime_name(spec.dataset_id, "quarantine")
    dp.table(name=target, comment=f"Quarantined records for {spec.dataset_id}")(quarantine)


def _register_valid_stream_view(spec: TableSpec, context: RuntimeContext, bronze: str) -> str:
    quarantine_rules = rules_for_action(spec.quality.rules, DQAction.QUARANTINE)
    expression = valid_expression(quarantine_rules)
    name = runtime_name(spec.dataset_id, "valid_stream")
    dp = context.pipelines
    spark = context.spark

    def valid_stream() -> Any:
        frame = spark.readStream.table(bronze)
        return frame.filter(expression) if expression else frame

    valid_stream.__name__ = name
    function = decorate_expectations(dp, valid_stream, spec.quality.rules)
    dp.temporary_view(name=name)(function)
    return name


def register_p01(spec: TableSpec, context: RuntimeContext, source: str) -> None:
    dp = context.pipelines
    spark = context.spark
    bronze = qualify_relation(context.catalog, spec.bronze.table)
    silver = qualify_relation(context.catalog, spec.silver.table)

    def bronze_snapshot() -> Any:
        return spark.read.table(source)

    bronze_snapshot.__name__ = runtime_name(spec.dataset_id, "bronze_snapshot")
    dp.materialized_view(name=bronze)(decorate_expectations(dp, bronze_snapshot, spec.quality.rules))

    def silver_snapshot() -> Any:
        return spark.read.table(bronze)

    silver_snapshot.__name__ = runtime_name(spec.dataset_id, "silver_snapshot")
    dp.materialized_view(name=silver)(silver_snapshot)


def register_p07(spec: TableSpec, context: RuntimeContext, source: str) -> None:
    dp = context.pipelines
    bronze = qualify_relation(context.catalog, spec.bronze.table)
    silver = qualify_relation(context.catalog, spec.silver.table)
    _register_stream_from_relation(spec, context, target=bronze, source=source)
    _register_quarantine(spec, context, bronze)
    valid_source = _register_valid_stream_view(spec, context, bronze)

    dp.create_streaming_table(silver, comment=f"Authoritative current state for {spec.dataset_id}")
    dp.create_auto_cdc_flow(
        target=silver,
        source=valid_source,
        keys=spec.identity.business_keys,
        sequence_by=_sequence_by(spec),
        except_column_list=["_ingest_run_id", "_ingest_sequence"],
        stored_as_scd_type=1,
        name=runtime_name(spec.dataset_id, "auto_cdc_current"),
    )


def register_p10(spec: TableSpec, context: RuntimeContext, source: str) -> None:
    dp = context.pipelines
    bronze = qualify_relation(context.catalog, spec.bronze.table)
    silver = qualify_relation(context.catalog, spec.silver.table)
    _register_stream_from_relation(spec, context, target=bronze, source=source)
    _register_quarantine(spec, context, bronze)
    valid_source = _register_valid_stream_view(spec, context, bronze)

    dp.create_streaming_table(silver, comment=f"SCD2 history for {spec.dataset_id}")
    dp.create_auto_cdc_flow(
        target=silver,
        source=valid_source,
        keys=spec.identity.business_keys,
        sequence_by=_sequence_by(spec),
        apply_as_deletes="_operation = 'd'",
        except_column_list=[
            "_operation",
            "_kafka_topic",
            "_kafka_partition",
            "_kafka_offset",
            "_ingest_run_id",
            "source_lsn",
            "source_event_sequence",
        ],
        stored_as_scd_type=2,
        track_history_column_list=spec.silver.tracked_columns or None,
        name=runtime_name(spec.dataset_id, "auto_cdc_scd2"),
    )


def register_p12(spec: TableSpec, context: RuntimeContext, source: str) -> None:
    dp = context.pipelines
    spark = context.spark
    bronze = qualify_relation(context.catalog, spec.bronze.table)
    silver = qualify_relation(context.catalog, spec.silver.table)
    _register_stream_from_relation(spec, context, target=bronze, source=source)
    _register_quarantine(spec, context, bronze)

    quarantine_rules = rules_for_action(spec.quality.rules, DQAction.QUARANTINE)
    valid = valid_expression(quarantine_rules)

    def canonical_events() -> Any:
        frame = spark.readStream.table(bronze)
        if valid:
            frame = frame.filter(valid)
        return (
            frame.withWatermark("event_time", "7 days")
            .dropDuplicatesWithinWatermark(["event_id"])
            .select("event_id", "order_id", "event_type", "event_time", "payload")
        )

    canonical_events.__name__ = runtime_name(spec.dataset_id, "canonical_events")
    function = decorate_expectations(dp, canonical_events, spec.quality.rules)
    dp.table(name=silver, comment=f"Canonical business events for {spec.dataset_id}")(function)


def register_p02(spec: TableSpec, context: RuntimeContext, source: str) -> None:
    dp = context.pipelines
    spark = context.spark
    bronze = qualify_relation(context.catalog, spec.bronze.table)
    silver = qualify_relation(context.catalog, spec.silver.table)
    _register_stream_from_relation(spec, context, target=bronze, source=source, quality_rules=True)

    versions = spec.capture.options.get("reference_snapshot_versions")
    if not isinstance(versions, list) or not versions or not all(isinstance(value, int) for value in versions):
        raise ValueError(f"{spec.dataset_id}: reference_snapshot_versions must be a non-empty integer list")
    ordered_versions = tuple(sorted(versions))

    def next_snapshot(latest_snapshot_version: Any) -> Any:
        candidates = [
            version
            for version in ordered_versions
            if latest_snapshot_version is None or version > int(latest_snapshot_version)
        ]
        if not candidates:
            return None
        version = candidates[0]
        frame = spark.read.table(bronze).where(f"_snapshot_id = {version}").drop("_snapshot_id")
        return frame, version

    dp.create_streaming_table(silver, comment=f"Snapshot-derived SCD2 history for {spec.dataset_id}")
    dp.create_auto_cdc_from_snapshot_flow(
        target=silver,
        source=next_snapshot,
        keys=spec.identity.business_keys,
        stored_as_scd_type=2,
        track_history_column_list=spec.silver.tracked_columns or None,
    )


BUILTIN_RUNTIME_HANDLERS: dict[str, RuntimeHandler] = {
    "P01": register_p01,
    "P02": register_p02,
    "P07": register_p07,
    "P10": register_p10,
    "P12": register_p12,
}


def implemented_builtin_patterns() -> frozenset[str]:
    return frozenset(BUILTIN_RUNTIME_HANDLERS)


def build_builtin_runtime(spec: TableSpec, context: RuntimeContext) -> None:
    try:
        handler = BUILTIN_RUNTIME_HANDLERS[spec.pattern_id]
    except KeyError as exc:
        raise NotImplementedError(
            f"built-in pattern {spec.pattern_id} is semantically registered but its Databricks runtime handler is not implemented yet"
        ) from exc
    source = _source_relation(spec, context)
    handler(spec, context, source)
