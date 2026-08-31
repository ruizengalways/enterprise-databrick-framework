# ADR-007: Separate personal DEV from shared DEV

Status: Accepted

## Decision

Use two Bundle deployment targets against the DEV environment:

- `dev`: developer-owned, development mode, disposable.
- `shared_dev`: stable CI/CD-owned deployment, production mode semantics, service-principal runtime.

Both use `edp_dev`; they do not share Bundle state or resource identity.

## Why

A single `dev` target cannot safely represent both a developer sandbox and the exact release that is promoted to UAT. Mixing those concerns makes release provenance ambiguous and can let developer lifecycle operations affect shared resources.

## Consequence

Promotion evidence is recorded from `shared_dev`, then the exact Git SHA can be promoted to UAT and PROD.
