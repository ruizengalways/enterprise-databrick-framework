# ADR-009: Stable layer schemas are the default layout

Status: Accepted

## Decision

Default environment catalogs use a stable schema set:

```text
bronze
silver
gold
reference
quarantine
platform_control
```

Dataset/domain identity is encoded in table names (`bronze.crm_customer_observation`) rather than creating a new schema for every `domain x layer` combination.

## Why

The default reusable framework should onboard a new dataset/domain through metadata and code without requiring a Terraform change merely to create another schema. A `domain x layer` layout creates schema/RBAC explosion and couples normal data onboarding to infrastructure promotion.

## Trade-off

Some organisations need domain-level schema isolation. That remains a valid deployment profile. Such a company can provide a schema-layout extension/alternative Terraform composition under an ADR without changing pipeline semantics or metadata taxonomy.

## Consequence

Table metadata stores `schema.table`, and runtime resolution prefixes the environment catalog. The same Git commit therefore promotes cleanly from `edp_dev` to `edp_uat` to `edp_prod`.
