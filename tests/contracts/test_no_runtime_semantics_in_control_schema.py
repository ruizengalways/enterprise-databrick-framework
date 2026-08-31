from edp_framework.operations.control_tables import control_table_ddl


def test_runtime_control_tables_do_not_own_pipeline_desired_state() -> None:
    ddl = "\n".join(control_table_ddl("edp_dev")).lower()
    forbidden = ["business_keys", "pattern_id", "silver_contract", "bronze_contract"]
    for field in forbidden:
        assert field not in ddl
