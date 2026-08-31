# Enterprise Databricks Framework

A production-oriented, metadata-driven Databricks lakehouse framework for onboarding heterogeneous enterprise data sources without rewriting the platform for every table.

## Design goal

The framework turns a pipeline design contract into the appropriate Databricks implementation while keeping business transformations explicit. It supports current-state snapshots, watermark incrementals, raw append observation history, soft deletes, net/full CDC, Debezium/Kafka, Delta CDF, business events, snapshot-diff patterns, SCD1/SCD2, reconciliation, replay, repair, quarantine, schema evolution and immutable CI/CD promotion.

The core reasoning model is:

```text
data semantics
  -> capture / delivery
  -> cursor / ordering
  -> Bronze contract
  -> Silver contract
  -> fidelity / recovery
```

## Repository rule

This repository is intentionally a **modular monorepo**. Reusable framework code lives in `src/edp_framework`; source- or company-specific behavior is added through package extension points. Do not split the core into a separate repository until multiple independently released Databricks platforms genuinely need to consume it.

## Directory map

```text
enterprise-databrick-framework/
├── docs/                 Architecture, ADRs, onboarding, runbooks and repo map
├── config/               Desired-state metadata and data contracts (Git-owned)
├── src/edp_framework/    Reusable Python package and extension points
├── resources/            Lakeflow Jobs/Pipelines bundle resource definitions
├── sql/                  Runtime control, observability and governance SQL
├── tests/                Contract, metadata, recovery and reconciliation tests
├── fixtures/             Deterministic test data
├── platform/terraform/   Account/workspace/UC infrastructure boundary
├── scripts/              CI, deployment and operational wrappers
└── .github/workflows/    CI/CD entry points
```

For the fastest navigation, start with [`docs/REPOSITORY_MAP.md`](docs/REPOSITORY_MAP.md).

## Configuration vs runtime state

**Git is the desired-state source of truth.** Table keys, semantics, cursor, DQ, SCD and recovery strategy belong under `config/`.

**Unity Catalog Delta tables store runtime state.** Runs, observed source positions, reconciliation outcomes, repair requests and incidents belong in `platform_control`.

A production operator must not be able to silently change a table from `SCD2` to `snapshot_replace` by editing a control table.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

edp validate config/tables
pytest
ruff check .
mypy src/edp_framework
```

When Databricks credentials and targets are configured:

```bash
databricks bundle validate -t dev
databricks bundle deploy -t dev
```

## Built-in pattern catalogue

The framework ships with the 14 semantic patterns represented in the companion data-engineering cheatsheet. See `config/contracts/pattern-catalog.yml` and `docs/architecture/pattern-routing.md`.

## Extension model

New source technologies or pipeline patterns should normally be delivered as packages, not as edits scattered across the framework. A package can register new pattern providers using the Python entry-point group `edp.patterns`.

```toml
[project.entry-points."edp.patterns"]
company_sap = "company_sap_patterns.provider:provider"
```

The package can then provide metadata validation, routing hints, runtime factories and tests while leaving the core stable.

## Status

Phase 0 foundation is implemented: project blueprint, architecture boundaries, metadata schema, built-in semantic catalogue, plugin contract, runtime control DDL, validation CLI and CI skeleton. Databricks workspace resources and real vertical slices are intentionally subsequent phases; see `docs/PROJECT_BLUEPRINT.md`.
