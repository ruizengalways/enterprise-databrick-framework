from __future__ import annotations

from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class DataSemantics(str, Enum):
    CURRENT_STATE = "current_state"
    CHANGE_FEED = "change_feed"
    BUSINESS_EVENTS = "business_events"
    DERIVED_CHANGES = "derived_changes"


class CaptureMechanism(str, Enum):
    FULL_SNAPSHOT = "full_snapshot"
    WATERMARK = "watermark"
    NATIVE_CDC = "native_cdc"
    DEBEZIUM = "debezium"
    DELTA_CDF = "delta_cdf"
    KAFKA = "kafka"
    API = "api"
    FILE = "file"
    LAKEFLOW_CONNECT = "lakeflow_connect"
    SNAPSHOT_DIFF = "snapshot_diff"
    CUSTOM_PACKAGE = "custom_package"


class ChangeGranularity(str, Enum):
    NONE = "none"
    NET = "net_changes"
    FULL = "full_changes"


class ExecutionMode(str, Enum):
    TRIGGERED = "triggered"
    CONTINUOUS = "continuous"


class BronzeContract(str, Enum):
    CURRENT_REPLICA = "current_replica"
    RAW_APPEND = "raw_append"
    SNAPSHOT_HISTORY = "snapshot_history"
    EVENT_HISTORY = "event_history"


class SilverContract(str, Enum):
    CURRENT = "current"
    CURRENT_SOFT_DELETE = "current_soft_delete"
    SCD1 = "scd1"
    SCD2 = "scd2"
    CANONICAL_EVENTS = "canonical_events"
    SNAPSHOT_REPLACE = "snapshot_replace"
    CUSTOM = "custom"


class CursorType(str, Enum):
    TIMESTAMP = "timestamp"
    ROWVERSION = "rowversion"
    LSN = "lsn"
    SCN = "scn"
    KAFKA_OFFSET = "kafka_offset"
    DELTA_VERSION = "delta_version"
    API_CURSOR = "api_cursor"
    SNAPSHOT_ID = "snapshot_id"
    FILE_POSITION = "file_position"
    CUSTOM = "custom"


class DeleteStrategy(str, Enum):
    NONE = "none"
    SOURCE_SOFT_DELETE = "source_soft_delete"
    CDC_DELETE = "cdc_delete"
    SNAPSHOT_ABSENCE = "snapshot_absence"
    PERIODIC_RECONCILIATION = "periodic_reconciliation"
    CUSTOM = "custom"


class DQAction(str, Enum):
    WARN = "warn"
    QUARANTINE = "quarantine"
    FAIL = "fail"


class RecoveryMode(str, Enum):
    REPLAY_BRONZE = "replay_bronze"
    REPLAY_SOURCE = "replay_source"
    SNAPSHOT_RELOAD = "snapshot_reload"
    FULL_REBUILD = "full_rebuild"
    DELTA_RESTORE = "delta_restore"
    CUSTOM = "custom"


class BootstrapMode(str, Enum):
    SNAPSHOT_ONLY = "snapshot_only"
    FULL_THEN_INCREMENTAL = "full_then_incremental"
    SNAPSHOT_AT_SOURCE_POSITION = "snapshot_at_source_position"
    EVENT_STREAM_FROM_POSITION = "event_stream_from_position"
    PROVIDER_MANAGED = "provider_managed"
    CUSTOM = "custom"


class DeliveryGuarantee(str, Enum):
    AT_LEAST_ONCE = "at_least_once"
    EFFECTIVELY_ONCE = "effectively_once"
    PROVIDER_DEFINED = "provider_defined"


class FidelityLevel(str, Enum):
    CURRENT_ONLY = "current_only"
    SNAPSHOT_INTERVAL = "snapshot_interval"
    INGESTION_OBSERVATION = "ingestion_observation"
    NET_CHANGE_WINDOW = "net_change_window"
    FULL_CAPTURED_CHANGE = "full_captured_change"
    DOMAIN_EVENT = "domain_event"


class SourceRef(StrictModel):
    system: str
    object: str
    owner: str | None = None
    connection_ref: str | None = None


class BootstrapSpec(StrictModel):
    mode: BootstrapMode
    handoff_position: str | None = None
    overlap_idempotent: bool = False
    notes: str | None = None

    @model_validator(mode="after")
    def validate_handoff(self) -> "BootstrapSpec":
        explicit_handoff = {
            BootstrapMode.FULL_THEN_INCREMENTAL,
            BootstrapMode.SNAPSHOT_AT_SOURCE_POSITION,
            BootstrapMode.EVENT_STREAM_FROM_POSITION,
        }
        if self.mode in explicit_handoff and not self.handoff_position:
            raise ValueError(f"{self.mode.value} requires handoff_position")
        return self


