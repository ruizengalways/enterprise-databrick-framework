# Project Context — Enterprise Databricks Framework

This is the **human-readable** framework context. Machine-readable repository ownership and implementation status live in `project/repository.yml` and `project/capabilities.yml`.

## Repository role

This repository is the **reusable installable data-engineering package**. It is not a company platform repo and not a reference-data repo.

Related repositories:

| Repository | Responsibility |
|---|---|
| `data-engineering-cheetsheet` | technology-neutral semantic/design source of truth; P01-P14 |
| `enterprise-databrick-framework` | reusable package and runtime/data-engineering behavior |
| `enterprise-databrick-customer` | independent reference consumer, learning fixtures, and certification evidence |
| `enterprise-databrick-infra` | optional Terraform/platform baseline and deployment templates |

## Non-negotiable boundary

Framework code must not require a consuming company to adopt this project's Terraform, workspace layout, catalog names, GitHub Environments, OIDC identities, or promotion topology.

A company with existing Databricks infrastructure should be able to install the framework wheel and use it from its own workload repository.

## Semantic principles

1. Classify source semantics before capture technology.
2. Capture mechanism is not target semantics.
3. SCD2 is a target/history contract, not an ingestion mode.
4. Source ordering and ingestion ordering are distinct.
5. Business, source-version, event, and delivery identities are distinct.
6. Bronze meaning is explicit: current replica, observation/raw append, snapshot history, or event history.
7. Incremental/change workloads declare bootstrap, delete completeness, idempotency, retention, reconciliation, and recovery.
8. Git owns desired behavior; Delta/system/control tables own runtime state.
9. Code rollback and data recovery are separate.
10. Certification claims require evidence tied to exact framework/customer SHAs.

## Capability model

The framework separates semantic contracts, runtime implementation, package quality, Databricks runtime certification, and recovery certification. See `docs/CAPABILITY_MATRIX.md` for the human explanation.

Current implementation state is intentionally not duplicated in this Markdown. Automated consumers read `project/capabilities.yml`; exact-SHA certification claims come from the customer repository's `certification/` directory.

## Where changes belong

- reusable metadata/runtime/recovery behavior -> this repo;
- customer/domain metadata, source fixtures, expected results, workload jobs/pipelines -> customer/company workload repo;
- workspaces, catalogs, OIDC, Terraform, environment topology -> infra/company platform repo;
- technology-neutral semantic taxonomy -> cheatsheet.

## Human vs machine documentation

```text
Human narrative
  README.md
  docs/**/*.md

Machine repository/capability state
  project/**/*.yml

Independent certification state
  enterprise-databrick-customer/certification/**/*.yml
```

Automation must not parse Markdown to infer runtime support or certification status.

## How to resume this repository

For a human, read this file, the README, relevant ADRs, and runbooks.

For an automated agent/new conversation, read:

1. this repo's `project/repository.yml`;
2. this repo's `project/capabilities.yml`;
3. the customer repo's `project/context.yml` and `project/state.yml`;
4. the customer certification lock/matrix;
5. current `main`, open PRs, and Actions.

Fast-changing Databricks runtime APIs must be re-verified against current official documentation before material implementation changes.
