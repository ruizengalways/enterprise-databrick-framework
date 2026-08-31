from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from edp_framework.metadata.loader import load_table_spec
from edp_framework.metadata.models import TableSpec
from edp_framework.patterns.contracts import RuntimeContext
from edp_framework.runtime import builtin

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "config" / "tables" / "reference"


def test_p07_delivery_metadata_drives_runtime_exclusions() -> None:
    spec = load_table_spec(REFERENCE / "customer_watermark_soft_delete.yml")
    assert spec.identity.delivery_identity_columns == ["_ingest_run_id", "_ingest_sequence"]


def test_p10_provider_delete_semantics_are_metadata_owned() -> None:
    spec = load_table_spec(REFERENCE / "customer_debezium_scd2.yml")
    assert builtin._string_option(spec, "apply_as_deletes") == "_operation = 'd'"
    assert builtin._string_list_option(spec, "runtime_except_columns") == [
        "_operation",
        "_kafka_topic",
        "_kafka_partition",
        "_kafka_offset",
        "_ingest_run_id",
        "source_lsn",
        "source_event_sequence",
    ]

    payload = deepcopy(spec.model_dump(mode="python"))
    payload["capture"]["options"].pop("apply_as_deletes")
    incomplete = TableSpec.model_validate(payload)
    with pytest.raises(ValueError, match="apply_as_deletes"):
        builtin.validate_builtin_runtime_contract(incomplete)


def test_p12_runtime_contract_is_metadata_validated() -> None:
    spec = load_table_spec(REFERENCE / "order_events.yml")
    assert spec.silver.effective_time_column == "event_time"
    assert spec.identity.event_identity_columns == ["event_id"]
    assert builtin._string_option(spec, "dedup_watermark") == "7 days"
    builtin.validate_builtin_runtime_contract(spec)


def test_p12_rejects_non_callable_domain_transform_before_registration() -> None:
    spec = load_table_spec(REFERENCE / "order_events.yml")
    context = RuntimeContext(
        spark=object(),
        pipelines=object(),
        environment="test",
        catalog="edp_test",
        options={"transform": "not-callable"},
    )
    with pytest.raises(TypeError, match="must be callable"):
        builtin.register_p12(spec, context, "edp_test.reference.source")
