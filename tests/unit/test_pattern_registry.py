import pytest

from edp_framework.metadata.loader import load_table_spec
from edp_framework.metadata.models import BronzeContract, SilverContract
from edp_framework.patterns.contracts import PatternDefinition
from edp_framework.patterns.registry import PatternRegistry

DEBEZIUM_EXAMPLE = "examples/table_specs/customer_debezium_scd2.yml"


def test_builtin_catalog_contains_all_cheatsheet_patterns() -> None:
    registry = PatternRegistry(load_plugins=False)
    ids = {definition.id for definition in registry.definitions()}
    assert ids == {f"P{i:02d}" for i in range(1, 15)}


def test_debezium_scd2_routes_to_full_event_pattern() -> None:
    spec = load_table_spec(DEBEZIUM_EXAMPLE)
    definition = PatternRegistry(load_plugins=False).validate(spec)
    assert definition.id == "P10"
    assert definition.implementation_hint == "cdc/full_event"


def test_pattern_semantics_cannot_be_mislabeled() -> None:
    spec = load_table_spec(DEBEZIUM_EXAMPLE)
    spec.semantics = "current_state"

    with pytest.raises(ValueError, match="requires semantics change_feed"):
        PatternRegistry(load_plugins=False).validate(spec)


def test_extension_must_ship_runtime_builder() -> None:
    class MetadataOnlyProvider:
        def definitions(self):
            return [
                PatternDefinition(
                    id="X_BAD_001",
                    name="metadata only",
                    bronze_contract=BronzeContract.RAW_APPEND,
                    supported_silver_contracts=frozenset({SilverContract.CURRENT}),
                    description="invalid extension",
                    implementation_hint="none",
                )
            ]

        def validate(self, spec):
            return None

    with pytest.raises(TypeError, match="build_runtime"):
        PatternRegistry(load_plugins=False).register_provider(MetadataOnlyProvider())  # type: ignore[arg-type]
