# Classes and libraries

What can a CESDM model describe, and what can it reuse? The classes say what may exist. A library is a set of objects many models share. The [tutorial](../tutorial/index.md) uses both on the Swiss system.

## The classes

Schema 1.0.0 publishes 59 classes in three packages: `cesdm/schemas/base`, `cesdm/schemas/powerflow` and `cesdm/schemas/dynamics`. For a first model you need a handful. They fall into a few families, each drawn as one [schema diagram](../reference/schema-diagrams/index.md):

| Family | Examples | Diagram |
|---|---|---|
| Assets | `GenerationUnit`, `HydroGenerationUnit`, `StorageUnit`, `HydroReservoir`, `DemandUnit`, `ExternalSupply` | [Assets](../reference/schema-diagrams/assets.md) |
| Network and regions | `ElectricalBus`, `TransmissionLine`, `Transformer`, `HVDCLink`, `GeographicalRegion`, `CarrierDomain` | [Network](../reference/schema-diagrams/network.md) |
| Conversion | `HeatPumpUnit`, `ElectrolyserUnit`, `CHPUnit` — assets that link two carrier domains | [Conversion units](../reference/schema-diagrams/conversion.md) |
| Shared types | `GeneratorType`, `StorageType`, `Carrier`, `NaturalResource` | [Technologies](../reference/schema-diagrams/technologies.md) |
| Time series | `Profile`, `TimestampSeries`, `EnergySystemModel` | [System and time series](../reference/schema-diagrams/time-series.md) |
| Dynamics | machine models, AVRs, governors, stabilisers | [Dynamics](../reference/schema-diagrams/dynamics.md) |

An asset sits either in a **region** (`belongsToGeographicalRegion`, a zonal model, as in the tutorial) or at a **node** (`atNode`, a nodal model). Gas, heat and hydrogen are modelled the same way as electricity, each in its own carrier domain; see [carrier domains](../guides/carrier-domains.md).

How a model is written down, including hourly profiles, is [Files and time series](files-and-time-series.md).

## Libraries

A **library** is a CESDM model of shared, reusable objects: technologies, carriers, carrier domains, regions. Schemas and libraries do different jobs:

| Schema | Library |
|---|---|
| defines classes, attributes, relations, rules | contains objects of those classes, with values |
| says what *may* exist | provides objects *many models use* |
| `GeneratorType` is a class | `Generation.Thermal.Gas.CCGT.New` is one object, efficiency 0.6 |

```python
model.import_library("cesdm/library/default_library")    # technologies, carriers, domains
model.import_library("cesdm/library/regions_library")    # countries and NUTS regions
```

A library is not a special format: it is an ordinary CESDM model, validated like any other. That is why a project can write its own — a national technology catalogue, a manufacturer's equipment list — and import it next to the default one. An optional `cesdm/library/tyndp_library/` adds the TYNDP technology classes.

When groups have agreed that a code means one library entry, an adapter writes `hasTechnology` to that entry, and the plant takes its efficiency and cost from there unless it sets its own ([plants and technologies](ear.md#plants-and-technologies)). The four groups in the tutorial have not agreed that, so each plant carries `generator_technology_type` and its own efficiency and variable cost. Values specific to one plant — its capacity, its node, a retrofit efficiency — stay on the plant either way.

On export, `include_library="referenced"` (the default) writes only the library objects your model uses; `"none"` writes none and `"all"` writes every one that was imported.
