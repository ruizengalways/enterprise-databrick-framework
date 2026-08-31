from __future__ import annotations

import argparse

from pyspark.sql import SparkSession

from edp_framework.operations.release_history import append_release_evidence


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--git-sha", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--bundle-target", required=True)
    parser.add_argument("--workflow-run-id", required=True)
    parser.add_argument("--deployed-by", required=True)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()

    spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
    release_id = append_release_evidence(
        spark,
        args.catalog,
        git_sha=args.git_sha,
        environment=args.environment,
        bundle_target=args.bundle_target,
        workflow_run_id=args.workflow_run_id,
        deployed_by=args.deployed_by,
        repository=args.repository,
    )
    print(f"[RECORDED] release_id={release_id} git_sha={args.git_sha} target={args.bundle_target}")


if __name__ == "__main__":
    main()
