# Platform foundation

This document defines the reusable infrastructure and deployment boundary for the framework.

## Environment model

```text
Personal developer deployment
  target: dev
  catalog: edp_dev
  run-as: developer

Ephemeral PR integration
  target: ci
  catalog: edp_ci
  namespace: pr-<number>
  run-as: CI runtime service principal

Stable shared development
  target: shared_dev
  catalog: edp_dev
  run-as: DEV runtime service principal

UAT
  target: uat
  catalog: edp_uat
  run-as: UAT runtime service principal

PROD
  target: prod
  catalog: edp_prod
  run-as: PROD runtime service principal
```

`dev` and `shared_dev` intentionally share the DEV catalog but not the Bundle deployment state or resource lifecycle. Personal development is disposable and user-prefixed; shared DEV is a stable promoted release.

## Identity separation

Each shared environment should use two automation identities:

```text
GitHub deployer service principal
  -> authenticates by GitHub OIDC
  -> validates/plans/deploys Bundle resources

Databricks runtime service principal
  -> configured by Bundle run_as
  -> receives only data/runtime privileges required by workloads
```

The deployer is not automatically the data-plane runtime identity. This avoids making a CI/CD identity the implicit owner of production business execution.

## Unity Catalog

Terraform creates long-lived environment catalogs with `isolation_mode = ISOLATED`. The default base schemas are:

- `bronze`
- `silver`
- `gold`
- `reference`
- `quarantine`
- `platform_control`

Environment-specific domain schemas can be added later, but adding a source must not require editing the framework core.

Catalog binding is managed separately from catalog creation. This is deliberate: binding changes can remove access from workspaces, so their lifecycle should not be coupled to catalog replacement/destruction.

## Bundle deployment paths

Shared targets deploy under a controlled `/Workspace/Platform/.bundle/...` path. The platform bootstrap must apply folder ACLs so only the deployment identity/platform administrators can modify deployed source artifacts.

Do not deploy production Bundles under `/Workspace/Shared`.

## Direct deployment engine

The Bundle explicitly uses `bundle.engine: direct`. Terraform owns platform infrastructure; the Bundle direct engine owns workload resource state. These are separate concerns despite both being declarative.

## Release invariant

A promoted release is the exact full 40-character Git SHA:

```text
SHA X
 -> validated
 -> deployed to shared DEV
 -> same SHA X promoted to UAT
 -> same SHA X promoted to PROD
```

After deployment the `release_gate` job:

1. bootstraps/validates `platform_control`,
2. smoke-checks required control tables,
3. records Git SHA, target, GitHub workflow run and deploy actor in `platform_control.release_history`.

A code rollback therefore means promoting a previous known-good SHA. Data recovery remains a separate workflow.
