from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

_GIT_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def validate_git_sha(value: str) -> str:
    if not _GIT_SHA.fullmatch(value):
        raise ValueError("git_sha must be the full 40-character hexadecimal commit SHA")
    return value.lower()


def release_evidence_row(
    *,
    git_sha: str,
    environment: str,
    bundle_target: str,
    workflow_run_id: str,
    deployed_by: str,
    repository: str,
) -> dict[str, Any]:
    return {
        "release_id": str(uuid4()),
        "git_sha": validate_git_sha(git_sha),
        "environment": environment,
        "bundle_target": bundle_target,
        "workflow_run_id": workflow_run_id,
        "deployed_at": datetime.now(timezone.utc),
        "deployed_by": deployed_by,
        "status": "SUCCESS",
        "metadata": {
            "repository": repository,
            "release_contract": "immutable_git_sha",
        },
    }


def append_release_evidence(
    spark: Any,
    catalog: str,
    *,
    git_sha: str,
    environment: str,
    bundle_target: str,
    workflow_run_id: str,
    deployed_by: str,
    repository: str,
) -> str:
    if not _IDENTIFIER.fullmatch(catalog):
        raise ValueError(f"unsafe Unity Catalog identifier: {catalog!r}")

    row = release_evidence_row(
        git_sha=git_sha,
        environment=environment,
        bundle_target=bundle_target,
        workflow_run_id=workflow_run_id,
        deployed_by=deployed_by,
        repository=repository,
    )
    table = f"{catalog}.platform_control.release_history"
    spark.createDataFrame([row]).write.mode("append").saveAsTable(table)
    return row["release_id"]
