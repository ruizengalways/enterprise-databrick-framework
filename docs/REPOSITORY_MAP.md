# Repository map

This repository is an installable reusable library, not a Databricks platform deployment repository.

## Where to change things

| Goal | Location |
|---|---|
| Change metadata schema/contracts | `src/edp_framework/metadata/` |
| Add or change built-in semantic pattern behavior | `src/edp_framework/patterns/` and runtime modules |
| Add framework operational/recovery behavior | `src/edp_framework/operations/` |
| Add deterministic package tests | `tests/` |
| Show how a dataset contract looks | `examples/table_specs/` |
| Build a company/vendor extension | `templates/pattern-extension/` |
| Understand recovery/reconciliation semantics | `docs/runbooks/` and architecture docs |
| Provision Unity Catalog/workspaces/OIDC | **not here**; use the company platform or `enterprise-databrick-infra` |
| Define DEV/UAT/PROD Bundle targets | consuming workload/platform repo |

## Rule of thumb

If a change needs a workspace ID, cloud subscription/account, storage credential, Terraform backend, GitHub Environment, service-principal application ID, catalog name such as `edp_prod`, or organisation-specific approval gate, it does not belong in this package repository.

If the same Python behavior should work in ten different Databricks estates when given the appropriate Spark/Lakeflow/runtime context, it belongs here.
