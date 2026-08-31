# Framework Capabilities — Human Guide

This document explains **how to interpret framework capabilities**. It is not the machine-readable current-status source.

Authoritative implementation state lives in [`project/capabilities.yml`](../project/capabilities.yml). Independent cross-repository certification state lives in `enterprise-databrick-customer/certification/matrix.yml`.

## Capability layers

The framework contains several different kinds of capability and they must not be collapsed into one status word.

### Semantic/contract capability

The package can understand and validate a pattern contract. This includes the P01-P14 taxonomy, cross-field invariants, identity/order/delete semantics, Bronze/Silver contracts, retention, reconciliation, and recovery declarations.

### Runtime implementation capability

The package can register or execute the corresponding reusable Databricks behavior. A semantic pattern can exist before its runtime implementation is released.

### Package quality capability

The implementation passes normal package checks such as unit tests, strict typing, linting, metadata validation, and wheel build.

### Databricks runtime certification

The released package has been exercised from the independent customer repository in a real Databricks environment against deterministic inputs and expected outputs.

### Recovery certification

Failure injection, replay/reset, reconciliation, and repair behavior have been exercised and evidence has been retained.

These levels are deliberately distinct. For example, a pattern can be semantically valid and package-tested while its real Databricks runtime certification is still `not_run`.

## Ownership boundary

Reusable metadata/runtime/recovery behavior belongs in this repository. The following remain outside the framework package:

- Terraform, workspaces, cloud networking, and storage credentials;
- organisation-specific Unity Catalog topology;
- OIDC/service-principal bootstrap;
- DEV/UAT/PROD environment naming and promotion policy;
- customer/domain fixtures and expected outcomes;
- workload-specific deployment resources.

The customer/company workload supplies runtime inputs and deployable workload resources. The optional infra repository supplies a reference platform baseline.

## Status rule

Humans may use this document to understand the model, but automation must read `project/capabilities.yml` rather than parse Markdown status tables.

A framework capability is not called cross-repository certified merely because package CI is green. The independent customer certification matrix is the authority for exact-SHA C0-C5 claims.
