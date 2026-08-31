# Enterprise Databricks Framework

An installable, production-oriented Python framework for metadata-driven Databricks data engineering.

This repository is intentionally **package-only**. It owns reusable pipeline semantics and runtime behavior; it does not own a company's Databricks workspaces, Unity Catalog topology, Terraform state, GitHub OIDC identities, Bundle environment targets or DEV/UAT/PROD platform deployment.

## Ecosystem

This repository is one part of a deliberately separated reference ecosystem:

- [`data-engineering-cheetsheet`](https://github.com/ruizengalways/data-engineering-cheetsheet) — technology-neutral semantic/design source of truth for P01-P14.
- **`enterprise-databrick-framework`** — reusable package (this repo).
- [`enterprise-databrick-customer`](https://github.com/ruizengalways/enterprise-databrick-customer) — reference consuming workload, deterministic learning data and exact-SHA certification evidence.
- [`enterprise-databrick-infra`](https://github.com/ruizengalways/enterprise-databrick-infra) — optional platform/IaC baseline.

For a new conversation or a returning engineer, start with [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md). The customer repository contains the cross-repository certification lock and coverage matrix.

## What you take to a new company

If the company already has Databricks infrastructure, you only need this package plus the company's own workload repository:

```text
company-data-repo
├── metadata / dataset contracts
├── source adapters / domain transforms
├── Databricks Jobs or Lakeflow Pipelines
└── dependency: enterprise-databricks-framework

existing company platform
├── workspaces
├── catalogs / schemas
├── identities / secrets
└── CI/CD deployment standards
```

No Terraform from this repository is required because there is no Terraform in this repository.

## Package responsibilities

The framework provides reusable contracts and runtime components for:

- full snapshots and snapshot history
- watermark incrementals and lookback
- raw append observation history
- soft-delete current-state materialisation
- net/full CDC and Debezium-style change feeds
- event streams
- SCD1 / SCD2
- bootstrap/handoff contracts
- identity, source ordering and idempotency contracts
- schema evolution policy
- DQ/quarantine semantics
- reconciliation and recovery contracts
- runtime control tables and release evidence
- extension packages via `edp.patterns`

The mental model is:

```text
data semantics
  -> capture / delivery
  -> cursor / authoritative ordering
  -> identity / idempotency
  -> Bronze contract
  -> Silver contract
  -> delete / fidelity / retention
  -> reconciliation / recovery
```

## Repository map

```text
enterprise-databrick-framework/
├── src/edp_framework/     reusable installable package
├── tests/                 package/contract/recovery tests
├── examples/              example metadata contracts, never environment config
├── templates/             extension-package template
├── docs/                  framework architecture and runbooks
├── sql/                   reusable runtime-control documentation/assets
├── scripts/ci/            package CI helpers
├── pyproject.toml
└── .github/workflows/     package validation/build only
```

Explicitly absent:

```text
terraform/
platform/
databricks.yml
resources/
config/environments/
DEV/UAT/PROD deployment workflows
```

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

edp validate examples/table_specs
pytest
ruff check .
mypy src/edp_framework
python -m pip wheel . --no-deps --wheel-dir dist
```

In a consuming project, pin the framework like any other internal library: a released wheel/version or exact SHA-derived artifact is preferred over copying framework source into every project.

## Certification

Package CI proves package-level behavior only. It does **not** prove real Databricks runtime behavior for every semantic pattern.

`enterprise-databrick-customer` is the independent reference consumer used to certify exact framework SHAs against deterministic source data and expected outcomes. Its certification model deliberately separates local contract/package evidence from real Databricks runtime and recovery evidence.

Never describe a pattern/capability as runtime-certified unless the customer certification matrix has corresponding evidence for the exact framework SHA.

## Extension model

A source technology that fits an existing semantic pattern should normally add only a source adapter/provider package. A genuinely new semantic pattern can register a provider through the Python entry-point group `edp.patterns`.

```toml
[project.entry-points."edp.patterns"]
company_sap = "company_sap_patterns.provider:provider"
```

Extensions own their semantic declaration, metadata validation, runtime construction and tests. Core should not become a vendor switch statement.

## Infrastructure boundary

The framework may require capabilities such as a writable catalog/schema or a runtime service principal, but it accepts them as **runtime/environment inputs**. It never provisions them.

See `docs/INTEGRATION_WITH_PLATFORM.md` and the companion infra repository for an optional reusable platform baseline.
