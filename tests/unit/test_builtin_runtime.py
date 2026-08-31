from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from edp_framework.metadata.loader import load_table_spec
from edp_framework.patterns.contracts import RuntimeContext
from edp_framework.patterns.registry import PatternRegistry
from edp_framework.runtime import builtin
from edp_framework.runtime.names import qualify_relation, runtime_name

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples" / "table_specs"


class FakeFrame:
    def __init__(self, relation: str) -> None:
        self.relation = relation
        self.filters: list[str] = []
        self.watermarks: list[tuple[str, str]] = []
        self.dedup_keys: list[list[str]] = []

    def filter(self, expression: str) -> FakeFrame:
        self.filters.append(expression)
        return self

    def withWatermark(self, column: str, delay: str) -> FakeFrame:  # noqa: N802
        self.watermarks.append((column, delay))
        return self

    def dropDuplicatesWithinWatermark(self, columns: list[str]) -> FakeFrame:  # noqa: N802
        self.dedup_keys.append(columns)
        return self


class FakeReader:
    def __init__(self, frames: list[FakeFrame]) -> None:
        self.frames = frames

    def table(self, relation: str) -> FakeFrame:
        frame = FakeFrame(relation)
        self.frames.append(frame)
        return frame


class FakeSpark:
    def __init__(self) -> None:
        self.frames: list[FakeFrame] = []
        self.read = FakeReader(self.frames)
        self.readStream = FakeReader(self.frames)


class FakePipelines:
    def __init__(self) -> None:
        self.tables: list[tuple[dict[str, Any], Any]] = []
        self.materialized_views: list[tuple[dict[str, Any], Any]] = []
        self.temporary_views: list[tuple[dict[str, Any], Any]] = []
        self.streaming_tables: list[tuple[tuple[Any, ...], dict[str, Any]]] = []
        self.auto_cdc: list[dict[str, Any]] = []
        self.snapshot_auto_cdc: list[dict[str, Any]] = []
        self.expectations: list[tuple[str, str, str]] = []

    def _decorator(self, bucket: list[tuple[dict[str, Any], Any]], **kwargs: Any) -> Any:
        def decorate(function: Any) -> Any:
            bucket.append((kwargs, function))
            return function

        return decorate

    def table(self, **kwargs: Any) -> Any:
        return self._decorator(self.tables, **kwargs)

    def materialized_view(self, **kwargs: Any) -> Any:
        return self._decorator(self.materialized_views, **kwargs)

    def temporary_view(self, **kwargs: Any) -> Any:
        return self._decorator(self.temporary_views, **kwargs)

    def expect(self, name: str, expression: str) -> Any:
        def decorate(function: Any) -> Any:
            self.expectations.append(("warn", name, expression))
            return function

        return decorate

    def expect_or_fail(self, name: str, expression: str) -> Any:
        def decorate(function: Any) -> Any:
            self.expectations.append(("fail", name, expression))
            return function

        return decorate

    def create_streaming_table(self, *args: Any, **kwargs: Any) -> None:
        self.streaming_tables.append((args, kwargs))

    def create_auto_cdc_flow(self, **kwargs: Any) -> None:
        self.auto_cdc.append(kwargs)

    def create_auto_cdc_from_snapshot_flow(self, **kwargs: Any) -> None:
        self.snapshot_auto_cdc.append(kwargs)


def context(*, options: dict[str, Any] | None = None) -> tuple[RuntimeContext, FakeSpark, FakePipelines]:
    spark = FakeSpark()
    dp = FakePipelines()
    runtime = RuntimeContext(
        spark=spark,
        pipelines=dp,
        environment="test",
        catalog="edp_test",
        options=options or {},
    )
    return runtime, spark, dp


def test_runtime_names_reject_unsafe_relations() -> None:
    assert qualify_relation("edp_test", "bronze.customer") == "edp_test.bronze.customer"
    assert runtime_name("crm.customer", "valid stream") == "crm_customer_valid_stream"
    with pytest.raises(ValueError, match="unsafe Unity Catalog relation"):
        qualify_relation("edp_test", "bronze.customer;drop")


