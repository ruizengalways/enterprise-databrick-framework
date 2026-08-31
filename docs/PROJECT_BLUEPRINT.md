# Enterprise Databricks Framework — Project Blueprint

Status: Phase 1 platform foundation and Phase 2 delivery spine implemented in code; remote Databricks OIDC deployment proof pending

This document is the canonical architecture source of truth for the repository. Important platform decisions must be recorded here and, where material, in an ADR.

## 1. Project goal

Build a production-grade reusable Databricks lakehouse platform that can onboard heterogeneous source systems through explicit metadata contracts while supporting batch, incremental current-state extraction, snapshot history, CDC, event streams, SCD1/SCD2, full refresh, reconciliation, replay, repair, schema evolution, CI/CD, observability, governance and cost control.

The platform must be reusable in a new organisation without rewriting the framework. New source-specific behavior should be introduced through small packages or explicit domain code, not forks of core orchestration logic.

## 2. Non-goals

- Do not build one giant universal notebook.
- Do not auto-generate arbitrary business transformations from metadata.
- Do not hide source semantics behind a flat `load_type` flag.
- Do not treat Git rollback as data recovery.
- Do not treat Bronze as universally immutable; its semantic contract is explicit per pattern.
- Do not store desired configuration in mutable runtime control tables.
- Do not create one repository per source database.
- Do not prematurely split the reusable core into another repository.

## 3. Architecture principles

1. **Semantics before technology.** Classify payload semantics before capture mechanism.
2. **Configuration-driven where behavior is stable; explicit code where business logic differs.**
3. **Git desired state, Delta runtime state.**
4. **One authoritative management mechanism per resource.**
5. **Bronze has an explicit semantic contract.** It can be current replica, raw observations, snapshot history or event history.
6. **Source ordering is distinct from ingestion ordering.**
7. **Entity identity, source-version identity, event identity and delivery identity are distinct concepts.**
8. **Every production pipeline has a bootstrap contract, retry/idempotency contract, delete contract, retention contract, reconciliation contract and recovery contract.**
9. **Reconciliation is a first-class workload, not a post-incident script.**
10. **Repair regenerates derived data through normal production code from the highest trustworthy layer.**
11. **CI/CD and operational scheduling are separate concerns.**
12. **Immutable Git SHA promotion across shared DEV/UAT/PROD.**
13. **Production jobs run as service principals, not individual engineers.**
14. **Prefer Databricks-native managed capabilities where they reduce custom state machines.**
15. **Extensions are packages with narrow contracts, not edits scattered through core code.**

## 4. Environment topology

Recommended default for one region:

```text
Databricks Account
├── Workspace: EDP-DEV
│   ├── personal development
│   ├── PR CI
│   └── shared DEV
├── Workspace: EDP-UAT
└── Workspace: EDP-PROD

Unity Catalog
├── edp_dev
├── edp_ci
├── edp_uat
└── edp_prod
```

Workspace-catalog binding is required for production so PROD catalogs cannot be queried from DEV/UAT workspaces even if a principal accidentally receives object privileges.

For larger regulated organisations, separate metastores/accounts/regions may be justified; that is an environment-specific deployment decision rather than a framework requirement.

The Bundle target model deliberately distinguishes personal development from stable shared development:

```text
dev        -> developer-owned deployment in edp_dev
ci         -> ephemeral PR namespace in edp_ci
shared_dev -> CI/CD-owned stable release in edp_dev
uat        -> CI/CD-owned release in edp_uat
prod       -> CI/CD-owned release in edp_prod
```

## 5. Repository strategy

Use one modular monorepo initially:

```text
enterprise-databrick-framework
```

The reusable core is a normal Python package under `src/edp_framework`. It is independently testable and can later be extracted without redesigning imports or contracts.

Extract it into a separate repository/package only when at least two independently versioned Databricks platform implementations need the same core and coordinated releases become a burden.

## 6. Repository structure

