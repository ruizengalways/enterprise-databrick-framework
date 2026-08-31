# ADR-005: Databricks Resource Ownership

Status: **Superseded by ADR-010**

## Historical decision

During the original single-repository architecture, Terraform owned stable account/workspace/Unity Catalog platform infrastructure, Declarative Automation Bundles owned workload resources such as Lakeflow Jobs and Pipelines, Git-owned Python/SQL implemented transformations, and Delta control tables owned runtime state.

The principle that **one resource must have one authoritative owner** remains valid. However, the repository ownership part of this ADR is no longer current.

## Current decision

ADR-010 split platform infrastructure from this reusable package repository:

- platform/admin Terraform, identities, workspace/catalog bindings and organisation-wide deployment templates belong to `enterprise-databrick-infra` or the consuming company's platform repo;
- workload Jobs/Pipelines/Bundle resources belong to the consuming workload repo;
- reusable semantic/runtime package code belongs here;
- runtime observations/state remain in Delta/system/control tables.

See `enterprise-databrick-infra/docs/adr/001-framework-infra-repository-boundary.md` for the current platform ownership boundary.
