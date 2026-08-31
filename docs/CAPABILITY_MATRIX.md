# Cheatsheet-to-Framework Capability Matrix

This matrix is the acceptance checklist connecting the pipeline-design cheatsheet to concrete framework artifacts.

| Design question / production concern | Framework representation | Enforced now? |
|---|---|---:|
| Current state vs change feed vs business event vs derived change | `semantics` | Yes |
| Full snapshot / watermark / CDC / Debezium / CDF / Kafka / custom | `capture.mechanism` | Yes |
| Net vs full/all change granularity | `capture.change_granularity` | Yes for P08-P11 |
| Where processing continues | `cursor` | Yes where required |
| Authoritative source order | `ordering` | Yes for change feed/SCD2 |
| Business/entity key | `identity.business_keys` | Yes for merge/SCD models |
| Source version identity | `identity.source_version_columns` | Contracted |
| Event identity | `identity.event_identity_columns` | Required for event history unless source ordering provides identity |
| Delivery/retry identity | `identity.delivery_identity_columns` + `delivery` | Contracted |
| Initial load/bootstrap handoff | `bootstrap` | Yes |
| Retry/redelivery/idempotency | `delivery.guarantee` + idempotency keys | Yes for at-least-once |
| Bronze meaning | `bronze.contract` | Yes and pattern-validated |
| Silver meaning | `silver.contract` | Yes and pattern-validated |
| Physical/logical delete completeness | `deletes` | Yes for soft delete / CDC / snapshot absence |
| Fidelity claim | `fidelity` | Required |
| Source/Bronze recovery retention | `retention` + `bronze.retention_days` | Required; key consistency checks enforced |
| DQ warn/quarantine/fail | `quality.rules[].action` | Yes |
| Reconciliation | `reconciliation` | Required for enabled datasets |
| Stable reconciliation cutoff | `reconciliation.cutoff_strategy` | Required |
| Schema evolution | `schema_evolution` | Required/defaulted |
| SCD2 stable identity and ordering | metadata cross-validation | Yes |
| Repair scope | `recovery` + runtime `repair_request` | Contract/DDL implemented |
| Source runtime cursor state | `platform_control.source_state` | DDL implemented |
| Release provenance | `platform_control.release_history` | DDL implemented; write step Phase 2 |
| Code rollback vs data recovery | ADR/runbooks | Yes architecturally |
| Failure injection | test directories/roadmap | Phase 4 |
| Native telemetry | Lakeflow event log + `system.lakeflow.*` | Architecture defined |
| Cost attribution | Databricks system/billing tables | Architecture defined |
| New semantic/vendor pattern | package entry points `edp.patterns` with definition + validation + runtime builder | Extension mechanism implemented |

A row marked architecture/Phase 2+ is intentionally not claimed as implemented runtime behavior yet. The goal is to prevent a green CI badge from overstating production readiness.
