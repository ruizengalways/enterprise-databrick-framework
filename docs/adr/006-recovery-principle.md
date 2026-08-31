# ADR-006: Recovery Principle

Status: Accepted

## Decision

Repair from the highest trustworthy layer and regenerate derived state using normal production logic. Code rollback and data recovery remain separate operations.

## Examples

- bad code: redeploy known-good Git SHA
- bad Silver rows: replay affected trusted Bronze keys/window
- missing source history: snapshot resync
- accidental Delta mutation inside retention: evaluate Delta restore followed by normal downstream recomputation
