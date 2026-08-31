# Repair Runbook

Repairs are requested through `platform_control.repair_request` and executed by a controlled job.

Required flow:

```text
identify trustworthy boundary
-> create scoped repair request
-> validate requested range/key against retention
-> approve if policy requires
-> replay/rebuild through normal production code
-> run reconciliation
-> publish only on acceptable result
-> record repair outcome and incident link
```

Never fix a downstream Gold table with an unrelated manual UPDATE when the correct fix is to regenerate from trusted upstream history.
