# Terraform boundary

Terraform owns long-lived Databricks platform infrastructure. Declarative Automation Bundles own workload resources such as Lakeflow Jobs and Pipelines.

## Modules

- `modules/unity_catalog_environment`: one isolated environment catalog plus long-lived base schemas and least-privilege UC grants.
- `modules/workspace_binding`: explicit binding of an isolated securable to an allowed workspace. Keep this in a separate state from catalog creation so binding lifecycle cannot accidentally break catalog destruction/replacement.
- `modules/github_oidc_service_principal`: Databricks-managed service principal plus a GitHub Actions workload-identity federation policy.

## State boundaries

Use separate Terraform state for account-level identity, workspace/Unity Catalog foundations, and cloud-specific workspace/storage bootstrap. Do not let one state file own both a production workspace and every workload deployed into it.

Recommended composition:

```text
cloud/account bootstrap
        ↓
Databricks workspace + metastore assignment
        ↓
account identity / GitHub OIDC
        ↓
Unity Catalog environment
        ↓
workspace binding
        ↓
Declarative Automation Bundles
```

The repository intentionally does not hard-code AWS, Azure, or GCP workspace creation. A company-specific stack composes these reusable modules with the cloud provider resources it actually uses.

## Provider version

Modules require Databricks Terraform provider `~> 1.128` and Terraform `>= 1.7.5`. Pin exact versions in company root modules/lock files according to the organisation's upgrade policy.

## Safety rules

1. Run `terraform plan` in CI before apply.
2. Protect PROD apply with an environment approval.
3. Never use personal identities for production automation.
4. Never manage the same Job/Pipeline in Terraform and a Bundle.
5. Catalogs are created with `ISOLATED` access mode.
6. Binding and catalog lifecycle are separate modules/states.
7. Production Terraform state must use a remote encrypted backend with locking appropriate to the chosen cloud.
