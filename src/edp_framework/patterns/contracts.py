from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from edp_framework.metadata.models import BronzeContract, SilverContract, TableSpec


@dataclass(frozen=True)
class PatternDefinition:
    id: str
    name: str
    bronze_contract: BronzeContract
    supported_silver_contracts: frozenset[SilverContract]
    description: str
    implementation_hint: str


@dataclass(frozen=True)
class RuntimeContext:
    """Databricks runtime objects passed to an extension without coupling core to PySpark imports.

    `spark` is the active SparkSession and `pipelines` is normally `pyspark.pipelines` (`dp`).
    Keeping them injected makes extension packages unit-testable outside Databricks.
    """

    spark: Any
    pipelines: Any
    environment: str
    catalog: str
    options: dict[str, Any] = field(default_factory=dict)


class PatternProvider(Protocol):
    """Extension contract for a genuinely new pattern.

    A package owns three things together: semantic declaration, metadata validation, and
    Databricks runtime registration. This prevents a plugin that merely makes validation
    green without providing executable behavior.
    """

    def definitions(self) -> list[PatternDefinition]: ...

    def validate(self, spec: TableSpec) -> None: ...

    def build_runtime(self, spec: TableSpec, context: RuntimeContext) -> None: ...
