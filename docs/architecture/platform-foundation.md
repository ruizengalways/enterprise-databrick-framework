# Platform Foundation — Boundary from the Framework

This filename is retained to avoid breaking old links, but the platform foundation is **not owned by this package repository**.

The framework requires a consuming workload/platform to supply capabilities such as:

- an authenticated Databricks execution environment;
- writable target catalogs/schemas or equivalent destinations;
- runtime identity and least-privilege grants;
- source connectivity and credentials;
- Lakeflow Jobs/Pipelines or other scheduling/orchestration;
- environment promotion and approval policy;
- retention/recovery infrastructure sufficient for the declared data contract.

The framework must not assume fixed catalog names such as `edp_dev`/`edp_prod`, workspace IDs, GitHub Environments, service-principal IDs, cloud subscriptions/accounts or Terraform state.

For the optional reference implementation of those concerns, use [`enterprise-databrick-infra`](https://github.com/ruizengalways/enterprise-databrick-infra). For a concrete consumer that exercises the framework, use [`enterprise-databrick-customer`](https://github.com/ruizengalways/enterprise-databrick-customer).

A company may implement the same integration contract with a completely different workspace/catalog/environment topology without changing framework semantics.