class DeliverySpec(StrictModel):
    guarantee: DeliveryGuarantee
    idempotency_key_columns: list[str] = Field(default_factory=list)
    retry_safe: bool = True

    @model_validator(mode="after")
    def validate_at_least_once(self) -> "DeliverySpec":
        if self.guarantee is DeliveryGuarantee.AT_LEAST_ONCE and not self.idempotency_key_columns:
            raise ValueError("at_least_once delivery requires idempotency_key_columns")
        return self


class FidelitySpec(StrictModel):
    level: FidelityLevel
    caveat: str


class RetentionSpec(StrictModel):
    source_replay_window_hours: int | None = Field(default=None, ge=1)
    required_recovery_window_hours: int = Field(ge=1)
    alert_before_expiry_hours: int = Field(default=24, ge=1)

    @model_validator(mode="after")
    def validate_source_window(self) -> "RetentionSpec":
        if (
            self.source_replay_window_hours is not None
            and self.source_replay_window_hours < self.required_recovery_window_hours
        ):
            raise ValueError(
                "source_replay_window_hours must cover required_recovery_window_hours "
                "or source replay cannot be claimed as a recovery guarantee"
            )
        return self


class CaptureSpec(StrictModel):
    mechanism: CaptureMechanism
    change_granularity: ChangeGranularity = ChangeGranularity.NONE
    execution: ExecutionMode = ExecutionMode.TRIGGERED
    provider_package: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_custom_provider(self) -> "CaptureSpec":
        if self.mechanism is CaptureMechanism.CUSTOM_PACKAGE and not self.provider_package:
            raise ValueError("custom_package capture requires provider_package")
        return self


class CursorSpec(StrictModel):
    type: CursorType
    columns: list[str] = Field(min_length=1)
    lookback: str | None = None
    boundary: Literal["lower_exclusive_upper_inclusive", "provider_defined"] = (
        "lower_exclusive_upper_inclusive"
    )


class OrderingSpec(StrictModel):
    columns: list[str] = Field(min_length=1)
    authoritative: bool = True


class IdentitySpec(StrictModel):
    business_keys: list[str] = Field(default_factory=list)
    source_version_columns: list[str] = Field(default_factory=list)
    event_identity_columns: list[str] = Field(default_factory=list)
    delivery_identity_columns: list[str] = Field(default_factory=list)


class BronzeSpec(StrictModel):
    contract: BronzeContract
    table: str
    preserve_raw_payload: bool = True
    retention_days: int = Field(default=180, ge=1)
    append_delivery_attempts: bool = True


class SilverSpec(StrictModel):
    contract: SilverContract
    table: str
    tracked_columns: list[str] = Field(default_factory=list)
    ignored_history_columns: list[str] = Field(default_factory=list)
    effective_time_column: str | None = None


class DeleteSpec(StrictModel):
    strategy: DeleteStrategy = DeleteStrategy.NONE
    indicator_column: str | None = None
    deleted_values: list[Any] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_soft_delete(self) -> "DeleteSpec":
        if self.strategy is DeleteStrategy.SOURCE_SOFT_DELETE and not self.indicator_column:
            raise ValueError("source_soft_delete requires indicator_column")
        return self


class QualityRule(StrictModel):
    name: str
    expression: str
    action: DQAction
    threshold: float = Field(default=1.0, ge=0.0, le=1.0)
    owner: str | None = None


class QualitySpec(StrictModel):
    rules: list[QualityRule] = Field(default_factory=list)
    quarantine_table: str | None = None

    @model_validator(mode="after")
    def validate_quarantine(self) -> "QualitySpec":
        if any(r.action is DQAction.QUARANTINE for r in self.rules) and not self.quarantine_table:
            raise ValueError("quarantine rules require quarantine_table")
        return self


class ReconciliationRule(StrictModel):
    name: str
    kind: Literal[
        "row_count",
        "key_count",
        "pk_presence",
        "aggregate",
        "hash",
        "source_position",
        "operation_count",
        "scd2_current_uniqueness",
        "scd2_no_overlap",
        "custom",
    ]
    severity: Literal["warn", "fail"] = "fail"
    tolerance: float = Field(default=0.0, ge=0.0)
    options: dict[str, Any] = Field(default_factory=dict)


class ReconciliationSpec(StrictModel):
    enabled: bool = True
    cutoff_strategy: Literal[
        "captured_upper_bound",
        "source_position",
        "snapshot_id",
        "provider_defined",
    ] = "captured_upper_bound"
    rules: list[ReconciliationRule] = Field(default_factory=list)


