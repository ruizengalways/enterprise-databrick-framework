# Streaming Checkpoint Recovery

Checkpoint reset is an exception path, not a normal retry mechanism.

Before reset:

1. stop concurrent writers
2. identify last trustworthy source position and target version
3. verify source/Bronze retention can cover replay
4. choose selective replay, backup+backfill or full refresh
5. record an approved repair request
6. execute with deterministic event/source-version idempotency
7. reconcile through an explicit source cutoff
8. resume normal processing only after validation
