# ADR-001: Repository Boundary

Status: Accepted

## Decision

Create one new repository, `enterprise-databrick-framework`. Keep the reusable core as the installable package `src/edp_framework`. Do not create a separate core repository yet.

## Consequences

- clone/copy is self-contained for a new organisation
- code, metadata, tests and deployment definitions version together
- no cross-repo dependency drift
- extraction remains easy because the core already has a package boundary