class SchemaEvolutionSpec(StrictModel):
    add_nullable: Literal["allow", "review", "fail"] = "allow"
    add_required: Literal["review", "fail"] = "fail"
    drop: Literal["review", "fail"] = "fail"
    rename: Literal["review", "fail"] = "fail"
    widen_type: Literal["allow", "review", "fail"] = "review"
    incompatible_type: Literal["review", "fail", "quarantine"] = "fail"
    rescued_data: bool = True


class RecoverySpec(StrictModel):
    primary: RecoveryMode
    allowed: list[RecoveryMode] = Field(default_factory=list)
    key_replay: bool = False
    time_window_replay: bool = False
    partition_replay: bool = False
    requires_approval: bool = True


class SlaSpec(StrictModel):
    freshness_minutes: int | None = Field(default=None, ge=1)
    max_recovery_minutes: int | None = Field(default=None, ge=1)


class TableSpec(StrictModel):
    version: Annotated[int, Field(ge=1)] = 1
    dataset_id: str
    pattern_id: str
    enabled: bool = True
    source: SourceRef
    semantics: DataSemantics
    capture: CaptureSpec
    bootstrap: BootstrapSpec
    delivery: DeliverySpec
    fidelity: FidelitySpec
    retention: RetentionSpec
    cursor: CursorSpec | None = None
    ordering: OrderingSpec | None = None
    identity: IdentitySpec
    bronze: BronzeSpec
    silver: SilverSpec
    deletes: DeleteSpec = Field(default_factory=DeleteSpec)
    quality: QualitySpec = Field(default_factory=QualitySpec)
    reconciliation: ReconciliationSpec = Field(default_factory=ReconciliationSpec)
    schema_evolution: SchemaEvolutionSpec = Field(default_factory=SchemaEvolutionSpec)
    recovery: RecoverySpec
    sla: SlaSpec = Field(default_factory=SlaSpec)
    tags: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_semantics(self) -> "TableSpec":
        keys = self.identity.business_keys
        merge_like = {
            SilverContract.CURRENT,
            SilverContract.CURRENT_SOFT_DELETE,
            SilverContract.SCD1,
            SilverContract.SCD2,
        }
        if self.silver.contract in merge_like and not keys:
            raise ValueError(f"{self.silver.contract.value} requires stable business_keys")

        if self.silver.contract is SilverContract.SCD2 and not self.ordering:
            raise ValueError("scd2 requires authoritative source ordering")

        if self.capture.mechanism is CaptureMechanism.WATERMARK and self.cursor is None:
            raise ValueError("watermark capture requires cursor")

        incremental_or_change = (
            self.capture.mechanism is CaptureMechanism.WATERMARK
            or self.capture.change_granularity is not ChangeGranularity.NONE
        )
        if incremental_or_change and self.bootstrap.mode is BootstrapMode.SNAPSHOT_ONLY:
            raise ValueError("incremental/change processing requires an explicit baseline-to-change handoff")

        if self.capture.change_granularity is not ChangeGranularity.NONE and self.ordering is None:
            raise ValueError("change feeds require source ordering")

        if self.bronze.contract is BronzeContract.EVENT_HISTORY:
            has_event_identity = bool(self.identity.event_identity_columns)
            has_ordering_identity = self.ordering is not None and bool(self.ordering.columns)
            if not (has_event_identity or has_ordering_identity):
                raise ValueError("event_history requires event identity or source ordering")

        if (
            self.deletes.strategy is DeleteStrategy.NONE
            and self.silver.contract is SilverContract.CURRENT_SOFT_DELETE
        ):
            raise ValueError("current_soft_delete requires explicit delete strategy")

        if self.reconciliation.enabled and not self.reconciliation.rules:
            raise ValueError("enabled reconciliation requires at least one rule")

        if self.recovery.primary not in self.recovery.allowed:
            raise ValueError("recovery.primary must also appear in recovery.allowed")

        if (
            self.recovery.primary is RecoveryMode.REPLAY_BRONZE
            and self.bronze.retention_days * 24 < self.retention.required_recovery_window_hours
        ):
            raise ValueError("Bronze retention does not cover the required recovery window")

        if (
            RecoveryMode.REPLAY_SOURCE in self.recovery.allowed
            and self.retention.source_replay_window_hours is None
        ):
            raise ValueError("replay_source requires an explicit source_replay_window_hours contract")

        if (
            self.deletes.strategy is DeleteStrategy.SNAPSHOT_ABSENCE
            and self.capture.mechanism
            not in {CaptureMechanism.FULL_SNAPSHOT, CaptureMechanism.SNAPSHOT_DIFF}
        ):
            raise ValueError("snapshot_absence delete detection requires complete comparable snapshots")

        if (
            self.deletes.strategy is DeleteStrategy.CDC_DELETE
            and self.capture.change_granularity is ChangeGranularity.NONE
        ):
            raise ValueError("cdc_delete requires a change feed contract")

        return self