```text
.
├── docs/                 architectural source of truth and runbooks
├── config/               Git-owned desired-state metadata/contracts
├── src/edp_framework/    reusable platform package
├── resources/            Declarative Automation Bundle job/pipeline resources
├── sql/                  control, observability and governance SQL
├── tests/                unit/contract/integration/recovery tests
├── fixtures/             deterministic test fixtures
├── platform/terraform/   account/workspace/UC infrastructure boundary
├── scripts/              CI/deploy/operations wrappers
└── .github/workflows/    CI/CD
```

Directory readability has priority over minimizing directory count. Names describe responsibility rather than tooling implementation details.

## 7. Metadata taxonomy

Every dataset contract answers these orthogonal questions:

```text
1. source data semantics
2. capture / delivery mechanism
3. change granularity
4. cursor / continuation position
5. authoritative source ordering
6. business/entity identity
7. source-version identity
8. event identity
9. delivery identity
10. Bronze semantic contract
11. Silver semantic contract
12. delete semantics
13. DQ behavior
14. reconciliation
15. schema evolution
16. recovery
17. SLA
```

The built-in semantic catalogue maps to P01-P14 in `config/contracts/pattern-catalog.yml`.

## 8. Built-in workload families

### Current-state family

- full snapshot -> current replica
- full snapshot -> snapshot history
- watermark -> current replica
- watermark + lookback -> current replica
- watermark + lookback -> raw append observations
- watermark + soft delete -> current replica
- watermark + lookback + soft delete -> raw append observations

### Change-feed family

- net changes -> current replica
- net changes -> append change history
- full/all changes -> event history
- full/all changes -> intentionally lossy current replica

Capture providers can include database-native CDC, Lakeflow Connect, Debezium, Delta CDF or a company-specific package.

### Business-event family

- Kafka/Event Hubs/domain event sources -> Event Bronze -> canonical events / projections

### Derived-change family

- complete snapshot N vs N-1 -> current materialisation
- complete snapshot N vs N-1 -> append derived changes

## 9. Bronze contracts

Bronze is semantic, not merely a folder name.

### CURRENT_REPLICA
One business key represents the latest known source state. Replay may require source reload or Delta history.

### RAW_APPEND
Preserves ingestion observations including intentional lookback rereads and retries. It is replayable ingestion history, not automatically full source change history.

### SNAPSHOT_HISTORY
Preserves complete periodic source snapshots with snapshot identity. Fidelity is bounded by snapshot interval.

### EVENT_HISTORY
Preserves distinct captured CDC/domain events. Redelivery of the same event must not be interpreted as a new business event.

## 10. Silver contracts

Supported framework contracts:

- `current`
- `current_soft_delete`
- `scd1`
- `scd2`
- `canonical_events`
- `snapshot_replace`
- `custom`

SCD2 is a target semantic, not an ingestion mode. SCD2 requires stable business identity and authoritative ordering. Business-effective time is distinct from database-change time.

## 11. Databricks-native execution strategy

Prefer Lakeflow Spark Declarative Pipelines for declarative streaming/incremental tables, AUTO CDC, expectations and event-log observability.

Prefer Lakeflow Jobs for schedules, task dependencies, retries, repair runs and operational orchestration.

Use custom Structured Streaming/foreachBatch only when native declarative primitives cannot satisfy a real requirement. The framework should not reimplement checkpoint state machines by default.

Declarative Automation Bundles use the direct deployment engine. Terraform owns long-lived platform infrastructure; Bundles own workload resources. The deprecated Terraform-backed Bundle engine is not part of the target architecture.

## 12. Bootstrap strategy

Every incremental/CDC dataset must define the initial baseline and handoff point.

Conceptual invariant:

```text
establish consistent baseline at P
-> durably commit baseline
-> consume changes after/around P using deterministic overlap rules
```

No pipeline is production-ready if it cannot explain how snapshot-to-incremental handoff avoids gaps and uncontrolled double application.

## 13. Incremental read windows

For bounded incremental reads:

```text
lower = previous committed position - optional lookback
upper = source high-watermark captured at run start
read deterministic range
commit target + reconciliation
only then commit source position = upper
```

