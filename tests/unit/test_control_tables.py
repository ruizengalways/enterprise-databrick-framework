import pytest

from edp_framework.operations.control_tables import control_table_ddl


def test_control_ddl_contains_required_operability_tables() -> None:
    ddl = "\n".join(control_table_ddl("edp_prod"))
    for name in (
        "release_history",
        "source_state",
        "reconciliation_result",
        "repair_request",
        "repair_run",
        "quality_result",
        "incident_event",
    ):
        assert f"`{name}`" in ddl


def test_catalog_identifier_is_validated() -> None:
    with pytest.raises(ValueError, match="unsafe Unity Catalog identifier"):
        control_table_ddl("edp_prod; DROP CATALOG x")
