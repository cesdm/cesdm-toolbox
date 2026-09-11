# Schemas

The [first model](../get-started/first-model.md) loaded `schemas/cesdm`. That folder is the **allowed list**: which object types exist and which facts and connections they may have. Your study only fills those fields.

The current CESDM core schema version is **1.0.0**, declared in `schemas/cesdm/SCHEMA_MANIFEST.yaml`. Exported models record that version. What changed: [release log](../community/changelog.md). Which families are stable or experimental: [Schema governance](../develop/governance.md) and the [roadmap](../community/roadmap.md).

Lookup: [Schema reference (HTML)](../reference/schema-reference.html).

!!! quote "Vocabulary versus your study"
    **Schemas** list the types and fields.  
    **Your model** creates the concrete plants, buses and links.

## What a schema file defines

| In the schema | In your first model |
|---------------|---------------------|
| Type `ElectricalBus` may have `nominal_voltage` | `bus.demo` is 380 kV |
| Type `GenerationUnit` may link `atNode` to a bus | the wind farm sits on `bus.demo` |
| `HydroGenerationUnit` is a kind of `GenerationUnit` | the turbines reuse generator fields plus reservoir links |

Nothing in a schema is a concrete plant. If you set a fact or connection the loaded list does not allow, [validation](../use/validate-models.md) reports it.

```python
model = build_model_from_yaml("schemas/cesdm")
```

You normally **load** schemas. You do not edit them for a first study. To add types later, see [Schema extensions](../develop/schema-extensions.md).

Schemas live under `schemas/cesdm/`. The catalogue of types and fields is the [Schema reference](../reference/schema.md).

## Attribute groups

Large types carry facts for several study views — dispatch, network attachment, power flow — without splitting one plant into several objects. The schema may tag a field with `belongsToGroup`. That is organisation only; the data still sit on one object.

```yaml
attributes:
  - id: nominal_power_capacity
    belongsToGroup: dispatch

relations:
  - id: atNode
    belongsToGroup: topology
```

| Group | Purpose |
|-------|---------|
| `dispatch` | Operation and dispatch |
| `topology` | `atNode`, `fromNode`, `toNode` |
| `power_flow` | Power-flow parameters |
| `technical` | Technology-specific fields |
| `capacity_expansion` | Commission, retrofit, retirement |
| `spatial` | Geography |
| `dynamics` | Dynamic-simulation parameters |

In Python, groups can appear as nested names (`hydro.dispatch.nominal_power_capacity`). See the [Python API](../develop/python-api.md). How the engine applies schemas is in [EAR internals](../develop/ear-internals.md#schemas-engine-and-your-model).

## Next

[Profiles](profiles.md) · [Validation](../use/validate-models.md) · [Schema reference](../reference/schema.md)
