# Desired Configuration vs Runtime State

Git owns intent; Delta owns observations.

## Git-owned examples

- business keys
- source/change semantics
- cursor definition
- source ordering
- Bronze/Silver contract
- SCD2 tracking rules
- delete policy
- DQ rules
- reconciliation policy
- recovery capabilities

## Runtime Delta examples

- last observed/committed source position
- run status
- reconciliation result
- DQ counts
- repair request/status
- incident lifecycle
- release/deployment history

No operational SQL UPDATE should silently redefine a pipeline's intended semantics.