def test_p01_registers_current_bronze_and_authoritative_silver() -> None:
    spec = load_table_spec(EXAMPLES / "country.yml")
    runtime, _, dp = context(options={"source_relation": "source.country_snapshot"})

    PatternRegistry(load_plugins=False).build_runtime(spec, runtime)

    names = [entry[0]["name"] for entry in dp.materialized_views]
    assert names == ["edp_test.reference_bronze.country", "edp_test.reference_silver.country"]
    assert dp.auto_cdc == []


def test_p02_uses_workload_snapshot_callback_without_fixture_versions() -> None:
    spec = load_table_spec(EXAMPLES / "customer_snapshot_scd2.yml")

    def snapshot_source(latest: Any) -> Any:
        return None

    runtime, _, dp = context(options={"snapshot_source": snapshot_source})
    PatternRegistry(load_plugins=False).build_runtime(spec, runtime)

    assert len(dp.snapshot_auto_cdc) == 1
    call = dp.snapshot_auto_cdc[0]
    assert call["source"] is snapshot_source
    assert call["keys"] == ["customer_id"]
    assert call["stored_as_scd_type"] == 2
    assert "name" not in call


def test_p02_rejects_missing_snapshot_callback() -> None:
    spec = load_table_spec(EXAMPLES / "customer_snapshot_scd2.yml")
    runtime, _, _ = context()
    with pytest.raises(ValueError, match="snapshot_source"):
        PatternRegistry(load_plugins=False).build_runtime(spec, runtime)


def test_p07_preserves_source_soft_delete_row_in_current_target() -> None:
    spec = load_table_spec(EXAMPLES / "customer_watermark_soft_delete.yml")
    runtime, _, dp = context(options={"source_relation": "source.crm_observations"})

    PatternRegistry(load_plugins=False).build_runtime(spec, runtime)

    assert len(dp.auto_cdc) == 1
    call = dp.auto_cdc[0]
    assert call["keys"] == ["customer_id"]
    assert call["sequence_by"] == "row_version"
    assert call["stored_as_scd_type"] == 1
    assert "apply_as_deletes" not in call
    assert "_ingest_run_id" in call["except_column_list"]


def test_p10_requires_provider_owned_delete_expression() -> None:
    spec = load_table_spec(EXAMPLES / "customer_debezium_scd2.yml")
    assert builtin._string_option(spec, "apply_as_deletes") == "_operation = 'd'"
    builtin.validate_builtin_runtime_contract(spec)

    payload = spec.model_dump(mode="python")
    payload["capture"]["options"].pop("apply_as_deletes")
    incomplete = type(spec).model_validate(payload)
    with pytest.raises(ValueError, match="apply_as_deletes"):
        builtin.validate_builtin_runtime_contract(incomplete)


def test_p12_registers_watermark_and_event_identity_dedup() -> None:
    spec = load_table_spec(EXAMPLES / "order_events.yml")
    runtime, spark, dp = context(options={"source_relation": "source.order_events"})

    PatternRegistry(load_plugins=False).build_runtime(spec, runtime)

    silver = next(function for kwargs, function in dp.tables if kwargs["name"] == "edp_test.commerce_silver.order_events")
    frame = silver()
    assert frame is spark.frames[-1]
    assert frame.watermarks == [("event_time", "7 days")]
    assert frame.dedup_keys == [["event_id"]]
    assert any(kwargs["name"] == "edp_test.commerce_quarantine.order_events" for kwargs, _ in dp.tables)


def test_unimplemented_builtin_runtime_fails_explicitly() -> None:
    spec = load_table_spec(EXAMPLES / "customer_watermark_soft_delete.yml")
    payload = spec.model_dump(mode="python")
    payload["pattern_id"] = "P05"
    payload["deletes"] = {"strategy": "none"}
    payload["bronze"]["contract"] = "raw_append"
    payload["silver"]["contract"] = "current"
    p05 = type(spec).model_validate(payload)
    runtime, _, _ = context(options={"source_relation": "source.any"})

    with pytest.raises(NotImplementedError, match="not implemented"):
        PatternRegistry(load_plugins=False).build_runtime(p05, runtime)
