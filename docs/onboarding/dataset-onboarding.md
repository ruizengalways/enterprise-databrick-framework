# Dataset Onboarding

1. Classify payload semantics.
2. Identify capture/delivery mechanism.
3. Define cursor and authoritative source ordering.
4. Confirm stable business key or explicitly choose a no-key-safe pattern.
5. Define source-version/event/delivery identity.
6. Select Bronze contract.
7. Select Silver contract.
8. Define physical/logical delete coverage.
9. Define bootstrap handoff.
10. Define DQ and quarantine behavior.
11. Define reconciliation with a stable cutoff.
12. Define history/retention and recovery window.
13. Define repair scopes.
14. Add deterministic fixtures/tests.
15. Run `edp validate` before deployment.

If the semantic pattern is new, implement it as an extension package first. Do not add source-specific branches throughout core.
