# Repository Map — Where to Change What

This document is the shortest route into the repository. If a contributor cannot decide where a change belongs from this page, the repository boundary needs improvement.

| I need to... | Start here | Rule |
|---|---|---|
| Onboard a source/table using an existing pattern | `config/tables/` | Configuration first; do not fork framework code. |
| Describe source ownership/connection conventions | `config/sources/` | Keep credentials outside Git. |
| Understand the P01-P14 semantic catalogue | `config/contracts/pattern-catalog.yml` + `docs/architecture/pattern-routing.md` | Classify semantics before choosing technology. |
| Add a genuinely new semantic/vendor pattern | `templates/pattern-extension/` | Extend through a package/entry point that ships definition + validation + executable runtime; do not add scattered `if vendor == ...`. |
| Change reusable metadata validation | `src/edp_framework/metadata/` | Changes require unit tests and backward-compatibility review. |
| Change pattern registration/routing | `src/edp_framework/patterns/` | Built-ins remain stable; company-specific patterns belong in extension packages. |
| Change runtime operational-control tables | `src/edp_framework/operations/` | Runtime state is not desired-state configuration. |
| Add a Databricks Job/Pipeline resource | `resources/` | Workload resources are Bundle-owned. |
| Change account/workspace/Unity Catalog foundation | `platform/terraform/` | Stable platform infrastructure is Terraform-owned. |
| Change CI validation | `.github/workflows/validate.yml` | PR validation never deploys PROD. |
| Promote an immutable release | `.github/workflows/promote.yml` | Deploy the requested Git SHA, not whatever `main` currently contains. |
| Diagnose/repair bad data | `docs/runbooks/` + `platform_control` runtime records | Repair the highest trustworthy layer and regenerate derived layers normally. |
| Understand what is truly implemented | `docs/CAPABILITY_MATRIX.md` | Do not infer runtime readiness from directory names. |
| Understand the full platform contract | `docs/PROJECT_BLUEPRINT.md` | Canonical architecture source of truth. |

## Repository ownership mental model

```text
Git desired state
├── config/                  dataset contracts and behavior
├── src/edp_framework/       reusable product code
├── resources/               Databricks workload definitions
├── platform/terraform/      stable platform infrastructure
└── .github/                 delivery policy

Databricks runtime state
└── <env>.platform_control   runs, positions, DQ, reconciliation, repairs, incidents
```

## Copy-to-a-new-company rule

Clone the repository as a whole. Change environment/company configuration and add source-specific extension packages only where a source contract genuinely needs behavior not represented by the built-in catalogue. Do not copy individual notebooks out of the framework; doing so destroys upgradeability, tests, and recovery semantics.
