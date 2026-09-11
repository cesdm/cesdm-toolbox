# Entities and relationships

In [your first model](../get-started/first-model.md), you created a bus, a wind farm and demand. In everyday language, CESDM describes these using **objects, facts and connections**.

```text
wind farm  ── atNode ──► bus
demand     ── atNode ──► bus
bus        ── in ──────► Switzerland
```

The technical terms are:

| Intuitive term | CESDM term | Example |
|---|---|---|
| Object | **Entity** | a particular wind farm |
| Fact | **Attribute** | capacity = 500 MW |
| Connection | **Relationship** | wind farm `atNode` bus |

You can work with the intuitive terms first; the technical names become useful when reading schemas or developing extensions.

## Type versus a particular object

`GenerationUnit` is a **type**. `gen.demo.wind` is one particular wind farm in your study.

```python
wind = model.add_entity("GenerationUnit", "gen.demo.wind")
```

You do not create a new type for every plant. You create another object of a type CESDM already knows. The allowed types are defined by [schemas](schemas.md).

## Facts

Facts describe one object:

```python
wind.name = "Demo wind farm"
wind.nominal_power_capacity = (500, "MW")
```

## Connections

Connections link objects:

```python
wind.atNode = bus
wind.hasTechnology = GeneratorTypes.GENERATION_RENEWABLE_WIND_ONSHORE
```

If a fact or connection is not allowed by the loaded CESDM schema, [validation](../use/validate-models.md) can flag it.

## How the pieces fit together

```text
Object / Entity
   │
   ├── facts / attributes
   │     capacity = 500 MW
   │     name = "Demo wind"
   │
   └── connections / relationships
         atNode ──► bus.demo
         hasTechnology ──► onshore wind
```

Shared technology definitions come from [libraries](libraries.md). Hourly data are represented through [profiles](profiles.md). Electricity, gas and heat belong to [carrier domains](carrier-domains.md).

## Schema, semantics and ontology

CESDM is a **schema-driven, tool-independent semantic framework** for interoperable energy-system modelling. It is not usefully described as “an energy-system ontology.”

These three terms are easy to mix:

| Term | Question |
|---|---|
| **Schema** | What information is allowed or required? |
| **Semantics** | What does that information mean? |
| **Ontology** | What concepts exist and how are they related? |

```text
GenerationUnit
    │
    ├── nominal_power_capacity = 500 MW
    │
    └── atNode ──────────────► ElectricalBus
```

- **Schema** — a `GenerationUnit` may have `nominal_power_capacity` and `atNode`.
- **Semantics** — `nominal_power_capacity` means rated generation capacity; `atNode` means the unit is associated with a network node.
- **Ontology** — `GenerationUnit` and `ElectricalBus` are distinct energy-system concepts, and a defined relationship can connect them.

CESDM is **semantic** because the fields have agreed meaning across tools. It is **schema-driven** because the [schema](schemas.md) says what may appear and can be checked. The concept graph is ontology-like; that is the background, not the product name.

## Next

Continue with [Schemas](schemas.md). When you are ready to construct a study, go to [Build models](../use/build-models.md). Neighbouring standards and tools: [Related work](related-work.md). Schema version and stability: [Roadmap](../community/roadmap.md).
