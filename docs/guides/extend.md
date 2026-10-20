# Extend the schema

Use this page when your study needs classes or attributes the core does not have. Add them in a **schema package of your own**. The core stays untouched, so your models remain compatible with future releases. Why this is done by augmentation rather than by subclasses or by editing the core is explained in [Schemas](../concepts/schemas.md#extending-without-forking); this page is the recipe.

The example below adds market agents that own and bid assets. A package has the same structure as the core and declares what it builds on:

```text
schemas/my_extension/
├── SCHEMA_MANIFEST.yaml
├── entities/Agent.yaml
├── attributes/attributes.yaml
├── relations/relations.yaml
└── augmentations.yaml
```

**Manifest** — what the package builds on:

```yaml
name: my-extension
version: "0.1.0"
description: Market agents that own and bid energy assets.
extends:
  - ../base
```

`name` is what an exported file records. It is not the folder name, so two packages can both use a folder called `base` without claiming the same identity. The core packages are `cesdm`, `cesdm-powerflow` and `cesdm-dynamics`.

**New class** (`entities/Agent.yaml`):

```yaml
name: Agent
parents: [SemanticEntity]
description: A market participant that owns and bids assets.
attributes:
  - id: agent_name
    required: true
```

**New attributes and relations** — every id a class uses is defined once:

```yaml
# attributes/attributes.yaml
attributes:
  agent_name:
    description: Display name of the agent.
    value: {type: string}
  bidding_strategy:
    description: Market bidding strategy.
    value:
      type: string
      constraints:
        enum: [price_taker, strategic, cooperative]
```

```yaml
# relations/relations.yaml
relations:
  ownedByAgent:
    description: The agent that owns and bids this asset.
    target: [Agent]
```

**Add to existing classes** — without subclassing. Augmenting `EnergyAssetInstance` reaches every generator, storage, demand and transmission element:

```yaml
# augmentations.yaml
augmentations:
  EnergyAssetInstance:
    groups:
      agent:
        attributes: [{id: bidding_strategy}]
        relations: [{id: ownedByAgent}]
```

**Use it** — one path loads the core and the extension:

```python
from cesdm_toolbox import build_model_from_yaml

model = build_model_from_yaml("schemas/my_extension")
model.add_entity("Agent", "agent.utility_a")
model.add_attribute("agent.utility_a", "agent_name", "Utility A")
model.add_entity("HydroGenerationUnit", "gen.CH_HYD_RES")
model.add_attribute("gen.CH_HYD_RES", "bidding_strategy", "strategic")
model.add_relation("gen.CH_HYD_RES", "ownedByAgent", "agent.utility_a")
model.validate()    # []
```

`examples/example_schema_extension.py` is a smaller sketch of the same mechanism.

Two analysis packages ship with the toolbox and use the same mechanism. `cesdm/schemas/base` is the dispatch base. Power-flow fields and classes are in `cesdm/schemas/powerflow`; machine models and controllers are in `cesdm/schemas/dynamics`. Each extends the base, so one path loads both layers:

```python
build_model_from_yaml("cesdm/schemas/powerflow")
build_model_from_yaml(["cesdm/schemas/powerflow", "cesdm/schemas/dynamics"])
```

## For exchange

A model that uses an extension can only be read by groups that load the same extension. Share the package together with the model, or propose the addition for the core through an issue — that is how the core schema grows.

An extension used in a full study is the [living-lab case](../use-cases/living-lab.md): `docs/examples/living-lab/schema/` adds households and a survey, and its `augmentations.yaml` attaches `ownedBy` to `DemandUnit`, `SolarGenerationUnit` and `StorageUnit` from `cesdm/schemas/base`.
