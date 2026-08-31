from __future__ import annotations

import argparse

from pyspark.sql import SparkSession

from edp_framework.operations.release_smoke import assert_control_plane_ready


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    args = parser.parse_args()

    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    tables = assert_control_plane_ready(spark, args.catalog)
    print(f"[PASS] control plane ready in {args.catalog}; verified {len(tables)} tables")


if __name__ == "__main__":
    main()
