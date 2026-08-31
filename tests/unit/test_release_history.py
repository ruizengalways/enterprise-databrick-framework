from __future__ import annotations

from datetime import datetime

import pytest

from edp_framework.operations.release_history import release_evidence_row, validate_git_sha
from edp_framework.operations.release_smoke import assert_control_plane_ready


class _FakeCatalog:
    def __init__(self, existing: set[str]) -> None:
        self._existing = existing

    def tableExists(self, name: str) -> bool:  # noqa: N802 - mirrors PySpark API
        return name in self._existing


class _FakeSpark:
    def __init__(self, existing: set[str]) -> None:
        self.catalog = _FakeCatalog(existing)


def test_validate_git_sha_requires_full_sha() -> None:
    sha = "A" * 40
    assert validate_git_sha(sha) == "a" * 40

    with pytest.raises(ValueError, match="40-character"):
        validate_git_sha("abc123")


def test_release_row_contains_immutable_provenance() -> None:
    row = release_evidence_row(
        git_sha="1" * 40,
        environment="prod",
        bundle_target="prod",
        workflow_run_id="12345",
        deployed_by="github-actions",
        repository="ruizengalways/enterprise-databrick-framework",
    )

    assert row["git_sha"] == "1" * 40
    assert row["status"] == "SUCCESS"
    assert row["metadata"]["release_contract"] == "immutable_git_sha"
    assert isinstance(row["deployed_at"], datetime)


def test_smoke_check_requires_all_control_tables() -> None:
    prefix = "edp_prod.platform_control."
    required = {
        prefix + name
        for name in (
            "release_history",
            "pipeline_run",
            "table_run",
            "source_state",
            "reconciliation_run",
            "reconciliation_result",
            "quality_result",
            "repair_request",
            "repair_run",
            "schema_change_event",
            "incident_event",
        )
    }
    spark = _FakeSpark(required)
    assert len(assert_control_plane_ready(spark, "edp_prod")) == 11

    required.remove(prefix + "source_state")
    with pytest.raises(RuntimeError, match="source_state"):
        assert_control_plane_ready(_FakeSpark(required), "edp_prod")
