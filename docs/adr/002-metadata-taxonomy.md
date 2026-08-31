# ADR-002: Metadata Taxonomy

Status: Accepted

## Decision

Do not use a single `load_type` field. Model source semantics, capture technology, change granularity, cursor, ordering, identities, Bronze contract, Silver contract, delete semantics, reconciliation and recovery independently.

## Rationale

Watermark, Debezium, Kafka, Delta CDF and SCD2 answer different architectural questions. Flattening them creates invalid combinations and hides recovery guarantees.
