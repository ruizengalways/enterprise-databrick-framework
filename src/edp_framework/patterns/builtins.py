from __future__ import annotations

from edp_framework.metadata.models import BronzeContract as B
from edp_framework.metadata.models import ChangeGranularity, DataSemantics, TableSpec
from edp_framework.metadata.models import SilverContract as S
from edp_framework.patterns.contracts import PatternDefinition


def _set(*items: S) -> frozenset[S]:
    return frozenset(items)


BUILTIN_PATTERNS: tuple[PatternDefinition, ...] = (
    PatternDefinition("P01", "Full Snapshot -> Current Bronze", B.CURRENT_REPLICA, _set(S.CURRENT, S.SNAPSHOT_REPLACE), "Complete source snapshot materialised as current state.", "batch/full_snapshot_current"),
    PatternDefinition("P02", "Full Snapshot -> Snapshot Bronze", B.SNAPSHOT_HISTORY, _set(S.CURRENT, S.SCD2, S.SNAPSHOT_REPLACE), "Append periodic complete snapshots with snapshot identity.", "batch/snapshot_history"),
    PatternDefinition("P03", "Watermark -> Current Bronze", B.CURRENT_REPLICA, _set(S.CURRENT, S.SCD1), "Incremental current rows merged into current Bronze.", "batch/watermark_current"),
    PatternDefinition("P04", "Watermark + Lookback -> Current Bronze", B.CURRENT_REPLICA, _set(S.CURRENT, S.SCD1), "Overlapping watermark reads with idempotent current materialisation.", "batch/watermark_lookback_current"),
    PatternDefinition("P05", "Watermark + Lookback -> Raw Append Bronze", B.RAW_APPEND, _set(S.CURRENT, S.SCD1, S.SCD2), "Preserve ingestion observations then collapse rereads downstream.", "batch/watermark_lookback_raw"),
    PatternDefinition("P06", "Watermark + Soft Delete -> Current Bronze", B.CURRENT_REPLICA, _set(S.CURRENT_SOFT_DELETE, S.SCD1), "Current incremental source with retained deletion marker.", "batch/watermark_soft_delete_current"),
    PatternDefinition("P07", "Watermark + Lookback + Soft Delete -> Raw Append Bronze", B.RAW_APPEND, _set(S.CURRENT_SOFT_DELETE, S.SCD1, S.SCD2), "Replayable observation history with source soft-delete semantics.", "batch/watermark_soft_delete_raw"),
    PatternDefinition("P08", "Net Changes -> Current Bronze", B.CURRENT_REPLICA, _set(S.CURRENT, S.SCD1), "Apply per-window net I/U/D to current replica.", "cdc/net_current"),
    PatternDefinition("P09", "Net Changes -> Append Bronze", B.EVENT_HISTORY, _set(S.CURRENT, S.SCD2), "Preserve net-window change observations.", "cdc/net_append"),
    PatternDefinition("P10", "Full Changes -> Event Bronze", B.EVENT_HISTORY, _set(S.CURRENT, S.SCD1, S.SCD2, S.CANONICAL_EVENTS), "Preserve captured CDC events; sequence and deduplicate by event identity.", "cdc/full_event"),
    PatternDefinition("P11", "Full Changes -> Current Bronze", B.CURRENT_REPLICA, _set(S.CURRENT, S.SCD1), "Intentionally collapse full CDC history to latest state.", "cdc/full_current_lossy"),
    PatternDefinition("P12", "Business Events -> Event Bronze", B.EVENT_HISTORY, _set(S.CANONICAL_EVENTS, S.CURRENT), "Preserve domain events and derive projections where required.", "streaming/domain_events"),
    PatternDefinition("P13", "Snapshot Diff -> Current", B.CURRENT_REPLICA, _set(S.CURRENT, S.SCD1), "Derive I/U/D by comparing complete snapshots, then materialise current state.", "snapshot_diff/current"),
    PatternDefinition("P14", "Snapshot Diff -> Append Changes", B.EVENT_HISTORY, _set(S.CURRENT, S.SCD2), "Persist derived snapshot-interval changes.", "snapshot_diff/append"),
)


EXPECTED_SEMANTICS: dict[str, DataSemantics] = {
    **{f"P{i:02d}": DataSemantics.CURRENT_STATE for i in range(1, 8)},
    **{f"P{i:02d}": DataSemantics.CHANGE_FEED for i in range(8, 12)},
    "P12": DataSemantics.BUSINESS_EVENTS,
    "P13": DataSemantics.DERIVED_CHANGES,
    "P14": DataSemantics.DERIVED_CHANGES,
}

EXPECTED_CHANGE_GRANULARITY: dict[str, ChangeGranularity] = {
    "P08": ChangeGranularity.NET,
    "P09": ChangeGranularity.NET,
    "P10": ChangeGranularity.FULL,
    "P11": ChangeGranularity.FULL,
}


def validate_builtin_pattern(spec: TableSpec, definition: PatternDefinition) -> None:
    expected_semantics = EXPECTED_SEMANTICS[definition.id]
    if spec.semantics is not expected_semantics:
        raise ValueError(
            f"{spec.dataset_id}: {definition.id} requires semantics {expected_semantics.value}, "
            f"got {spec.semantics.value}"
        )

    expected_granularity = EXPECTED_CHANGE_GRANULARITY.get(definition.id)
    if expected_granularity is not None and spec.capture.change_granularity is not expected_granularity:
        raise ValueError(
            f"{spec.dataset_id}: {definition.id} requires {expected_granularity.value}, "
            f"got {spec.capture.change_granularity.value}"
        )

    if spec.bronze.contract is not definition.bronze_contract:
        raise ValueError(
            f"{spec.dataset_id}: {definition.id} requires Bronze {definition.bronze_contract.value}, "
            f"got {spec.bronze.contract.value}"
        )
    if spec.silver.contract not in definition.supported_silver_contracts:
        allowed = ", ".join(sorted(x.value for x in definition.supported_silver_contracts))
        raise ValueError(
            f"{spec.dataset_id}: {definition.id} does not support Silver {spec.silver.contract.value}; "
            f"allowed: {allowed}"
        )
