from __future__ import annotations

from collections.abc import Callable
from typing import Any

from edp_framework.metadata.models import (
    BronzeContract,
    DQAction,
    DeleteStrategy,
    SilverContract,
    TableSpec,
)
from edp_framework.patterns.contracts import RuntimeContext
from edp_framework.runtime.names import qualify_relation, runtime_name
from edp_framework.runtime.quality import (
    decorate_expectations,
    invalid_expression,
    rules_for_action,
    valid_expression,
)

RuntimeHandler = Callable[[TableSpec, RuntimeContext], None]
SnapshotSource = Callable[[Any], Any]


def _string_option(spec: TableSpec, name: str) -> str | None:
    value = spec.capture.options.get(name)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{spec.dataset_id}: capture.options.{name} must be a non-empty string")
    return value


def _string_list_option(spec: TableSpec, name: str) -> list[str]:
    value = spec.capture.options.get(name)
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{spec.dataset_id}: capture.options.{name} must be a list of strings")
    return value


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def _source_relation(spec: TableSpec, context: RuntimeContext) -> str:
    """Resolve the normalized capture-adapter output consumed by the framework.

    The framework intentionally does not embed JDBC/Kafka/API/file connector code in the
    semantic runtime. A workload or extension adapter supplies a normalized relation and
    the framework materializes the declared Bronze/Silver semantics from that boundary.
    """

    configured = context.options.get("source_relation") or spec.capture.options.get(
        "reference_source_relation"
    )
    if not isinstance(configured, str) or not configured.strip():
        raise ValueError(
            f"{spec.dataset_id}: runtime source_relation is required; "
            "the consuming capture adapter must supply a normalized schema.table relation"
        )
    return qualify_relation(context.catalog, configured)


def _snapshot_source(spec: TableSpec, context: RuntimeContext) -> SnapshotSource:
    """Return the workload-supplied historical snapshot iterator for P02.

    `AUTO CDC FROM SNAPSHOT` supports a callback that receives the last processed version
    and returns `(DataFrame, version)` or `None`. The callback belongs to the consuming
    workload because snapshot discovery can mean files, API versions, database exports,
    or another retained Bronze implementation. Core must not hard-code fixture versions.
    """

    value = context.options.get("snapshot_source")
    if not callable(value):
        raise ValueError(
            f"{spec.dataset_id}: P02 requires RuntimeContext.options['snapshot_source'] "
            "as a callable returning (DataFrame, snapshot_version) or None"
        )
    return value


def _sequence_by(spec: TableSpec) -> Any:
    if spec.ordering is None or not spec.ordering.authoritative:
        raise ValueError(f"{spec.dataset_id}: authoritative source ordering is required")
    columns = spec.ordering.columns
    if len(columns) == 1:
        # AUTO CDC accepts a column name directly. Returning a string keeps package tests
        # importable outside a Databricks/PySpark runtime.
        return columns[0]

    from pyspark.sql.functions import col, struct

    return struct(*[col(column) for column in columns])


def _runtime_except_columns(spec: TableSpec) -> list[str] | None:
    configured = _string_list_option(spec, "runtime_except_columns")
    combined = _unique([*configured, *spec.identity.delivery_identity_columns])
    return combined or None


