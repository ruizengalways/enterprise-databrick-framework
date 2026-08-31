# ADR-003: Git vs Runtime State

Status: Accepted

## Decision

Git configuration is desired state. Unity Catalog Delta control tables hold runtime state only.

## Consequence

Production behavior changes require code review and promotion. Operators can request repair/replay without mutating the platform definition.
