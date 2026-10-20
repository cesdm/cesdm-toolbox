# Entity, attribute, relation

Every CESDM model is built from three parts: **entities**, their **attributes** and the **relations** between them — EAR for short. The [tutorial](../tutorial/index.md) uses them on the Swiss system. This page names them.

## The three parts

```text
gen.CH_HYD_RES                    HydroGenerationUnit            entity
├── nominal_power_capacity        = 8500 MW                      attribute
├── generator_technology_type     = reservoir_hydro              attribute
├── belongsToGeographicalRegion   → region.country.CH            relation
└── drawsFromHydroReservoir     → storage.CH_RES               relation
```

| | Is | Example | Call |
|---|---|---|---|
| **Entity** | one object, with a class and an id | the turbine `gen.CH_HYD_RES`, a `HydroGenerationUnit` | `add_entity` |
| **Attribute** | a value on that object, with a unit | `nominal_power_capacity = 8500 MW` | `add_attribute` |
| **Relation** | a link from that object to another object | `drawsFromHydroReservoir → storage.CH_RES` | `add_relation` |

A rule of thumb for adapter authors: an entity is a component of your model — a plant, a basin, a demand, a line, a region. Everything that describes it is an attribute: numbers with their unit, but also a name or a category. Everything that points at another component is a relation.

### Entity

An entity is one object, with a class and an id.

| Class | Instance | In the tutorial |
|---|---|---|
| `HydroGenerationUnit` | `gen.CH_HYD_RES` | Reservoir turbine, 8.5 GW |
| `HydroReservoir` | `storage.CH_RES` | Its basin, 8.8 TWh |
| `DemandUnit` | `demand.CH` | National electricity demand |
| `GeographicalRegion` | `region.country.CH` | Switzerland, from the regions library |
| `CarrierDomain` | `domain.electricity` | The electricity network |

```python
model.add_entity("HydroGenerationUnit", "gen.CH_HYD_RES")
```

### Attribute

An attribute is a value on that object. The schema names the attribute and the allowed unit. The model supplies the number.

```python
model.add_attribute(
    "gen.CH_HYD_RES",
    "nominal_power_capacity",
    8500,
    unit="MW",
)
```

A value the loaded schema does not allow for that class — an unknown attribute, a unit that is not permitted, text where a number belongs — is refused when it is written.

### Provenance

Every attribute can record where its value came from, the same way it records a unit:

```python
model.add_attribute("gen.CH_NUC", "nominal_power_capacity", 3000, unit="MW",
                    provenance_ref="group-a")
```

Read it back with `get_attr_value_unit_prov(entity, "nominal_power_capacity")` from `ear`, which returns value, unit and source:

```python
from ear import get_attr_value_unit_prov

gen = model.get_entities("GenerationUnit")["gen.CH_NUC"]
get_attr_value_unit_prov(gen, "nominal_power_capacity")    # (3000.0, 'MW', 'group-a')
```

When models from several groups meet — compared, merged or passed on — every number still says where it came from. YAML and Frictionless keep that source next to the value; see [Files and time series](files-and-time-series.md).

### Relation

A relation points at another object. The schema names the link and the classes it may point at. The model chooses the target.

```python
model.add_relation("gen.CH_HYD_RES", "belongsToGeographicalRegion", "region.country.CH")
model.add_relation("gen.CH_HYD_RES", "drawsFromHydroReservoir", "storage.CH_RES")
```

`8500 MW` describes this turbine. `storage.CH_RES` is a different object. A capacity cannot point at a basin, and writing the basin's name into a text field does not make the link. Because the link is a relation, `validate()` can check that `storage.CH_RES` exists and is a `HydroReservoir`.

## Classes and instances

| | Example | What it is | Who creates it |
|---|---|---|---|
| **Class** | `HydroGenerationUnit` | The type | The schema |
| **Instance** | `gen.CH_HYD_RES` | One plant in this study | You |

You create instances of classes that already exist. A second reservoir is another instance, not a new class. Classes inherit from each other: every `HydroGenerationUnit` is a `GenerationUnit`, so it has a capacity and a region like any generator, plus the hydro-specific links. The [schema diagrams](../reference/schema-diagrams/index.md) show the inheritance.

The schema defines the slots: which attributes and relations a class may have, with which type, unit and target. Your model fills those slots. It does not invent a new slot for one plant.

| | Where | Question |
|---|---|---|
| **Define** | Schema | Which properties may `HydroGenerationUnit` have? |
| **Assign** | Your model | What are the capacity and the basin of **this** plant? |

**The schema is the contract.** The system model is the set of instances, values and links.

## How many entities is one plant?

An entity is not always one physical device. The question is what the other objects in the model need to point at.

- A **battery** is one entity, a `StorageUnit`: it stores energy and converts it, and nothing else needs to refer to its parts.
- A **reservoir plant** is two: the turbine `gen.CH_HYD_RES` (`HydroGenerationUnit`, 8.5 GW) draws from the basin `storage.CH_RES` (`HydroReservoir`, 8.8 TWh and the inflow). Pumps, a second turbine or a cascade can then point at the same basin.

Group A in the tutorial keeps the basin in its own `storage.csv`, Group C writes it inside the plant. Both adapters produce the same two entities — which is why the two groups can be compared at all. Part 2 then puts a setpoint and a synchronous machine on that same turbine.

## Plants and technologies

Some values belong to one plant: its capacity, its node, its region. Others are shared by every plant of a kind: the efficiency of a new CCGT, its variable cost. CESDM can keep the shared values in a **library** entry and let the plant point at it:

```python
from cesdm.default_library import GeneratorTypes

model.add_entity("GenerationUnit", "gen.CH_CCGT")
model.add_attribute("gen.CH_CCGT", "nominal_power_capacity", 500, unit="MW")
model.add_relation("gen.CH_CCGT", "hasTechnology", GeneratorTypes.GENERATION_THERMAL_GAS_CCGT_NEW)

model.get_effective_attribute_value("gen.CH_CCGT", "energy_conversion_efficiency")   # 0.6, from the library
```

A value set on the plant overrides the library value. Pointing at a library entry only makes sense when the groups agree what that entry means. The four groups in the tutorial have not agreed that, so each plant carries its own category (`generator_technology_type`), efficiency and cost. See [libraries](classes-and-libraries.md#libraries).

## The same three calls

A region, a line or a heat demand is the same sequence:

1. **Create** the object — `add_entity`
2. **Set** its values — `add_attribute`
3. **Link** it — `add_relation`

These are all an adapter needs to write a model; reading it back uses `get_entities`, `get_attr_value` and `get_relation` ([API](../reference/api.md#the-calls-you-need-for-an-adapter)). For your own scripts there is a shorter, attribute-style way to write the same calls — `gen.nominal_power_capacity = (8500, "MW")` — described in [the proxy API](../guides/proxy-api.md). Both write the same entity.

## A schema that is not energy

The three calls do not mention a generator. The classes come from the schema that is loaded. CESDM loads `cesdm/schemas/base`. A schema that does not extend it is another domain, and the same engine checks it. The [bookshelf](../use-cases/bookshelf.md) is that case: an author, a book, and `writtenBy`.

How a model is written down is [Files and time series](files-and-time-series.md). Where the energy classes come from is the next page: [The EAR engine and CESDM](engine.md).