Timestamp-only watermarks must account for ties. Prefer rowversion/sequence, composite `(timestamp, PK)`, continuation token or overlap + idempotent materialisation.

## 14. Delete completeness

Delete behavior is explicit metadata:

- source soft delete
- CDC delete
- snapshot absence
- periodic reconciliation/diff
- custom package
- none, only when deletion is not part of the target contract

A plain watermark current-state source does not magically expose physical deletes.

## 15. Quality model

Quality actions:

- WARN: publish but surface metric/incident according to threshold
- QUARANTINE: route offending rows to an explicit quarantine dataset and preserve lineage
- FAIL: block the affected publication/update

Quality rules are Git-owned. Runtime results are Delta-owned.

## 16. Reconciliation model

Reconciliation runs Source->Bronze, Bronze->Silver and optionally Silver->Gold depending on the contract.

Standard rule types:

- row count
- key count
- key presence
- aggregate/control totals
- hash/checksum
- source position/cursor
- CDC operation counts
- SCD2 current-row uniqueness
- SCD2 interval overlap

Streaming comparisons use an explicit cutoff/source position. Never compare two moving systems at unrelated wall-clock times and call the difference drift.

## 17. Runtime control model

`<environment_catalog>.platform_control` stores runtime state only.

Core tables:

- `pipeline_run`
- `table_run`
- `source_state`
- `reconciliation_run`
- `reconciliation_result`
- `quality_result`
- `repair_request`
- `repair_run`
- `schema_change_event`
- `incident_event`
- `release_history`

Desired pattern, keys, SCD strategy and rules remain in Git.

Release provenance is written only after a deployed release passes the control-plane smoke gate. A release record contains the exact full Git SHA, Bundle target, workflow run, deploy actor and repository metadata.

## 18. Recovery model

Failure classes are handled deliberately:

- transient platform/network -> retry
- source unavailable -> retry/alert/SLA state
- duplicate/redelivered event -> event/source-version idempotency
- out-of-order CDC -> authoritative sequence / AUTO CDC
- bad row -> quarantine
- incompatible schema -> contract failure
- bad watermark -> replay trusted Bronze/source range
- source/target drift -> reconciliation + targeted repair
- bad SCD2 -> rebuild affected key/window from trusted history
- checkpoint corruption -> selective reset/backfill or full refresh according to runbook
- bad code release -> previous Git SHA
- bad data -> replay/rebuild/Delta restore according to trust boundary
- CDC retention gap -> snapshot resync

Code rollback and data recovery are separate workflows.

## 19. Repair model

Repairs are auditable requests, not notebook edits.

Supported scopes:

- business key
- time window
- partition/range
- snapshot reload
- full rebuild
- checkpoint reset (exception path)

Normal flow:

```text
request -> validate -> approve when required -> execute -> reconcile -> publish -> close
```

Derived layers should be regenerated using normal production transformations.

## 20. Schema evolution

Default policy:

- add nullable -> allow
- add required -> fail
- drop -> fail
- rename -> fail; prefer expand/migrate/contract
- type widening -> review
- incompatible type -> fail
- unexpected semi-structured fields -> rescue where supported, but do not silently promote to trusted schemas

## 21. Governance and security

Unity Catalog is the governance plane. Production ownership is assigned to groups/service principals, not individual users.

Use:

- least privilege
- workspace-catalog bindings
- separate deployment/runtime service principals
- workload identity federation for CI/CD where available
- tags/classification
- row filters/column masks where required
- synthetic/masked test data in non-production where production data access is inappropriate

Shared environments use two distinct identities:

```text
GitHub deployer service principal
  -> GitHub OIDC
  -> validate/plan/deploy Bundle resources

Runtime service principal
  -> Bundle run_as
  -> execute workloads with only required Unity Catalog privileges
```

## 22. CI/CD and promotion

Use Declarative Automation Bundles for Databricks workload definitions and source artifacts.

Lifecycle:

```text
feature branch
-> local/unit/metadata validation
-> personal DEV
-> PR
-> isolated CI target/namespace
-> contract + integration + failure tests
-> merge
-> immutable Git SHA
-> shared DEV
-> UAT
-> approval
-> PROD
-> smoke/reconciliation
```

