# Integration with an existing Databricks platform

The framework is intentionally infrastructure-agnostic.

## Minimum integration contract

A consuming project/platform supplies:

1. an authenticated Databricks execution environment;
2. target catalog/schema names or fully qualified table names;
3. permissions for the runtime identity;
4. source connectivity/credentials;
5. Job/Lakeflow Pipeline deployment and scheduling;
6. environment promotion/approval rules.

The framework supplies metadata validation and reusable runtime semantics. It must not create workspaces, networks, storage credentials or service principals as a side effect of installing the package.

## Common adoption modes

### Existing enterprise platform

Use the company's existing workspaces, Unity Catalog, secret management, cluster/serverless policies and CI/CD. Install the framework wheel in the company workload repo and map the framework's runtime inputs to the existing platform.

### Greenfield/small platform

Optionally reuse modules/templates from `enterprise-databrick-infra`, then consume this framework package from the workload repository.

### Heavily regulated platform

The platform may use separate accounts/metastores/workspaces or domain-specific schemas. Those are deployment choices. Framework semantic contracts such as P10 CDC -> SCD2 must remain unchanged.

## Ownership boundary

The package can define a control-table schema contract and functions to create/use it. The platform decides **where** that schema lives and **which identity** may execute those functions.
