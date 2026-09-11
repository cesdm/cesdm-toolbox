# Adapter development

Use this page if you want to **connect CESDM to your own tool or to a tool that has no shipped converter**. Adapters translate between CESDM's shared representation and tool-specific model structures.

```text
Tool-specific model  ⇄  CESDM  ⇄  Tool-specific model
```

A good adapter should:

1. Make the mapping explicit in both directions.
2. Preserve semantic meaning (units, topology, carrier domains).
3. Report unsupported concepts clearly.
4. Avoid silently dropping information.

Existing converters and the portable export formats are documented in [Import and export](../use/import-export.md). For TYNDP 2024 and PyPSA `elec.nc`, start with [Convert TYNDP and PyPSA](../examples/import-tyndp-and-pypsa.md).
