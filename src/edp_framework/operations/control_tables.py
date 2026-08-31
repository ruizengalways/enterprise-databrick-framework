from __future__ import annotations

import re
from typing import Any

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _ident(value: str) -> str:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError(f"unsafe Unity Catalog identifier: {value!r}")
    return f"`{value}`"


def control_table_ddl(catalog: str) -> list[str]:
    c = _ident(catalog)
    s = "`platform_control`"
    return [
        f"CREATE SCHEMA IF NOT EXISTS {c}.{s}",
        f"""CREATE TABLE IF NOT EXISTS {c}.{s}.`release_history` (
          release_id STRING NOT NULL,
          git_sha STRING NOT NULL,
          environment STRING NOT NULL,
          bundle_target STRING NOT NULL,
          workflow_run_id STRING,
          deployed_at TIMESTAMP NOT NULL,
          deployed_by STRING NOT NULL,
          status STRING NOT NULL,
          metadata MAP<STRING, STRING>
        ) USING DELTA""",
        f"""CREATE TABLE IF NOT EXISTS {c}.{s}.`pipeline_run` (
          run_id STRING NOT NULL,
          pipeline_id STRING NOT NULL,
          started_at TIMESTAMP NOT NULL,
          ended_at TIMESTAMP,
          status STRING NOT NULL,
          git_sha STRING,
          correlation_id STRING,
          error_class STRING,
          error_message STRING
        ) USING DELTA""",
        f"""CREATE TABLE IF NOT EXISTS {c}.{s}.`table_run` (
          run_id STRING NOT NULL,
          dataset_id STRING NOT NULL,
          source_lower_position STRING,
          source_upper_position STRING,
          source_rows BIGINT,
          bronze_rows BIGINT,
          silver_rows BIGINT,
          started_at TIMESTAMP NOT NULL,
          ended_at TIMESTAMP,
          status STRING NOT NULL,
          error_class STRING,
          error_message STRING
        ) USING DELTA""",
        f"""CREATE TABLE IF NOT EXISTS {c}.{s}.`source_state` (
          dataset_id STRING NOT NULL,
          committed_position STRING,
          position_type STRING,
          committed_at TIMESTAMP,
          run_id STRING,
          metadata MAP<STRING, STRING>
        ) USING DELTA""",
        f"""CREATE TABLE IF NOT EXISTS {c}.{s}.`reconciliation_run` (
          reconciliation_run_id STRING NOT NULL,
          dataset_id STRING NOT NULL,
          cutoff_type STRING NOT NULL,
          cutoff_value STRING NOT NULL,
          started_at TIMESTAMP NOT NULL,
          ended_at TIMESTAMP,
          status STRING NOT NULL
        ) USING DELTA""",
        f"""CREATE TABLE IF NOT EXISTS {c}.{s}.`reconciliation_result` (
          reconciliation_run_id STRING NOT NULL,
          rule_name STRING NOT NULL,
          rule_kind STRING NOT NULL,
          expected_value STRING,
          actual_value STRING,
          variance DOUBLE,
          severity STRING NOT NULL,
          passed BOOLEAN NOT NULL,
          details MAP<STRING, STRING>
        ) USING DELTA""",
        f"""CREATE TABLE IF NOT EXISTS {c}.{s}.`quality_result` (
          run_id STRING NOT NULL,
          dataset_id STRING NOT NULL,
          rule_name STRING NOT NULL,
          action STRING NOT NULL,
          evaluated_rows BIGINT,
          failed_rows BIGINT,
          passed BOOLEAN NOT NULL,
          recorded_at TIMESTAMP NOT NULL
        ) USING DELTA""",
        f"""CREATE TABLE IF NOT EXISTS {c}.{s}.`repair_request` (
          request_id STRING NOT NULL,
          dataset_id STRING NOT NULL,
          repair_type STRING NOT NULL,
          start_position STRING,
          end_position STRING,
          key_filter STRING,
          partition_filter STRING,
          requested_by STRING NOT NULL,
          requested_at TIMESTAMP NOT NULL,
          approved_by STRING,
          approved_at TIMESTAMP,
          reason STRING NOT NULL,
          status STRING NOT NULL
        ) USING DELTA""",
        f"""CREATE TABLE IF NOT EXISTS {c}.{s}.`repair_run` (
          repair_run_id STRING NOT NULL,
          request_id STRING NOT NULL,
          started_at TIMESTAMP NOT NULL,
          ended_at TIMESTAMP,
          status STRING NOT NULL,
          source_version STRING,
          target_version_before BIGINT,
          target_version_after BIGINT,
          reconciliation_run_id STRING,
          error_message STRING
        ) USING DELTA""",
        f"""CREATE TABLE IF NOT EXISTS {c}.{s}.`schema_change_event` (
          event_id STRING NOT NULL,
          dataset_id STRING NOT NULL,
          detected_at TIMESTAMP NOT NULL,
          change_type STRING NOT NULL,
          compatibility STRING NOT NULL,
          old_schema_json STRING,
          new_schema_json STRING,
          action STRING NOT NULL,
          run_id STRING
        ) USING DELTA""",
        f"""CREATE TABLE IF NOT EXISTS {c}.{s}.`incident_event` (
          incident_id STRING NOT NULL,
          dataset_id STRING,
          opened_at TIMESTAMP NOT NULL,
          closed_at TIMESTAMP,
          severity STRING NOT NULL,
          category STRING NOT NULL,
          status STRING NOT NULL,
          run_id STRING,
          repair_request_id STRING,
          summary STRING NOT NULL
        ) USING DELTA""",
    ]


def ensure_control_tables(spark: Any, catalog: str) -> None:
    for statement in control_table_ddl(catalog):
        spark.sql(statement)
