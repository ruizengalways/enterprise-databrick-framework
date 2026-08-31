# Failed Deployment Runbook

1. Stop promotion; do not deploy a different `main` revision to compensate.
2. Record the failing Git SHA, target, workflow run and Databricks resource errors.
3. If deployment was atomic/no workload executed, fix forward on a new commit and re-run the normal release lifecycle.
4. If bad code executed and changed data, separate code rollback from data recovery.
5. Redeploy the last known-good immutable SHA when rollback is required.
6. Repair/replay affected datasets from the highest trustworthy layer.
7. Reconcile before reopening publication.
