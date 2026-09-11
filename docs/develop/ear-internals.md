# EAR internals

This page is for contributors and adapter authors. Modellers can stay with [Entities and relationships](../understand/entities-and-relationships.md) and the [Python API](python-api.md).

CESDM stores every study as **entities**, **attributes**, and **relations**. The generic engine that applies those three operations is the Entity–Attribute–Relation ([EAR](../reference/glossary.md#ear)) layer. Energy concepts are not hard-coded in that engine; they come from loaded [schemas](../understand/schemas.md).

## Three operations

Every change to a model is one of:

1. **Create** an entity (`add_entity`)
2. **Describe** it (`add_attribute`)
3. **Connect** it (`add_relation`)

```python
model.add_entity(entity_class="GenerationUnit", entity_id="gen.ch.wind")
model.add_attribute(
    entity_id="gen.ch.wind",
    attribute_id="nominal_power_capacity",
    value=3500,
    unit="MW",
)
model.add_relation(
    entity_id="gen.ch.wind",
    relation_id="atNode",
    target_entity_id="bus.ch",
)
```

The [Python API](python-api.md) assigns the same slots on entity handles (`gen.nominal_power_capacity = …`). Both paths write the same store.

## Schemas, engine, and your model

Three layers work together:

| Layer | What it is | Your role |
|-------|------------|-----------|
| **Schemas** | Vocabulary and rules in YAML | Load CESDM core; [extend](schema-extensions.md) only when needed |
| **EAR engine** | Generic create / describe / connect | Validate assignments against the loaded schemas |
| **System model** | Concrete instances in a study | Create assets, regions, and profiles |

![CESDM Semantic Architecture](../illustrations/cesdm_semantic_architecture.svg)

**Schemas** answer: *what types may exist, and which attributes and relations may be used on each type?*  
The **system model** answers: *which instances exist, and what values and links do they have?*

When you call `add_entity(entity_class="GenerationUnit", …)`, the engine checks the loaded schemas. See [Validation](../use/validate-models.md).

## When to use the core operations

Use `add_entity` / `add_attribute` / `add_relation` for generic tooling, importers, exporters, and schema-independent processing. Day-to-day model building should use the [Python API](python-api.md).

The full `ear` package surface is in the [API reference](../reference/api.md).

## EAR beyond CESDM

CESDM is one application of EAR — the energy-system vocabulary — not the engine itself.

The EAR engine does not know about generators, buses or carriers. It only knows how to **create** entities, **describe** them with attributes, and **connect** them with relations, then check those assignments against whatever schemas you load. Any system that can be described that way can use the same engine: load a schema package for that domain, then use the same `add_entity` / `add_attribute` / `add_relation` operations.

Energy systems are the CESDM case. Other domains are possible whenever the objects, their properties and the links between them are the right grain — for example organisations, municipalities and households rather than electrical assets.

`examples/example_ear_generic_domain.py` shows that path. It loads `schemas/agentbased` (households, municipalities, energy communities) and never uses CESDM types or the CESDM proxy layer.
