# Pattern Extension Package Template

Use this only when a source cannot be expressed by an existing P01-P14 semantic pattern, or when a reusable provider-specific implementation truly needs its own lifecycle.

Copy this package **inside the company platform repository by default**. Move it to a separate repository only when multiple independently released platforms consume the same package.

The extension registers through the `edp.patterns` Python entry-point group. A provider must ship all three pieces together:

```text
PatternDefinition   -> what the new semantic pattern means
validate()          -> what metadata makes that pattern safe
build_runtime()     -> the executable Databricks graph/implementation
```

Core discovers the package without source-specific `if vendor == ...` branches. The template runtime intentionally raises `NotImplementedError`; CI must not treat a metadata-only plugin as a working production pattern.