def validate_builtin_runtime_contract(spec: TableSpec) -> None:
    """Validate extra runtime requirements for the built-in handlers released in v1."""

    if spec.pattern_id not in BUILTIN_RUNTIME_HANDLERS:
        return

    if spec.pattern_id == "P01":
        if spec.bronze.contract is not BronzeContract.CURRENT_REPLICA:
            raise ValueError(f"{spec.dataset_id}: P01 runtime requires current-replica Bronze")
        if spec.silver.contract not in {SilverContract.CURRENT, SilverContract.SNAPSHOT_REPLACE}:
            raise ValueError(f"{spec.dataset_id}: P01 runtime supports current/snapshot_replace Silver")

    if spec.pattern_id == "P02":
        if spec.bronze.contract is not BronzeContract.SNAPSHOT_HISTORY:
            raise ValueError(f"{spec.dataset_id}: P02 runtime requires snapshot-history Bronze")
        if spec.silver.contract is not SilverContract.SCD2:
            raise ValueError(f"{spec.dataset_id}: P02 v1 runtime currently supports SCD2 Silver")
        if spec.cursor is None or len(spec.cursor.columns) != 1:
            raise ValueError(f"{spec.dataset_id}: P02 requires exactly one snapshot-version cursor column")

    if spec.pattern_id == "P07":
        if spec.bronze.contract is not BronzeContract.RAW_APPEND:
            raise ValueError(f"{spec.dataset_id}: P07 runtime requires raw-append Bronze")
        if spec.deletes.strategy is not DeleteStrategy.SOURCE_SOFT_DELETE:
            raise ValueError(f"{spec.dataset_id}: P07 runtime requires source_soft_delete semantics")
        if spec.silver.contract not in {
            SilverContract.CURRENT_SOFT_DELETE,
            SilverContract.SCD1,
            SilverContract.SCD2,
        }:
            raise ValueError(f"{spec.dataset_id}: unsupported P07 Silver runtime contract")

    if spec.pattern_id == "P10":
        if spec.bronze.contract is not BronzeContract.EVENT_HISTORY:
            raise ValueError(f"{spec.dataset_id}: P10 runtime requires event-history Bronze")
        if spec.silver.contract not in {
            SilverContract.CURRENT,
            SilverContract.SCD1,
            SilverContract.SCD2,
        }:
            raise ValueError(f"{spec.dataset_id}: P10 v1 AUTO CDC runtime supports current/SCD1/SCD2")
        if spec.deletes.strategy is DeleteStrategy.CDC_DELETE and _string_option(
            spec, "apply_as_deletes"
        ) is None:
            raise ValueError(
                f"{spec.dataset_id}: CDC delete semantics require explicit "
                "capture.options.apply_as_deletes; core will not infer provider operation codes"
            )
        _string_list_option(spec, "runtime_except_columns")

    if spec.pattern_id == "P12":
        if spec.bronze.contract is not BronzeContract.EVENT_HISTORY:
            raise ValueError(f"{spec.dataset_id}: P12 runtime requires event-history Bronze")
        if spec.silver.contract is not SilverContract.CANONICAL_EVENTS:
            raise ValueError(f"{spec.dataset_id}: P12 v1 runtime supports canonical_events Silver")
        if not spec.silver.effective_time_column:
            raise ValueError(f"{spec.dataset_id}: P12 requires silver.effective_time_column")
        if not spec.identity.event_identity_columns:
            raise ValueError(f"{spec.dataset_id}: P12 requires event_identity_columns")
        if _string_option(spec, "dedup_watermark") is None:
            raise ValueError(
                f"{spec.dataset_id}: P12 requires capture.options.dedup_watermark; "
                "watermark/lateness policy must be an explicit workload contract"
            )


def _register_stream_bronze(
    spec: TableSpec,
    context: RuntimeContext,
    *,
    source: str,
    target: str,
) -> None:
    dp = context.pipelines
    spark = context.spark

    def bronze_stream() -> Any:
        return spark.readStream.table(source)

    bronze_stream.__name__ = runtime_name(spec.dataset_id, "bronze_stream")
    function = decorate_expectations(dp, bronze_stream, spec.quality.rules)
    dp.table(name=target, comment=f"Bronze {spec.bronze.contract.value} for {spec.dataset_id}")(
        function
    )


def _register_batch_bronze(
    spec: TableSpec,
    context: RuntimeContext,
    *,
    source: str,
    target: str,
) -> None:
    dp = context.pipelines
    spark = context.spark

    def bronze_snapshot() -> Any:
        return spark.read.table(source)

    bronze_snapshot.__name__ = runtime_name(spec.dataset_id, "bronze_snapshot")
    function = decorate_expectations(dp, bronze_snapshot, spec.quality.rules)
    dp.materialized_view(
        name=target,
        comment=f"Bronze {spec.bronze.contract.value} for {spec.dataset_id}",
    )(function)


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
    dp.temporary_view(name=name, comment=f"Valid records for {spec.dataset_id}")(valid_stream)
    return name


def register_p01(spec: TableSpec, context: RuntimeContext) -> None:
    validate_builtin_runtime_contract(spec)
    source = _source_relation(spec, context)
    bronze = qualify_relation(context.catalog, spec.bronze.table)
    silver = qualify_relation(context.catalog, spec.silver.table)
    _register_batch_bronze(spec, context, source=source, target=bronze)

    dp = context.pipelines
    spark = context.spark

    def silver_snapshot() -> Any:
        return spark.read.table(bronze)

    silver_snapshot.__name__ = runtime_name(spec.dataset_id, "silver_snapshot")
    dp.materialized_view(name=silver, comment=f"Authoritative snapshot for {spec.dataset_id}")(
        silver_snapshot
    )