Never independently deploy "whatever main is now" to each environment.

Deployment evidence must include Git SHA, bundle target, deploy identity, workflow run, tests, release timestamp and result.

Current delivery resources include:

- PR validation and Terraform module validation
- optional remote PR Bundle integration when the `ci` GitHub Environment has OIDC configuration
- independent PR-close cleanup for orphan protection
- automatic shared DEV deployment from the exact merge SHA when DEV OIDC configuration exists
- manual immutable-SHA UAT/PROD promotion protected by GitHub Environments
- `release_gate` smoke test and release-history write

## 23. Resource ownership matrix

| Resource | Authoritative owner |
|---|---|
| Databricks account/workspace/metastore bootstrap | Terraform/platform automation |
| storage credentials/external locations | Terraform/platform automation |
| workspace-catalog binding | Terraform/platform automation |
| long-lived UC catalogs/base schemas | Terraform/platform automation |
| account groups/service principals | Terraform/identity automation |
| GitHub OIDC federation policies | Terraform/identity automation |
| Lakeflow Jobs | Declarative Automation Bundles |
| Lakeflow Pipelines | Declarative Automation Bundles |
| workload code/package | Git + Bundle artifact |
| table business transformations | explicit Python/SQL pipeline code |
| table desired metadata | `config/` in Git |
| runtime control state | Delta tables |
| native event/job telemetry | Databricks event/system tables |
| platform-specific reconciliation outcomes | Delta control tables |

No resource should be simultaneously managed by Terraform and Bundles without an explicit ADR.

Terraform state is split by blast radius/change cadence. Account/workspace bootstrap, identity/OIDC, Unity Catalog environment foundations and workspace bindings are independent roots/states. Workload resources are not placed in Terraform state.

## 24. Extension/package architecture

The framework exposes Python entry point group `edp.patterns`.

An extension package can add:

- a new pattern definition
- metadata validation
- connector/capture implementation hints
- runtime factory code
- package-specific tests and fixtures
- reconciliation hooks
- recovery hooks

Example package:

```text
company-sap-databricks-patterns/
├── pyproject.toml
└── src/company_sap_patterns/
    ├── provider.py
    ├── capture.py
    ├── reconciliation.py
    └── tests/
```

This prevents core from becoming a switch statement for every future vendor.

## 25. Observability

Use Databricks native telemetry first:

- Lakeflow pipeline event log
- `system.lakeflow.*`
- billing/system tables
- audit logs
- lineage

Add framework runtime tables only for enterprise semantics Databricks cannot infer, such as source-to-target correctness, repair lifecycle, publication approval and source positions.

## 26. Testing strategy

Required test layers:

1. metadata schema tests
2. pattern contract tests
3. unit tests for deterministic transformations
4. integration tests using deterministic fixtures
5. CDC ordering/redelivery tests
6. SCD2 interval tests
7. schema-change compatibility tests
8. reconciliation tests
9. recovery/replay tests
10. CI orphan cleanup tests
11. security/permission tests
12. failure-injection tests

Failure-injection catalogue includes duplicate CDC, out-of-order CDC, late rows, deletes, source gap, schema change, null key, partial failure, bad release, checkpoint reset and reconciliation mismatch.

The standard PR gate currently validates table metadata, Ruff, strict mypy, Python tests/coverage, Terraform formatting, Terraform provider initialization and Terraform module validation. Remote Databricks integration is a separate conditional gate until OIDC is configured.

## 27. Cost strategy

Use serverless/job compute where appropriate, workload tagging, system billing tables, budget alerts and workload isolation. Cost is treated as an observable platform SLO, not a one-time sizing exercise.

## 28. Onboarding model

A normal new dataset should require:

```text
config/source or connection registration
config/table metadata
explicit source/domain transform only if semantics require it
fixture/contract tests
```

A normal new source technology should first attempt to reuse an existing semantic pattern with a new capture adapter/package.

