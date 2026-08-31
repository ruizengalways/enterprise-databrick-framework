import pytest
from pydantic import ValidationError

from edp_framework.metadata.models import TableSpec


def _base() -> dict:
    return {
        "dataset_id": "x.customer",
        "pattern_id": "P10",
        "source": {"system": "x", "object": "customer"},
        "semantics": "change_feed",
        "capture": {
            "mechanism": "debezium",
            "change_granularity": "full_changes",
            "execution": "continuous",
        },
        "bootstrap": {
            "mode": "snapshot_at_source_position",
            "handoff_position": "LSN P",
            "overlap_idempotent": True,
        },
        "delivery": {
            "guarantee": "at_least_once",
            "idempotency_key_columns": ["partition", "offset"],
        },
        "fidelity": {
            "level": "full_captured_change",
            "caveat": "bounded by retained CDC history",
        },
        "retention": {
            "source_replay_window_hours": 168,
            "required_recovery_window_hours": 72,
        },
        "cursor": {"type": "kafka_offset", "columns": ["partition", "offset"]},
        "ordering": {"columns": ["lsn", "seq"]},
        "identity": {
            "business_keys": ["customer_id"],
            "event_identity_columns": ["partition", "offset"],
        },
        "bronze": {"contract": "event_history", "table": "x_bronze.customer"},
        "silver": {"contract": "scd2", "table": "x_silver.customer"},
        "deletes": {"strategy": "cdc_delete"},
        "reconciliation": {
            "enabled": True,
            "cutoff_strategy": "source_position",
            "rules": [{"name": "position", "kind": "source_position"}],
        },
        "recovery": {"primary": "replay_bronze", "allowed": ["replay_bronze"]},
    }


def test_scd2_requires_business_key() -> None:
    payload = _base()
    payload["identity"]["business_keys"] = []
    with pytest.raises(ValidationError, match="stable business_keys"):
        TableSpec.model_validate(payload)


def test_scd2_requires_source_ordering() -> None:
    payload = _base()
    payload.pop("ordering")
    with pytest.raises(ValidationError, match="scd2 requires authoritative source ordering"):
        TableSpec.model_validate(payload)


def test_watermark_requires_cursor() -> None:
    payload = _base()
    payload["pattern_id"] = "P05"
    payload["semantics"] = "current_state"
    payload["capture"] = {"mechanism": "watermark", "execution": "triggered"}
    payload["bronze"]["contract"] = "raw_append"
    payload["silver"]["contract"] = "current"
    payload.pop("cursor")
    with pytest.raises(ValidationError, match="watermark capture requires cursor"):
        TableSpec.model_validate(payload)


def test_at_least_once_requires_idempotency_key() -> None:
    payload = _base()
    payload["delivery"]["idempotency_key_columns"] = []
    with pytest.raises(ValidationError, match="idempotency_key_columns"):
        TableSpec.model_validate(payload)


def test_incremental_requires_explicit_bootstrap_handoff() -> None:
    payload = _base()
    payload["bootstrap"] = {"mode": "snapshot_only"}
    with pytest.raises(ValidationError, match="baseline-to-change handoff"):
        TableSpec.model_validate(payload)


def test_source_replay_claim_requires_retention_contract() -> None:
    payload = _base()
    payload["recovery"]["allowed"].append("replay_source")
    payload["retention"].pop("source_replay_window_hours")
    with pytest.raises(ValidationError, match="replay_source requires"):
        TableSpec.model_validate(payload)