def register_p02(spec: TableSpec, context: RuntimeContext) -> None:
    """Register snapshot-derived SCD2 from a workload-owned Bronze snapshot iterator.

    The workload/capture adapter owns discovery and retention of complete snapshots in the
    declared Bronze contract. It passes a callback through RuntimeContext that returns the
    next complete snapshot and version. This keeps file/API/database version discovery out
    of reusable semantic core and avoids forbidden actions such as collect() in dataset definitions.
    """

    validate_builtin_runtime_contract(spec)
    snapshot_source = _snapshot_source(spec, context)
    silver = qualify_relation(context.catalog, spec.silver.table)
    dp = context.pipelines

    dp.create_streaming_table(silver, comment=f"Snapshot-derived SCD2 for {spec.dataset_id}")
    # Current Lakeflow API does not expose a `name` argument for snapshot AUTO CDC.
    dp.create_auto_cdc_from_snapshot_flow(
        target=silver,
        source=snapshot_source,
        keys=spec.identity.business_keys,
        stored_as_scd_type=2,
        track_history_column_list=spec.silver.tracked_columns or None,
    )


def register_p07(spec: TableSpec, context: RuntimeContext) -> None:
    validate_builtin_runtime_contract(spec)
    source = _source_relation(spec, context)
    bronze = qualify_relation(context.catalog, spec.bronze.table)
    silver = qualify_relation(context.catalog, spec.silver.table)

    _register_stream_bronze(spec, context, source=source, target=bronze)
    _register_quarantine(spec, context, bronze)
    valid_source = _register_valid_stream_view(spec, context, bronze)

    stored_type = 2 if spec.silver.contract is SilverContract.SCD2 else 1
    dp = context.pipelines
    dp.create_streaming_table(
        silver,
        comment=f"Current state derived from raw observations for {spec.dataset_id}",
    )
    dp.create_auto_cdc_flow(
        target=silver,
        source=valid_source,
        keys=spec.identity.business_keys,
        sequence_by=_sequence_by(spec),
        except_column_list=_runtime_except_columns(spec),
        stored_as_scd_type=stored_type,
        track_history_column_list=(spec.silver.tracked_columns or None) if stored_type == 2 else None,
        name=runtime_name(spec.dataset_id, "observation_auto_cdc"),
    )


def register_p10(spec: TableSpec, context: RuntimeContext) -> None:
    validate_builtin_runtime_contract(spec)
    source = _source_relation(spec, context)
    bronze = qualify_relation(context.catalog, spec.bronze.table)
    silver = qualify_relation(context.catalog, spec.silver.table)

    _register_stream_bronze(spec, context, source=source, target=bronze)
    _register_quarantine(spec, context, bronze)
    valid_source = _register_valid_stream_view(spec, context, bronze)

    stored_type = 2 if spec.silver.contract is SilverContract.SCD2 else 1
    dp = context.pipelines
    dp.create_streaming_table(silver, comment=f"CDC-derived state/history for {spec.dataset_id}")
    dp.create_auto_cdc_flow(
        target=silver,
        source=valid_source,
        keys=spec.identity.business_keys,
        sequence_by=_sequence_by(spec),
        apply_as_deletes=_string_option(spec, "apply_as_deletes"),
        except_column_list=_runtime_except_columns(spec),
        stored_as_scd_type=stored_type,
        track_history_column_list=(spec.silver.tracked_columns or None) if stored_type == 2 else None,
        name=runtime_name(spec.dataset_id, "full_cdc_auto_cdc"),
    )


def register_p12(spec: TableSpec, context: RuntimeContext) -> None:
    validate_builtin_runtime_contract(spec)
    source = _source_relation(spec, context)
    bronze = qualify_relation(context.catalog, spec.bronze.table)
    silver = qualify_relation(context.catalog, spec.silver.table)
    event_time = spec.silver.effective_time_column
    assert event_time is not None
    watermark = _string_option(spec, "dedup_watermark")
    assert watermark is not None

    transform = context.options.get("transform")
    if transform is not None and not callable(transform):
        raise TypeError(f"{spec.dataset_id}: RuntimeContext.options['transform'] must be callable")

    _register_stream_bronze(spec, context, source=source, target=bronze)
    _register_quarantine(spec, context, bronze)

    quarantine_rules = rules_for_action(spec.quality.rules, DQAction.QUARANTINE)
    valid = valid_expression(quarantine_rules)
    spark = context.spark
    dp = context.pipelines

    def canonical_events() -> Any:
        frame = spark.readStream.table(bronze)
        if valid:
            frame = frame.filter(valid)
        frame = frame.withWatermark(event_time, watermark).dropDuplicatesWithinWatermark(
            spec.identity.event_identity_columns
        )
        return transform(frame) if transform is not None else frame

    canonical_events.__name__ = runtime_name(spec.dataset_id, "canonical_events")
    dp.table(name=silver, comment=f"Canonical business events for {spec.dataset_id}")(
        canonical_events
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
            f"built-in pattern {spec.pattern_id} is semantically registered but its "
            "Databricks runtime handler is not implemented in this framework release"
        ) from exc
    handler(spec, context)
