from __future__ import annotations

import argparse
import re
from typing import Any

from pyspark.sql import SparkSession

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_FIXTURES: dict[str, tuple[str, str]] = {
    "fixture_country_snapshot": (
        "country_code STRING, country_name STRING",
        """('AU','Australia'),('NZ','New Zealand'),('US','United States')""",
    ),
    "fixture_crm_customer_observations": (
        "customer_id BIGINT, name STRING, email STRING, row_version BIGINT, is_deleted BOOLEAN, _ingest_run_id STRING, _ingest_sequence BIGINT",
        """(100,'Alice','alice@example.com',501,false,'batch_001',1),
        (200,'Bob','bob@example.com',601,false,'batch_001',2),
        (100,'Alice','alice@example.com',501,false,'batch_002',3),
        (100,'Alice Smith','alice.smith@example.com',502,false,'batch_002',4),
        (200,'Bob','bob@example.com',602,true,'batch_002',5),
        (300,'Invalid Email','not-an-email',701,false,'batch_002',6)""",
    ),
    "fixture_sales_customer_cdc": (
        "customer_id BIGINT, name STRING, status STRING, address STRING, updated_at TIMESTAMP, _operation STRING, source_lsn BIGINT, source_event_sequence BIGINT, _kafka_topic STRING, _kafka_partition INT, _kafka_offset BIGINT, _ingest_run_id STRING",
        """(100,'Alice','BRONZE','Sydney',TIMESTAMP'2026-08-01 09:00:00','c',1001,1,'sales.public.customer',0,1,'cdc_001'),
        (200,'Bob','ACTIVE','Melbourne',TIMESTAMP'2026-08-01 09:01:00','c',1001,2,'sales.public.customer',0,2,'cdc_001'),
        (100,'Alice','GOLD','Sydney',TIMESTAMP'2026-08-01 09:20:00','u',1003,1,'sales.public.customer',0,3,'cdc_001'),
        (100,'Alice','SILVER','Sydney',TIMESTAMP'2026-08-01 09:10:00','u',1002,1,'sales.public.customer',0,4,'cdc_001'),
        (200,'Bob','ACTIVE','Melbourne',TIMESTAMP'2026-08-01 09:30:00','d',1004,1,'sales.public.customer',0,5,'cdc_001'),
        (999,'Unknown','UNKNOWN','Nowhere',TIMESTAMP'2026-08-01 09:40:00','x',1005,1,'sales.public.customer',0,6,'cdc_001')""",
    ),
    "fixture_commerce_order_events": (
        "event_id STRING, order_id BIGINT, event_type STRING, event_time TIMESTAMP, payload STRING, _kafka_topic STRING, _kafka_partition INT, _kafka_offset BIGINT",
        """('evt-1',1000,'ORDER_CREATED',TIMESTAMP'2026-08-01 10:00:00','{\"amount\":100}','order-events',0,1),
        ('evt-2',1000,'ORDER_PAID',TIMESTAMP'2026-08-01 10:05:00','{\"amount\":100}','order-events',0,2),
        ('evt-2',1000,'ORDER_PAID',TIMESTAMP'2026-08-01 10:05:00','{\"amount\":100}','order-events',0,3),
        ('evt-3',1000,'ORDER_SHIPPED',TIMESTAMP'2026-08-01 11:00:00','{\"carrier\":\"demo\"}','order-events',0,4),
        ('evt-bad',1001,'ORDER_UNKNOWN',TIMESTAMP'2026-08-01 11:05:00','{}','order-events',0,5)""",
    ),
    "fixture_legacy_customer_snapshots": (
        "customer_id BIGINT, name STRING, segment STRING, status STRING, _snapshot_id BIGINT",
        """(1,'Alice','SMB','ACTIVE',1),(2,'Bob','ENTERPRISE','ACTIVE',1),
        (1,'Alice','ENTERPRISE','ACTIVE',2),(2,'Bob','ENTERPRISE','ACTIVE',2),(3,'Carol','SMB','ACTIVE',2),
        (1,'Alice','ENTERPRISE','ACTIVE',3),(3,'Carol','SMB','PAUSED',3)""",
    ),
}


def seed_reference_sources(spark: Any, catalog: str) -> None:
    if not _IDENTIFIER.fullmatch(catalog):
        raise ValueError(f"unsafe catalog identifier: {catalog!r}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.reference")
    for table_name, (schema, values) in _FIXTURES.items():
        table = f"{catalog}.reference.{table_name}"
        spark.sql(
            f"CREATE TABLE IF NOT EXISTS {table} ({schema}) USING DELTA "
            "TBLPROPERTIES ('edp.fixture'='true','edp.fixture_version'='1')"
        )
        if spark.table(table).limit(1).count() == 0:
            spark.sql(f"INSERT INTO {table} VALUES {values}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    args = parser.parse_args()
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    seed_reference_sources(spark, args.catalog)
    print(f"[READY] reference fixture sources seeded in {args.catalog}.reference")


if __name__ == "__main__":
    main()
