# ADR-005: Databricks Resource Ownership

Status: Accepted

## Decision

Terraform owns stable account/workspace/Unity Catalog platform infrastructure. Declarative Automation Bundles own workload resources such as Lakeflow Jobs and Pipelines. Git-owned Python/SQL implements transformations. Delta control tables own runtime state.

No resource is managed by more than one mechanism without a dedicated ADR.
