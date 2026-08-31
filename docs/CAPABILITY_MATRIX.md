# Capability matrix

Legend: **implemented** = reusable package code exists and is covered by package tests; **in progress** = design/contract exists but executable coverage is still being expanded.

| Capability | Package status | Platform dependency |
|---|---|---|
| Strict dataset metadata model | implemented | none |
| P01-P14 semantic catalogue | implemented | none |
| Cross-field safety validation | implemented | none |
| Extension entry point `edp.patterns` | implemented | none |
| Runtime control-table DDL helpers | implemented | writable catalog/schema supplied externally |
| Release evidence helpers | implemented | execution identity/catalog supplied externally |
| Full snapshot runtime | in progress | Spark/Lakeflow context |
| Watermark/lookback runtime | in progress | source adapter + Spark/Lakeflow context |
| Full CDC -> SCD2 runtime | in progress | captured change source + Lakeflow context |
| Snapshot -> SCD2 runtime | in progress | complete snapshot source + Lakeflow context |
| Business-event runtime | in progress | event source + Spark/Lakeflow context |
| Reconciliation executor | in progress | source/target access |
| Repair executor | in progress | source/target access and organisation approval policy |
| Terraform workspaces/catalogs/OIDC | out of scope | companion infra/company platform |
| DEV/UAT/PROD deployment | out of scope | consuming repo/platform CI/CD |

The framework can declare what runtime capability is required; it does not own the organisation-specific infrastructure that provides it.
