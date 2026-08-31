from __future__ import annotations

from importlib.metadata import entry_points
from typing import Iterable

from edp_framework.metadata.models import TableSpec
from edp_framework.patterns.builtins import BUILTIN_PATTERNS, validate_builtin_pattern
from edp_framework.patterns.contracts import (
    PatternDefinition,
    PatternProvider,
    RuntimeContext,
)


class PatternRegistry:
    def __init__(self, load_plugins: bool = True) -> None:
        self._definitions: dict[str, PatternDefinition] = {p.id: p for p in BUILTIN_PATTERNS}
        self._providers: list[PatternProvider] = []
        self._provider_by_pattern: dict[str, PatternProvider] = {}
        if load_plugins:
            self._load_entry_points()

    def _load_entry_points(self) -> None:
        for ep in entry_points(group="edp.patterns"):
            provider = ep.load()()
            self.register_provider(provider)

    def register_provider(self, provider: PatternProvider) -> None:
        definitions = provider.definitions()
        if not definitions:
            raise ValueError("pattern provider must register at least one definition")
        if not callable(getattr(provider, "build_runtime", None)):
            raise TypeError("pattern provider must implement build_runtime(spec, context)")

        for definition in definitions:
            if definition.id in self._definitions:
                raise ValueError(f"pattern already registered: {definition.id}")
            self._definitions[definition.id] = definition
            self._provider_by_pattern[definition.id] = provider
        self._providers.append(provider)

    def definitions(self) -> Iterable[PatternDefinition]:
        return self._definitions.values()

    def get(self, pattern_id: str) -> PatternDefinition:
        try:
            return self._definitions[pattern_id]
        except KeyError as exc:
            raise ValueError(
                f"unknown pattern_id {pattern_id!r}; install/register an extension package if this is a new pattern"
            ) from exc

    def validate(self, spec: TableSpec) -> PatternDefinition:
        definition = self.get(spec.pattern_id)
        if spec.pattern_id.startswith("P") and spec.pattern_id[1:].isdigit():
            validate_builtin_pattern(spec, definition)
        provider = self._provider_by_pattern.get(spec.pattern_id)
        if provider is not None:
            provider.validate(spec)
        return definition

    def build_extension_runtime(self, spec: TableSpec, context: RuntimeContext) -> None:
        """Register runtime behavior for an extension pattern.

        Built-in P01-P14 execution is owned by core Databricks runtime modules. This method
        is intentionally extension-only so a company package can add a new pattern without
        patching the core routing tree.
        """

        self.validate(spec)
        provider = self._provider_by_pattern.get(spec.pattern_id)
        if provider is None:
            raise ValueError(
                f"{spec.pattern_id} is a built-in pattern; use the core runtime router, not an extension runtime"
            )
        provider.build_runtime(spec, context)
