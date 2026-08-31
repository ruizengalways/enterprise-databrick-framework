# Repository Strategy

## Decision

Use one Databricks platform repository containing a clean reusable Python package.

## Why not a second core repository now?

A separate core repository introduces package publishing, dependency pinning, coordinated version upgrades, compatibility testing and cross-repo release management before any second consumer exists. That cost does not increase reusability today.

The current `src/edp_framework` package already creates the extraction seam. When a second independently released Databricks platform needs it, move that package to its own repository and publish a versioned wheel without redesigning table metadata or imports.
