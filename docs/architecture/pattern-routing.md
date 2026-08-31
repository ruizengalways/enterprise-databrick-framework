# Pattern Routing

The router does not ask "batch or streaming?" first. It asks what the payload *means*.

```text
payload semantics
├── current state
│   ├── full snapshot
│   └── incremental current rows
├── change feed
│   ├── net changes
│   └── full/all changes
├── business events
└── derived snapshot changes
```

Capture technology is then selected independently: Lakeflow Connect, JDBC, files, API, Debezium/Kafka, Delta CDF or an extension package.

The pattern registry validates semantic compatibility. Runtime factories will be added in the vertical-slice phase so a new provider can implement an existing semantic pattern without changing its business contract.
