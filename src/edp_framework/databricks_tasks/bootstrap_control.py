from __future__ import annotations

import argparse

from pyspark.sql import SparkSession

from edp_framework.operations.control_tables import ensure_control_tables


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    args = parser.parse_args()
    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    ensure_control_tables(spark, args.catalog)


if __name__ == "__main__":
    main()
