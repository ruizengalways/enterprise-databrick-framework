from __future__ import annotations

from edp_framework.metadata.models import BronzeContract, SilverContract, TableSpec
from edp_framework.patterns.contracts import PatternDefinition, RuntimeContext

from company_pattern_extension.runtime import register_runtime


class CompanyPatternProvider:
    def definitions(self) -> list[PatternDefinition]:
        return [
            PatternDefinition(
                id="X_COMPANY_001",
                name="Company-specific source pattern",
                bronze_contract=BronzeContract.RAW_APPEND,
                supported_silver_contracts=frozenset({SilverContract.CURRENT}),
                description="Replace with the real semantic difference, not merely a vendor name.",
                implementation_hint="company_package/custom_runtime",
            )
        ]

    def validate(self, spec: TableSpec) -> None:
        if spec.pattern_id != "X_COMPANY_001":
            return
        if spec.capture.provider_package != "company-pattern-extension":
            raise ValueError("X_COMPANY_001 requires company-pattern-extension")

    def build_runtime(self, spec: TableSpec, context: RuntimeContext) -> None:
        register_runtime(spec, context)


def provider() -> CompanyPatternProvider:
    return CompanyPatternProvider()
