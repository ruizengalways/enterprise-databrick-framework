# Project Context — Enterprise Databricks Framework

Last architecture/documentation audit: **2026-08-31**.

Read this file first when resuming this repository in a new conversation.

## Repository role

This repository is the **reusable installable data-engineering package**. It is not a company platform repo and not a reference-data repo.

Related repositories:

| Repository | Responsibility |
|---|---|
| `data-engineering-cheetsheet` | technology-neutral semantic/design source of truth; P01-P14 |
| `enterprise-databrick-framework` | reusable package and runtime/data-engineering semantics |
| `enterprise-databrick-customer` | independent reference consumer, learning fixtures and certification evidence |
| `enterprise-databrick-infra` | optional Terraform/platform baseline and deployment templates |

## Non-negotiable boundary

Framework code must not require the consuming company to adopt this project's Terraform, workspace layout, catalog names, GitHub Environments, OIDC identities or promotion topology.

A company with existing Databricks infrastructure should be able to install the framework wheel and use it from its own workload repository.

## Semantic principles

1. Classify source semantics before capture technology.
2. Capture mechanism is not target semantics.
3. SCD2 is a target/history contract, not an ingestion mode.
4. Source ordering and ingestion ordering are distinct.
5. Business, source-version, event and delivery identities are distinct.
6. Bronze meaning is explicit: current replica, observation/raw append, snapshot history or event history.
7. Incremental/change workloads declare bootstrap, delete completeness, idempotency, retention, reconciliation and recovery.
8. Git owns desired behavior; Delta/system/control tables own runtime state.
9. Code rollback and data recovery are separate.
10. Certification claims require evidence tied to an exact framework SHA.

## Current state at this audit

- package/infra split is merged on `main`;
- package CI validates metadata examples, lint, strict typing, tests and wheel build;
- P01-P14 semantic catalogue is present;
- executable runtime coverage is still being expanded and must be tracked in `docs/CAPABILITY_MATRIX.md`;
- `enterprise-databrick-customer` pins an exact framework SHA and is the independent certification source;
- real Databricks runtime/recovery certification must not be inferred from package CI.

Before stating newer status, inspect current `main`, open PRs, Actions and the customer repo's `certification/framework-lock.yml` + `certification/matrix.yml`.

## Where changes belong

- reusable metadata/runtime/recovery behavior -> this repo;
- customer/domain metadata, source fixtures, expected results, workload jobs/pipelines -> customer/company workload repo;
- workspaces, catalogs, OIDC, Terraform, environment topology -> infra/company platform repo;
- technology-neutral semantic taxonomy -> cheatsheet.

## Documentation audit note

Legacy monorepo-era files were corrected during the 2026-08-31 audit. `docs/architecture/platform-foundation.md` and `docs/runbooks/configure-github-oidc.md` now document only the boundary and point to infra rather than pretending those resources are owned here.
