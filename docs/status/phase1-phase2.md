# Phase 1/2 implementation checkpoint

Status: implementation PR

## Implemented in this change

### Phase 1 foundation

- reusable Unity Catalog environment Terraform module
- isolated catalogs and long-lived base schemas
- least-privilege runtime UC grants
- separate workspace binding module using `databricks_workspace_binding`
- GitHub OIDC service-principal federation module
- explicit identity split between deployer and runtime principal
- personal DEV vs shared DEV target separation

### Phase 2 delivery spine

- Bundle direct deployment engine
- ephemeral PR namespace target
- shared DEV stable target
- UAT/PROD production targets
- immutable full Git SHA promotion
- release control-plane smoke job
- release provenance write to `platform_control.release_history`
- conditional remote PR integration workflow with automatic Bundle cleanup
- automatic shared DEV deployment after merge when OIDC variables exist
- Terraform module validation added to standard CI

## Deliberately not claimed yet

- no cloud-specific AWS/Azure/GCP workspace bootstrap is provisioned by this generic framework
- no remote Databricks deployment can run until GitHub Environment OIDC variables/permissions are configured
- no P01/P07/P10/P12 vertical slice is implemented yet
- reconciliation execution and repair executor remain Phase 4

## Exit criteria before Phase 3

1. standard PR validation passes,
2. Terraform modules validate against the pinned provider family,
3. GitHub OIDC is configured for at least CI and DEV,
4. remote PR integration successfully deploys/runs/destroys an isolated Bundle,
5. shared DEV deployment records a real Git SHA in `edp_dev.platform_control.release_history`.
