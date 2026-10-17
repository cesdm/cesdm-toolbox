# Extend the schema

When a study needs classes or attributes the core does not have, add them in a **schema package of your own**. The core stays untouched, so your models remain compatible with future releases. Why this is done by augmentation rather than by subclasses or by editing the core is explained in [Schemas](../concepts/schemas.md#extending-without-forking); this page is the recipe.

A package has the same structure as the core and declares what it builds on:

```text
my_extension/
├── SCHEMA_MANIFEST.yaml      # extends: [../cesdm]
├── entities/
├── attributes/
├── relations/
└── augmentations.yaml
```

```python
model = build_model_from_yaml("schemas/my_extension")   # loads core + extension
```

**New class**

```yaml
name: Agent
parents: [SemanticEntity]
attributes:
  - id: agent_name
```

**New attribute**

```yaml
attributes:
  bidding_strategy:
    description: Market bidding strategy.
    value:
      type: string
      constraints:
        enum: [price_taker, strategic, cooperative]
```

**Add to existing classes** — without subclassing. Augmenting `EnergyAssetInstance` reaches every generator, storage, demand and transmission element:

```yaml
augmentations:
  EnergyAssetInstance:
    groups:
      agent:
        attributes: [{id: bidding_strategy}]
        relations: [{id: ownedByAgent}]
```

A complete example is `docs/examples/living-lab/schema/`. Its `augmentations.yaml` adds `ownedBy` to `DemandUnit`, `SolarGenerationUnit` and `StorageUnit`, which are classes in `schemas/cesdm`. `examples/example_schema_extension.py` is a smaller sketch of the same mechanism.

Two analysis packages ship with the toolbox and use the same mechanism. `schemas/cesdm` is the dispatch base. Power-flow fields and classes are in `schemas/cesdm_power_flow`; machine models and controllers are in `schemas/cesdm_dynamic`. Each extends the base, so one path loads both layers:

```python
build_model_from_yaml("schemas/cesdm_power_flow")
build_model_from_yaml(["schemas/cesdm_power_flow", "schemas/cesdm_dynamic"])
```

## For exchange

A model that uses an extension can only be read by groups that load the same extension. Share the package together with the model, or propose the addition for the core through an issue — that is how the core schema grows.
