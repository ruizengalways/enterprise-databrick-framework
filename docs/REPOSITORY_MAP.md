# Repository Map

This repository is an installable reusable library, not a Databricks platform deployment repository. The enforceable machine layout is `project/layout.yml`.

## Top level

```text
.
├── src/edp_framework/          installable reusable Python package
├── tests/                      deterministic package tests
├── examples/                   metadata/package usage examples only
├── templates/                  extension-package starter templates
├── scripts/                    real package development/CI utilities
├── project/                    machine-readable capabilities + layout
└── docs/                       human-readable architecture/ADRs/runbooks
```

Directories are not used as a roadmap. If there is no executable SQL asset, recovery implementation, or extension namespace today, the repository does not keep an empty/reserved directory for it.

Customer fixtures, expected certification outputs, Terraform, workspace IDs, Bundle environment targets, and organisation credentials do not belong here.

## Python package map

```text
src/edp_framework/
├── metadata/                   contract models, loader, validation
├── patterns/                   P01-P14 definitions, registry, extension protocol
├── runtime/                    Lakeflow runtime registration + naming
├── quality/                    reusable DQ predicates and expectations
├── reconciliation/             cutoff-consistent comparison engine + audit output
├── operations/                 runtime control tables/release observations
├── databricks_tasks/           reusable task entrypoints over package operations
├── cli.py
└── __init__.py
```

A package directory must represent a real implemented capability. Empty future-facing namespaces are deliberately forbidden. Planned work belongs in `project/capabilities.yml` until code exists.

`runtime/quality.py` is retained only as a compatibility import shim; new code should import from `edp_framework.quality`.

The extension API is intentionally **not** an `extensions/` package. The executable extension contract lives in `patterns/contracts.py`, discovery lives in the pattern registry, and a consumer starter exists under `templates/pattern-extension/`.

## Where to change things

| Goal | Location |
|---|---|
| Change metadata schema/contracts | `src/edp_framework/metadata/` |
| Add/change semantic pattern definitions | `src/edp_framework/patterns/` |
| Change built-in Lakeflow runtime behavior | `src/edp_framework/runtime/` |
| Add reusable DQ behavior | `src/edp_framework/quality/` |
| Add cutoff-consistent reconciliation rules | `src/edp_framework/reconciliation/` |
| Add runtime control/audit behavior | `src/edp_framework/operations/` |
| Add deterministic package tests | matching area under `tests/` |
| Show a metadata contract | `examples/table_specs/` |
| Build a company/vendor extension | `templates/pattern-extension/` |
| Certify an exact framework SHA against independent customer data | **not here**; `enterprise-databrick-customer` |
| Provision Unity Catalog/workspaces/OIDC | **not here**; company platform or `enterprise-databrick-infra` |

## Reconciliation boundary

Reconciliation compares source and target representations that the consuming workload has already aligned to one explicit cutoff. The package must not query a moving source at time A and a target at time B and call the difference a data-quality failure.

The v2 engine supports row count, distinct-key count, source-key presence, reviewed numeric aggregates, source-position equality, SCD2 current-row uniqueness, and SCD2 no-overlap checks. Key-based rules may declare `options.keys` when the reconciliation comparison key is intentionally different from the dataset's business identity; P01 snapshot replacement is the reference example.

`hash`, `operation_count`, and `custom` remain declared metadata kinds but are not core-engine implementations. They fail explicitly if passed to the core evaluator. In particular, `operation_count` needs an application/audit relation and must not be guessed from an SCD2 target that no longer preserves source operation codes.

Executable reconciliation metadata is validated before runtime: aggregate rules require an expression, key-based rules require either business keys or explicit rule keys, and tolerance modes must be supported.

## Rule of thumb

If behavior should work unchanged in ten different Databricks estates when supplied with Spark/Lakeflow/runtime context, it belongs here. If it needs a specific workspace, cloud account, connection, customer fixture, environment name, or organisation approval workflow, it belongs in a consuming workload or platform repository.
