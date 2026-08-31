# ADR-004: Extension Packages

Status: Accepted

## Decision

New source technologies and genuinely new patterns integrate through package boundaries and Python entry points (`edp.patterns`). Core changes are required only when the extension contract itself is insufficient.

## Consequence

The framework stays stable while organisations can add SAP, mainframe, vendor API or proprietary CDC logic without a permanent fork.
