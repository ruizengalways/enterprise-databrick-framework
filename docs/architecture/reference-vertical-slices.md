# Reference vertical slices

The reference vertical slices prove that the framework's metadata contracts can compile into materially different Databricks execution semantics without building one universal notebook.

## Scope boundary

The reference pipeline begins at a deterministic Delta relation that represents what the capture edge delivered. This is deliberate.

```text
real company source edge                    reference proof edge
------------------------                    --------------------
JDBC / Lakeflow Connect / Kafka             deterministic Delta fixture
Debezium / CDF / API             OR         deterministic Delta fixture
           |                                      |
           +------------ capture contract --------+
                                  |
                               Bronze
                                  |
                      reusable semantic handler
                                  |
                       Silver / quarantine
```

The framework therefore does **not** claim that the fixture is a Kafka broker, Debezium connector, SQL Server reader, or API client. A production source package/connector owns capture and parsing; the built-in handler owns the reusable downstream semantics.

## Implemented handlers

### P01 — complete snapshot -> current state

- source: complete deterministic snapshot
- Bronze: materialized current replica
- Silver: materialized snapshot replacement
- quality: fail expectation for required country code

This pattern intentionally does not invent incremental history.

### P07 — watermark + lookback + soft delete -> Raw Append -> current state

The fixture models **already extracted source observations**, including an intentional reread of the same source version.

- Bronze: append observations
- source version: `row_version`
- delivery identity: `_ingest_run_id`, `_ingest_sequence`
- Silver: AUTO CDC SCD1/current state ordered by `row_version`
- soft delete: retained as `is_deleted=true`
- quarantine: invalid email observation excluded from trusted Silver and preserved separately

The SQL Server/JDBC watermark query itself is a capture-edge concern and will be supplied by the corresponding source package. The P07 handler does not hard-code JDBC.

### P10 — full change feed -> Event Bronze -> SCD2

The fixture models a canonicalised CDC delivery contract with deliberately out-of-order events.

- Bronze: event history
- business key: `customer_id`
- source ordering: `source_lsn`, `source_event_sequence`
- Silver: AUTO CDC SCD2
- delete predicate: supplied by `capture.options.apply_as_deletes`
- transport/provider columns excluded through `capture.options.runtime_except_columns`
- quarantine: unknown operation preserved outside trusted Silver

The core handler does not know that Debezium uses `_operation='d'`. That provider-specific expression lives in the source/capture metadata. A Delta CDF/native CDC package can reuse P10 with a different expression and source relation.

### P12 — business events -> canonical event stream

- Bronze: event history
- event identity: metadata-driven
- event-time column: `silver.effective_time_column`
- dedup retention: `capture.options.dedup_watermark`
- Silver: bounded stateful deduplication
- quarantine: unsupported domain event type

The reusable handler does **not** define the canonical order-event columns. The reference pipeline explicitly injects `transform_order_events()`. Business/domain mapping remains code owned by the domain, while event capture/dedup semantics remain reusable.

### P02 — snapshot history -> snapshot-derived SCD2

- Bronze: snapshot history
- version: `_snapshot_id`
- Silver: `create_auto_cdc_from_snapshot_flow`
- SCD2 fidelity: snapshot interval only
- deletion: absence from a later complete snapshot closes the active SCD2 row

The reference adapter enumerates deterministic snapshot versions. A production provider replaces this adapter with its own versioned snapshot source contract.

## Stable schema layout

The default reusable layout is:

```text
<environment catalog>
  bronze
  silver
  gold
  reference
  quarantine
  platform_control
```

Domain identity is carried in table names, for example `bronze.crm_customer_observation`. This keeps normal domain onboarding out of Terraform. Organisations that require domain-schema isolation can replace the schema-layout profile under an ADR without changing the pattern semantics.

## Quality behaviour

The runtime separates three outcomes:

- FAIL rules -> Lakeflow `expect_or_fail`
- WARN rules -> Lakeflow `expect`
- QUARANTINE rules -> explicit invalid-row route plus a trusted valid-row route

A quarantined row is not silently dropped from all lineage.

## Verification job

`reference_vertical_slice_validation` performs:

```text
seed deterministic source fixtures
        -> run Lakeflow reference pipeline
        -> execute exact output assertions
```

The assertions cover current-state convergence, soft deletes, quarantine counts, out-of-order CDC ordering, CDC deletes, duplicate event suppression, snapshot-derived SCD2 and snapshot-absence deletes.

## Current proof level

Static Python/metadata/Terraform CI validates the implementation. Actual Lakeflow execution is **not yet claimed as proven** because the repository's GitHub Databricks OIDC environments are not configured. Once CI OIDC is connected, this validation job becomes the remote integration proof and must pass before the Phase 3 implementation is called operationally verified.
