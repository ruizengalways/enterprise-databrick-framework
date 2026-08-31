# Phase 3 implementation checkpoint

Status: executable reference implementation in PR; remote Lakeflow proof pending

## Implemented in code

- P01 complete snapshot/current handler
- P02 snapshot-history -> AUTO CDC FROM SNAPSHOT -> SCD2 handler
- P07 raw watermark/lookback observations -> AUTO CDC current-state handler
- P10 full change-feed Event Bronze -> AUTO CDC SCD2 handler
- P12 business-event Event Bronze -> bounded dedup canonical-event handler
- fully-qualified environment/catalog relation resolution
- metadata-driven delivery-column exclusions
- metadata-driven CDC delete predicate
- explicit domain-transform injection seam
- fail/warn expectations and explicit quarantine routes
- deterministic reference source fixtures
- exact-output Databricks verification task
- Bundle pipeline/job resources for running the vertical-slice proof
- stable layer schema ADR
- runtime-contract preflight integrated into `edp validate`

## Deliberately outside core

- JDBC/SQL Server watermark query implementation
- Kafka/Debezium transport setup
- Lakeflow Connect configuration
- Delta CDF source adapter
- API/file capture implementation
- domain-specific business mappings

Those belong to source/provider packages or explicit domain code. They must satisfy the same capture contract and then reuse the semantic handlers where appropriate.

## Not yet claimed

- the Lakeflow pipeline has not executed in a real workspace from GitHub CI because OIDC variables are not configured
- P03/P04/P05/P06/P08/P09/P11/P13/P14 executable handlers are not implemented yet
- reconciliation execution and repair orchestration remain Phase 4

## Next proof gate

1. configure GitHub `ci` and `dev` Databricks OIDC environments,
2. run PR isolated Bundle deployment,
3. execute `reference_vertical_slice_validation`,
4. confirm exact assertions pass,
5. destroy PR resources,
6. merge the same SHA and rerun in shared DEV,
7. persist the exact SHA into `platform_control.release_history`.
