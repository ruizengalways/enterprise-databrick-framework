# Repository Strategy

Status: current after the 2026-08-31 package/infra split.

## Decision

Use separate repositories for separate ownership/lifecycle boundaries:

```text
data-engineering-cheetsheet
  -> semantic/design knowledge

enterprise-databrick-framework
  -> versioned reusable Python package

enterprise-databrick-customer
  -> consuming reference workload + learning/certification evidence

enterprise-databrick-infra
  -> optional platform/IaC baseline
```

## Why the split is intentional

A reusable framework must work inside a company that already has workspaces, Unity Catalog, networking, identities and CI/CD. Requiring adoption of this project's Terraform would reduce reusability and force normal data engineers to own platform code unnecessarily.

The customer/reference repository proves the package boundary: it consumes the framework as a dependency and owns its own metadata, fixtures and expected results.

The infra repository is optional and independently useful for greenfield/platform-team learning. It is not a runtime dependency of the framework.

## Dependency direction

```text
cheatsheet (semantic reference)
       |
       v
framework package
       |
       v
customer / company workload

infra -> supplies platform capabilities to workload, when needed
```

Avoid circular source dependencies. In particular, the framework must never import customer or infra code.
