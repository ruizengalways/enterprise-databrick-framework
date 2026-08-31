# ADR-010: Split reusable framework package from Databricks platform infrastructure

Status: Accepted

## Context

A new organisation may already have Databricks workspaces, Unity Catalog, identities, networking, storage, secrets and CI/CD. Requiring framework adopters to clone or understand Terraform creates unnecessary ownership coupling. Normal data-engineering team members also should not need platform-IaC permissions for routine dataset onboarding.

## Decision

`enterprise-databrick-framework` becomes an installable package repository containing reusable semantic/runtime code, tests, examples and framework documentation.

Platform concerns move to `enterprise-databrick-infra`, including Terraform modules, environment topology, workspace/catalog binding, service-principal/OIDC setup and platform deployment templates.

The two repositories must remain independently adoptable. The framework accepts platform resources as inputs and never provisions them.

## Consequences

- A company with existing infrastructure can adopt only the framework wheel.
- Platform and data-engineering ownership/review paths are separated.
- Framework CI is faster and does not need Databricks/Terraform credentials.
- Real Databricks acceptance testing can live outside the package repo while still testing a pinned framework artifact.
- Company-specific workload repositories own their own Bundle resources, scheduling and domain transformations.
