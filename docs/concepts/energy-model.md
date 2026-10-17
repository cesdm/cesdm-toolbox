# The energy data model

The previous pages describe the machinery: [entities, attributes and relations](ear.md), the [engine](engine.md), [schemas](schemas.md) and the [two checks](validation.md). This page is what CESDM fills them with for an energy system: the classes, the shared libraries, provenance, the files and the time series. The [tutorial](../tutorial/index.md) uses all of them on the Swiss system.

## The classes

Schema 1.0.0 publishes 81 classes in three packages: `schemas/cesdm`, `schemas/cesdm_power_flow` and `schemas/cesdm_dynamic`. For a first model you need a handful. They fall into a few families, each drawn as one [schema diagram](../reference/schema-diagrams/index.md):

| Family | Examples | Diagram |
|---|---|---|
| Assets | `GenerationUnit`, `HydroGenerationUnit`, `StorageUnit`, `HydraulicStorageUnit`, `DemandUnit`, `ExternalSupply` | [Assets](../reference/schema-diagrams/assets.md) |
| Network and regions | `ElectricalBus`, `TransmissionLine`, `Transformer`, `HVDCLink`, `GeographicalRegion`, `MarketZone`, `CarrierDomain` | [Network](../reference/schema-diagrams/network.md) |
| Conversion | `HeatPumpUnit`, `ElectrolyserUnit`, `CHPUnit` — assets that link two carrier domains | [Conversion units](../reference/schema-diagrams/conversion.md) |
| Shared types | `GeneratorType`, `StorageType`, `Carrier`, `NaturalResource` | [Technologies](../reference/schema-diagrams/technologies.md) |
| Time series | `Profile`, `TimestampSeries`, `EnergySystemModel` | [System and time series](../reference/schema-diagrams/time-series.md) |
| Dynamics | machine models, AVRs, governors, stabilisers | [Dynamics](../reference/schema-diagrams/dynamics.md) |
| Results | dispatch, power-flow and dynamic results, and the run records that produced them | [Results](../reference/schema-diagrams/results.md) |

An asset sits either in a **region** (`belongsToGeographicalRegion`, a zonal model, as in the tutorial) or at a **node** (`atNode`, a nodal model). Gas, heat and hydrogen are modelled the same way as electricity, each in its own carrier domain; see [carrier domains](../guides/carrier-domains.md).

## Libraries

A **library** is a CESDM model of shared, reusable objects: technologies, carriers, carrier domains, regions. Schemas and libraries do different jobs:

| Schema | Library |
|---|---|
| defines classes, attributes, relations, rules | contains objects of those classes, with values |
| says what *may* exist | provides objects *many models use* |
| `GeneratorType` is a class | `Generation.Thermal.Gas.CCGT.New` is one object, efficiency 0.6 |

```python
model.import_library("library/default_library")    # technologies, carriers, domains
model.import_library("library/regions_library")    # countries, NUTS regions, market zones
```

A library is not a special format: it is an ordinary CESDM model, validated like any other. That is why a project can write its own — a national technology catalogue, a manufacturer's equipment list — and import it next to the default one. An optional `library/tyndp_library/` adds the TYNDP technology classes.

When groups have agreed that a code means one library entry, an adapter writes `hasTechnology` to that entry, and the plant takes its efficiency and cost from there unless it sets its own ([plants and technologies](ear.md#plants-and-technologies)). The four groups in the tutorial have not agreed that, so each plant carries `generator_technology_type` and its own efficiency and variable cost. Values specific to one plant — its capacity, its node, a retrofit efficiency — stay on the plant either way.

On export, `include_library="referenced"` (the default) writes only the library objects your model uses; `"none"` writes none and `"all"` writes every one that was imported.

## Provenance

Every attribute can record where its value came from:

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

When models from several groups meet — compared, merged or passed on — every number still says where it came from.

## Files

| Format | Content | Best for |
|---|---|---|
| YAML | the whole model | exchange, review, version control |
| Frictionless | `datapackage.json` + one CSV per class | spreadsheets, data pipelines |
| HDF5 | the numbers of time series | large profiles, referenced from the YAML |

A YAML file is one way of writing a CESDM model down. `export_yaml(path)` writes the flat EAR file and `import_yaml(path)` reads it, for an `ear` model and for a `CesdmModel`. The header is `_cesdm_meta`. YAML keeps the unit that was written and the provenance of each value, including letters such as ü. A Frictionless package does the same: each attribute has a value column plus `__unit` and `__provenance_ref`, and every relation target is a row in `relations.csv`. The class table still shows the first target, so a foreign key has a single id to point at. The optional `parquet` extra adds `export_parquet` for profile numbers; the examples store those numbers in HDF5.

## Time series

Hourly data are not stored in the YAML. A `Profile` object says what a series means and where its numbers are; a `TimestampSeries` gives the time axis.

```python
ts = model.add_entity("TimestampSeries", "ts.hourly.2030")
model.add_attribute("ts.hourly.2030", "start_datetime", "2030-01-01T00:00:00")
model.add_attribute("ts.hourly.2030", "resolution", "PT1H")
model.add_attribute("ts.hourly.2030", "length", 8760)

model.add_entity("Profile", "profile.demand.CH")
model.add_attribute("profile.demand.CH", "profile_type", "as_normalized_annual_energy")
model.add_attribute("profile.demand.CH", "data_reference", "profiles.h5:/profiles/profile.demand.CH")
model.add_relation("profile.demand.CH", "hasTimestampSeries", "ts.hourly.2030")
model.add_relation("demand.CH", "hasDemandProfile", "profile.demand.CH")
```

| `profile_type` | Meaning | Typical use |
|---|---|---|
| `as_capacity_factor` | share of installed capacity | wind, PV availability |
| `as_normalized_annual_energy` | share of a yearly total | demand |
| `as_SI` | absolute values | prices, measurements |

| Common mistake | Fix |
|---|---|
| an array whose length differs from the `TimestampSeries` length | regenerate or trim the data |
| a `profile_type` that does not match the data — a capacity factor declared as `as_SI` | match the type to what the numbers mean |
| one time axis per profile | let all profiles of a study share one `TimestampSeries` |
