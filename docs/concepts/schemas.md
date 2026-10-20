# Schemas

A schema says **what may exist** in a model: which classes, which attributes and relations each class may have, of which type, with which units and limits. It never says what exists in your study — no plant, no number. Those belong in the model you build.

Schemas are YAML files, separate from the Python engine. The [engine](engine.md) applies whatever schema it loads, so the vocabulary can grow without changing code, and every group checks against the same rules.

## What a schema defines

| Building block | Role | Example |
|---|---|---|
| **Class** | a type you can create objects of | `HydroGenerationUnit` |
| **Inheritance** | a genuine *is-a* | every `HydroGenerationUnit` is a `GenerationUnit` |
| **Attribute** | a named value slot: type, unit, limits, whether required | `nominal_power_capacity`, decimal, MW, ≥ 0 |
| **Relation** | a named link slot: allowed target classes, whether required | `drawsFromHydroReservoir` → `HydroReservoir` |
| **Attribute group** | a label sorting the slots by use | `dispatch`, `topology`, `power_flow`, `dynamics` |

Attributes and relations are defined once, in a registry (`attributes/attributes.yaml`, `relations/relations.yaml`), and then **used** by classes. `nominal_power_capacity` is defined in one place and means the same on every class that uses it.

## One plant, three forms

The same hydro unit as a schema definition, as Python calls and as an exported file.

**Schema** — the class and the slots it uses (`cesdm/schemas/base/entities/…/HydroGenerationUnit.yaml`, shortened):

```yaml
name: HydroGenerationUnit
parents:
- GenerationUnit                 # inherits capacity, region, technology, …
attributes:
- id: turbine_efficiency
  required: false
  belongsToGroup: [dispatch]
relations:
- id: drawsFromHydroReservoir
  required: false
  target: HydroReservoir
```

**Model** — one object, its values and links:

```python
model.add_entity("HydroGenerationUnit", "gen.CH_HYD_RES")
model.add_attribute("gen.CH_HYD_RES", "nominal_power_capacity", 8500, unit="MW")
model.add_attribute("gen.CH_HYD_RES", "turbine_efficiency", 0.9)
model.add_relation("gen.CH_HYD_RES", "belongsToGeographicalRegion", "region.country.CH")
model.add_relation("gen.CH_HYD_RES", "drawsFromHydroReservoir", "storage.CH_RES")
```

**File** — what `model.export_yaml("model.yaml")` writes. Attributes and relations are lists of `{id, value}`. The header lists every schema package the model loaded, `cesdm` first, and `schema_version` is the package that was opened. The name comes from the manifest (`cesdm`, `cesdm-powerflow`, `cesdm-dynamics`), not from the folder. This plant was written from `cesdm/schemas/base` alone. A model opened on `cesdm/schemas/powerflow` lists `cesdm` and `cesdm-powerflow`.

```yaml
_cesdm_meta:
  format: cesdm-yaml
  schema_packages:
  - name: cesdm
    version: "1.0.0"
  schema_version: "1.0.0"
HydroGenerationUnit:
  gen.CH_HYD_RES:
    attributes:
    - id: nominal_power_capacity
      value: 8500.0
      unit: MW
    - id: turbine_efficiency
      value: 0.9
      unit: fraction
    relations:
    - id: belongsToGeographicalRegion
      target_entity_ids:
      - region.country.CH
    - id: drawsFromHydroReservoir
      target_entity_ids:
      - storage.CH_RES
```

The file is a model, not a schema. `import_yaml` reads it back. An `ear` model and a `CesdmModel` use this same flat file.

## Attribute groups

A generator carries values for several uses: its capacity and cost for dispatch, its node for topology, its setpoints for power flow, its machine model for dynamics. Attribute groups sort these slots in the schema (`belongsToGroup`) **without splitting the object**. Every value still belongs to exactly one entity and is stored once.

| Group | Holds |
|---|---|
| `dispatch` | capacities, efficiencies, costs, storage and inflow |
| `topology` | where the object sits: `atNode`, `fromNode`, `toNode`, its region |
| `technical` | technology-specific properties |
| `capacity_expansion` | commissioning, retirement, investment |
| `spatial` | coordinates and geography |
| `power_flow` | bus types, setpoints, reactive limits — from `cesdm/schemas/powerflow` |
| `dynamics` | machine and controller parameters — from `cesdm/schemas/dynamics` |

