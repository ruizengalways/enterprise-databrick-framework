# Runtime Boundary

This document is for humans. Machine-readable released capability state lives in `project/capabilities.yml`.

## Principle

The reusable framework owns **semantic materialisation after a normalized capture boundary**. It does not attempt to become a universal connector product.

```text
source technology
  JDBC / API / Kafka / Debezium / files / vendor connector
            |
            v
company/workload capture adapter
  authenticate
  discover/read
  apply source-specific cursor/window rules
  normalize provider payload/metadata
            |
            v
normalized relation or snapshot callback
            |
            v
enterprise-databrick-framework
  validate semantic contract
  materialize Bronze meaning
  enforce DQ/quarantine
  converge/apply ordered changes
  materialize Silver meaning
```

The same semantic pattern can therefore be reused with different source technologies without source-specific branches spreading through core.

## First built-in runtime verticals

### P01 — full snapshot to current state

The workload supplies the normalized complete snapshot relation. The framework creates current-replica Bronze and authoritative Silver materializations.

### P02 — complete snapshot history to SCD2

The consuming workload supplies a `snapshot_source(last_version)` callback compatible with Lakeflow `create_auto_cdc_from_snapshot_flow()`.

Snapshot discovery stays outside core because it can mean retained files, API snapshot versions, database exports, or another Bronze snapshot store. The callback must return the next complete snapshot/version without running unsupported Spark actions inside pipeline dataset definitions.

### P07 — watermark/lookback/soft-delete observations

The capture adapter owns the actual watermark query and lookback window. The framework receives append-only observations, retains raw Bronze observations, filters quarantine-invalid rows, then uses authoritative source-version ordering to converge the Silver current state.

`current_soft_delete` means an `is_deleted=true` row remains part of the current state. It is deliberately **not** mapped to a physical AUTO CDC delete.

Raw append observations still do not reconstruct intermediate source changes that the current-state source never exposed.

### P10 — full captured changes to SCD1/SCD2

The capture adapter normalizes the provider-specific CDC envelope. The framework preserves event Bronze and applies ordered AUTO CDC semantics.

Provider operation codes are not guessed. A CDC-delete workload must explicitly declare `apply_as_deletes`.

Delete tombstone retention is also explicit. The target streaming-table property `pipelines.cdc.tombstoneGCThresholdInSeconds` must exceed the declared maximum out-of-order delay so late records cannot incorrectly resurrect or overwrite deleted state.

### P12 — business events to canonical events

The workload supplies normalized domain events. The framework preserves event Bronze, separates quarantine-invalid events, applies an explicit event-time watermark, and deduplicates by event identity within that watermark before optional workload-owned canonical transformation.

The dedup watermark is a business/operability contract. Core never invents it.

## What belongs in a workload or extension adapter

Examples:

- SQL/JDBC watermark query and inclusive/exclusive boundaries;
- initial-source snapshot acquisition;
- raw Debezium envelope decoding;
- Kafka/Event Hubs connection and authentication;
- API pagination/cursor handling;
- file discovery and schema-specific parsing;
- vendor-specific operation-code mapping;
- domain-specific canonical event transformation.

When an adapter introduces a genuinely new semantic pattern rather than merely another transport/provider, implement it through the framework extension-package contract.

## Certification boundary

Package CI proves the registration code is linted, typed, unit tested, and buildable. It does not prove Databricks execution.

`enterprise-databrick-customer` independently pins an exact framework SHA and owns C3 real-Databricks and C4 failure/recovery evidence.
