# GitHub OIDC / Workload Identity Federation

GitHub-to-Databricks deployment identity is a **platform/deployment concern**, not framework package behavior.

This framework supports being run under a service principal supplied by the consuming platform, but it does not create that identity, federation policy, GitHub Environment or workspace grant.

The optional reference implementation and runbook live in [`enterprise-databrick-infra`](https://github.com/ruizengalways/enterprise-databrick-infra).

Current Databricks guidance recommends workload identity federation for automated workloads where possible, using short-lived OIDC/OAuth exchange rather than storing long-lived Databricks secrets. For GitHub Actions the deployment workflow normally needs `id-token: write`, `DATABRICKS_AUTH_TYPE=github-oidc`, a workspace `DATABRICKS_HOST`, and the Databricks service-principal application ID as `DATABRICKS_CLIENT_ID`.

Do not add organisation-specific OIDC subjects, account IDs, workspace URLs or service-principal IDs to this package repository.
