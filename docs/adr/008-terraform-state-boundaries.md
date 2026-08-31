# ADR-008: Separate Terraform state by platform concern

Status: Accepted

## Decision

Do not use one Terraform state for the entire Databricks organisation.

Use independent roots/state for at least:

1. cloud/account/workspace bootstrap,
2. account identity and GitHub OIDC federation,
3. Unity Catalog environment foundation,
4. workspace/securable bindings.

Bundle workload resources are not placed in Terraform state.

## Why

These resources have different privileges, blast radius and change cadence. Workspace bindings in particular can remove access to a securable and should not be implicitly destroyed while replacing a catalog module.

## Consequence

Company stacks compose reusable modules and pass outputs between states through approved remote-state/configuration mechanisms. The framework modules remain cloud-neutral.