The groups appear in the exported file (above), in the [schema diagrams](../reference/schema-diagrams/index.md), and in Python as namespaces: `gen.dispatch.nominal_power_capacity`, `gen.power_flow.active_power_setpoint` ([proxy API](../guides/proxy-api.md)).

## Extending without forking

A study often needs something the core does not have: power-flow setpoints, controller parameters, bidding strategies, failure rates. There are three ways to add them. Only one keeps models exchangeable.

| | Effect |
|---|---|
| Edit the core schema | Your copy and everyone else's diverge. Models no longer validate elsewhere. |
| Create subclasses — `MarketGenerationUnit`, `ReliabilityGenerationUnit` | One plant needs a different class for every study, and studies can no longer share it. |
| **Augment** in a package of your own | The core stays untouched. A `GenerationUnit` stays a `GenerationUnit`; your package attaches extra slots to it when it is loaded. |

An extension package has the same layout as the core and names what it builds on:

```text
my_extension/
├── SCHEMA_MANIFEST.yaml      # version, extends: [../cesdm]
├── entities/                 # new classes, if any
├── attributes/               # new attribute definitions
├── relations/                # new relation definitions
└── augmentations.yaml        # which existing classes use them
```

The power-flow package is exactly this. Its `augmentations.yaml` attaches setpoints to the existing base classes:

```yaml
augmentations:
  GenerationUnit:
    attributes:
      - id: active_power_setpoint
        required: false
        belongsToGroup: [power_flow]
      - id: voltage_magnitude_setpoint
        required: false
        belongsToGroup: [power_flow]
```

Because `HydroGenerationUnit` inherits from `GenerationUnit`, the reservoir turbine of the tutorial gets these slots too — no new class, no change to `cesdm/schemas/base`. Loading the package loads what it extends:

```python
build_model_from_yaml("cesdm/schemas/powerflow")                              # base + power flow
build_model_from_yaml(["cesdm/schemas/powerflow", "cesdm/schemas/dynamics"])   # base + both
```

Packages are combined into one schema **before** any object is created. Conflicts are reported then, not halfway through building a model:

```text
ValueError: Schema validation failed:
- [augmentation] Target class 'GenerationUnitt' does not exist (did you mean: GenerationUnit, WindGenerationUnit, SolarGenerationUnit)
```

The step-by-step recipe is in [Extend the schema](../guides/extend.md).

### What this means for exchange

A model can only be read in full by a group that loads the same packages. If Group A sends a model with power-flow setpoints and Group C loads only `cesdm/schemas/base`, the setpoints have no slot on C's side. The import skips them and lists them under `unknowns` in its result — check that list when you receive a file:

```python
result = model.import_yaml("group_a.yaml")
result["unknowns"]     # [('GenerationUnit', 'g1', 'unknown attribute: active_power_setpoint')]
``` Share the extension together with the model, and record which packages and versions you loaded (see [contribute and cite](../project/contribute.md#cite)).

### How the core grows

Extensions are also how CESDM evolves. A package that several groups use is a candidate for the core. The path from project-specific to shared:

1. A study adds what it needs in its own package — no waiting for a release.
2. Other groups load the same package; models stay exchangeable among them.
3. When the addition has proven itself, it is proposed for the core through an issue, and enters through the normal [versioning](../project/roadmap.md#versioning) rules.

Neither the core nor anyone's models break along the way. `cesdm/schemas/powerflow` and `cesdm/schemas/dynamics` are themselves experimental packages on this path.

## Where to look things up

- every class, attribute and relation, searchable: the [schema reference](../reference/schema-reference.html)
- the classes as UML diagrams, with inheritance and groups: the [schema diagrams](../reference/schema-diagrams/index.md)
- the version and the stability of each part: `cesdm/schemas/base/SCHEMA_MANIFEST.yaml` and [roadmap and releases](../project/roadmap.md)
