# Reconciliation Failure Runbook

A reconciliation failure is evidence of possible drift; do not automatically overwrite the target to make counts match.

1. Freeze publication for the affected dataset if severity is blocking.
2. Compare source cutoff/position with the target processed position.
3. Classify: missed range, delete drift, duplicate/redelivery, transformation bug, schema issue, partial write or bad baseline.
4. Identify the highest trustworthy layer.
5. Create a scoped repair request.
6. Re-run the normal transformation path.
7. Reconcile using the same stable cutoff.
8. Close the incident only after correctness and freshness are restored.