A genuinely new semantic pattern should be delivered as an extension package and registered through `edp.patterns`; core changes require an ADR only when the existing extension contract itself is insufficient.

## 29. Implementation roadmap

### Phase 0 — Architecture and contracts

Implemented:

- canonical blueprint
- repository skeleton
- P01-P14 pattern catalogue
- strict metadata model
- plugin registry contract requiring definition + validation + executable runtime builder
- example table contracts
- runtime control DDL
- validation CLI
- CI foundation
- repository navigation map for company adoption
- 5 heterogeneous reference dataset contracts
- metadata/pattern/control tests

### Phase 1 — Platform foundation

Implemented in reusable code:

- cloud-neutral Terraform module boundary
- isolated Unity Catalog environment/catalog module
- long-lived base schemas and least-privilege runtime grants
- separate workspace-binding module using `databricks_workspace_binding`
- GitHub OIDC service-principal federation module
- deployer/runtime identity separation
- DEV/CI/shared DEV/UAT/PROD Bundle target model
- separate Terraform state boundaries by platform concern

Still environment-specific and intentionally not hard-coded:

- AWS/Azure/GCP workspace/network/storage bootstrap
- real account/metastore/workspace IDs
- organisation groups and service-principal grants outside the reusable module contract

### Phase 2 — Thin delivery spine

Implemented in code:

- Bundle direct deployment engine
- isolated PR deployment namespace
- independent PR cleanup workflow
- immutable full-SHA promotion contract
- stable shared DEV deployment target
- UAT/PROD promotion workflow
- service-principal runtime identity
- release control-plane smoke job
- release provenance persisted to `platform_control.release_history`
- Terraform/Python static CI gates

Pending real environment proof:

- configure GitHub Environments and Databricks OIDC identities
- run PR deploy/smoke/destroy against Databricks
- merge a known SHA to shared DEV
- verify the same SHA is recorded in `edp_dev.platform_control.release_history`
- promote that exact SHA to UAT/PROD when real environments exist

### Phase 3 — Vertical slices

Implement deliberately heterogeneous datasets:

- full snapshot/current
- watermark+lookback+soft-delete raw observations
- Debezium full CDC -> SCD2
- domain-event streaming
- snapshot history -> SCD2

### Phase 4 — Operability

- reconciliation runner
- repair request executor
- source-state commits
- quarantine path
- failure-injection suite

### Phase 5 — Governance/observability/cost hardening

- system table dashboards
- audit/security tests
- classification/masking/row filtering examples
- cost attribution
- SLOs

## 30. Current implementation status

The repository now has a tested platform-foundation and delivery-spine implementation in addition to the Phase 0 metadata framework. The reusable Terraform modules validate against the pinned Databricks provider family, and the standard Python/metadata CI gate passes.

The project **does not yet claim that the remote Databricks deployment path has been proven**. GitHub Environment OIDC variables and actual Databricks workspaces/service principals are deployment-environment inputs; until they are configured, remote PR integration and shared-DEV deployment workflows intentionally skip rather than pretending deployment succeeded.

No business vertical slice has been implemented yet. That boundary is intentional: the platform delivery mechanism is established before broad ingestion code is added.

## 31. Next implementation step

First prove the delivery spine in a real Databricks CI/DEV environment:

```text
GitHub PR SHA
-> OIDC deployment identity
-> isolated CI Bundle deploy
-> release-gate smoke
-> Bundle destroy
-> merge exact SHA
-> shared DEV deploy
-> release_history contains that exact SHA
```

Then begin Phase 3 with the deliberately heterogeneous executable vertical slices. The first set should prove P01 full snapshot/current, P07 watermark+lookback+soft-delete raw observations, P10 Debezium full CDC -> SCD2, P12 domain events and P02 snapshot-history -> SCD2.

## 32. Architecture decision index

- ADR-001: repository boundary
- ADR-002: metadata taxonomy
- ADR-003: runtime-state boundary
- ADR-004: extension packages
- ADR-005: Databricks resource ownership
- ADR-006: recovery principle
- ADR-007: personal DEV vs shared DEV target
- ADR-008: Terraform state boundaries
