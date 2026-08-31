# Configure GitHub OIDC for Databricks deployments

Use workload identity federation. Do not store Databricks PATs or long-lived client secrets in GitHub.

## GitHub Environments

Create these GitHub Environments:

- `ci`
- `dev`
- `uat`
- `prod`

Use environment protection/required reviewers for UAT/PROD according to organisational policy.

For each environment define GitHub Environment variables:

```text
DATABRICKS_HOST
DATABRICKS_CLIENT_ID
DATABRICKS_RUNTIME_CLIENT_ID
DATABRICKS_OPERATOR_GROUP
```

Meaning:

- `DATABRICKS_HOST`: workspace URL for that environment.
- `DATABRICKS_CLIENT_ID`: deployment service-principal application ID authenticated by GitHub OIDC.
- `DATABRICKS_RUNTIME_CLIENT_ID`: service-principal application ID used by Bundle `run_as`.
- `DATABRICKS_OPERATOR_GROUP`: Databricks group allowed to manage the deployed workload resources.

## Federation subject

The Terraform OIDC module uses an Environment-scoped GitHub subject:

```text
repo:<owner>/<repository>:environment:<environment>
```

For this repository examples are:

```text
repo:ruizengalways/enterprise-databrick-framework:environment:ci
repo:ruizengalways/enterprise-databrick-framework:environment:dev
repo:ruizengalways/enterprise-databrick-framework:environment:uat
repo:ruizengalways/enterprise-databrick-framework:environment:prod
```

The GitHub workflow must declare the matching `environment:` value; the OIDC subject is an exact security boundary.

## Workflow authentication

Workflows set:

```text
permissions:
  id-token: write
  contents: read

DATABRICKS_AUTH_TYPE=github-oidc
DATABRICKS_HOST=<environment variable>
DATABRICKS_CLIENT_ID=<deployment SP application ID>
```

The Databricks CLI exchanges the GitHub OIDC token for a short-lived Databricks OAuth token.

## Bootstrap sequence

1. Create/identify Databricks account and workspaces.
2. Configure account-level Terraform authentication using a temporary/admin bootstrap path approved by the organisation.
3. Apply `github_oidc_service_principal` for each GitHub Environment.
4. Apply Unity Catalog environment foundations.
5. Apply workspace bindings from a dedicated binding state.
6. Grant the deployment SP the workspace permissions required to manage Bundle workload resources.
7. Grant the runtime SP only the Unity Catalog/runtime privileges needed by jobs/pipelines.
8. Add GitHub Environment variables.
9. Open a test PR and confirm `Databricks PR integration` runs rather than skips.
10. Merge and confirm `Deploy shared DEV` writes release provenance.

## Rotation and incident response

OIDC has no Databricks secret to rotate. If CI/CD identity is compromised:

1. disable/remove the federation policy,
2. disable the service principal if necessary,
3. revoke excessive workspace/UC grants,
4. inspect audit logs and deployment history,
5. create a replacement policy/identity,
6. revalidate known-good Git SHA before resuming promotion.
