# Glossary

Key CESDM terms used throughout the documentation. Link to these entries when a concept is introduced on a page.

---

## Analysis
A specific engineering workflow or study performed on an energy system model, such as optimal dispatch, power flow, dynamic simulation, or capacity expansion planning.

---

## Analysis-specific Validation
Validation that checks whether a CESDM model contains all information required for a particular [analysis](#analysis). Unlike [schema validation](#schema-validation), it verifies model completeness rather than structural correctness.

---

## Analysis View
An analysis-specific representation of a [common system model](#common-system-model) derived from the physical system description. Different analyses may require different subsets or aggregations of the same physical system.

---

## Asset
A physical component of an energy system represented by a CESDM [entity](#entity), such as a generator, storage unit, transmission line, demand, or conversion unit.

---

## Attribute
A named property of an [entity](#entity). Attributes describe the characteristics of an object. Together with [relations](#relation), attributes are one of the three building blocks of the [EAR](#ear) model — see [Core Concepts](../getting-started/core-concepts.md).

---

## Attribute Group
A logical grouping of schema-defined attributes and relations by modelling perspective, such as `dispatch`, `topology`, or `power_flow`. Declared in schema YAML via `belongsToGroup` — see [Schemas — Attribute groups](../getting-started/schemas.md#attribute-groups).

Attribute groups improve the usability of the [Proxy API](#proxy-api) but do not change the underlying semantic model.

---

## Carrier
A physical commodity that can be transported, stored, converted, or consumed within an energy system, for example electricity, natural gas, hydrogen, heat, water, steam, ammonia, or CO₂.

---

## Carrier Domain
A physical transfer domain that transports exactly one [carrier](#carrier).

Typical examples include electrical transmission systems, gas networks, district heating systems, hydrogen pipelines, water systems, and CO₂ transport networks.

---

## CESDM
The **Common Energy System Domain Model**.

CESDM extends the generic [EAR](#ear) framework with energy-system specific [schemas](#schema), reusable [libraries](#library), analysis support, validation, aggregation, and import/export functionality.

---

## Common System Model
The complete CESDM representation of a [physical energy system](#physical-energy-system).

It serves as the single source of truth from which [analysis views](#analysis-view) and [tool-specific models](#tool-specific-model) are derived.

---

## Conversion Unit
An [asset](#asset) that converts one or more input carriers or resources into one or more output carriers.

Examples include gas turbines, heat pumps, electrolysers, combined heat and power plants, and fuel cells.

---

## Default Library
The standard CESDM [library](#library) containing commonly used reusable entities such as [carriers](#carrier), [technology](#technology) definitions, [natural resources](#natural-resource), and other reference objects.

---

## EAR
The **Entity–Attribute–Relation** modelling framework on which CESDM is built.

Every CESDM model consists of [entities](#entity), [attributes](#attribute), and [relations](#relation). See [Core Concepts](../getting-started/core-concepts.md).

---

## Entity
A uniquely identified **instance** in a CESDM model — a concrete object in your study (e.g. `gen.ch.wind`).

Entities represent physical [assets](#asset), [carriers](#carrier), resources, [profiles](#profile), regions, [technologies](#technology), and many other concepts. Distinguished from [entity class](#entity-class), which defines the *type*.

---

## Entity Class
A [schema](#schema)-defined **type** describing the permitted attributes, relations, inheritance, and validation rules shared by a family of [entities](#entity) (e.g. `GenerationUnit`).

Modellers create **instances** of entity classes; classes are defined in [schemas](#schema) (CESDM core or [extended schemas](../getting-started/schemas-in-depth.md)).

---

## Frictionless Data Package
A tabular exchange format for CESDM models — CSV resources with a `datapackage.json` manifest. Alternative to hierarchical [YAML](#yaml) for spreadsheet-oriented workflows and tabular pipelines.

---

## Library
A reusable collection of CESDM [entity](#entity) instances shared across multiple projects — for example the [default library](#default-library).

Libraries typically contain [technology](#technology) definitions, [carrier](#carrier) definitions, [natural resources](#natural-resource), and other commonly used reference objects. Stored as [YAML](#yaml) like any CESDM model.

---

## Natural Resource
An exogenous resource supplied by nature rather than by another system asset.

Examples include wind, solar irradiation, water inflow, geothermal energy, and biomass resources.

---

## Physical Energy System
The real-world energy system represented by a CESDM model.

CESDM models describe the physical system rather than any particular software tool or analysis.

---

## Profile
A metadata [entity](#entity) describing the meaning, interpretation, and storage location of a time series.

The numerical values themselves are stored separately — typically in HDF5 or Parquet — while structure and semantics live in [YAML](#yaml). Linked to assets via [relations](#relation) and tied to a [timestamp series](#timestamp-series).

---

## Profile Type
Defines how the numerical values associated with a [profile](#profile) should be interpreted.

Examples include capacity factors, normalized annual energy distributions, or absolute physical quantities.

---

## Proxy API
An object-oriented programming interface providing typed access to CESDM [entities](#entity).

The Proxy API operates on exactly the same underlying [EAR](#ear) model while improving readability, auto-completion, and type safety. See the [Proxy API guide](../guides/proxy-api.md).

---

## Reference Model
A complete CESDM model used throughout the documentation and tutorials to demonstrate modelling concepts and workflows.

---

## Relation
A typed semantic connection between two [entities](#entity).

Relations describe how objects are connected within the [physical energy system](#physical-energy-system) — for example topology, geography, or classification.

---

## Schema
A [YAML](#yaml) definition specifying [entity classes](#entity-class), [attributes](#attribute), [relations](#relation), inheritance, constraints, and validation rules.

Schemas define the modelling vocabulary; your study model contains [entity instances](#entity). See [Schemas](../getting-started/schemas.md).

---

## Schema Validation
Validation that verifies whether a CESDM model conforms to the [schemas](#schema).

Schema validation checks entity classes, attributes, relations, inheritance rules, constraints, and data types independently of any particular [analysis](#analysis).

---

## Spatial Aggregation
The process of deriving a new CESDM model with reduced geographical resolution while preserving semantic consistency.

The original model remains unchanged.

---

## Technology
A reusable description of the characteristics shared by a class of [assets](#asset).

Individual assets reference technology [entities](#entity) via `hasTechnology` instead of duplicating common information — see [Libraries](../guides/libraries.md).

---

## Timestamp Series
Defines the common time axis shared by one or more [profiles](#profile).

---

## Tool-specific Model
A representation of a CESDM model transformed into the format required by a particular software tool.

Tool-specific models are derived from the [common system model](#common-system-model) without redefining the physical system.

---

## Validation Profile
A [YAML](#yaml) document describing the information required for a particular [analysis](#analysis).

Validation profiles are used by [analysis-specific validation](#analysis-specific-validation). Shipped examples: `analysis_profiles/optimal_dispatch.yaml`, `analysis_profiles/power_flow.yaml`.

---

## View
A representation of the [common system model](#common-system-model) tailored to a specific purpose, such as a particular analysis, software tool, or reporting workflow.

---

## YAML
**YAML** (YAML Ain't Markup Language) is a human-readable, text-based data format used throughout CESDM.

Typical uses:

| Use | Example |
|-----|---------|
| [Schemas](#schema) | Entity classes, attributes, relations under `schemas/cesdm/` |
| [Libraries](#library) | Shared reference entities in `library/default_library/` (carriers, technologies, resources) |
| **Model files** | Hierarchical export of a study scenario |
| [Validation profiles](#validation-profile) | Analysis readiness rules in `analysis_profiles/` |

CESDM models are commonly exchanged as hierarchical YAML together with external profile data (HDF5 or Parquet). YAML keeps structural metadata compact and version-control friendly; bulk time-series values are stored separately.

---

## See also

- [Core Concepts](../getting-started/core-concepts.md) — entities, attributes, relations
- [Modeller cheat sheet](../getting-started/modeller-cheat-sheet.md) — quick patterns
