# Frequently Asked Questions

### What is the difference between CESDM and CrossContracts, and how do they complement each other?

CESDM and [CrossContracts](https://sweet-cross.github.io/crosscontract/) are both activities within [SWEET-CoSi](https://www.sweet-cosi.ch/), and address different but complementary aspects of energy-system modelling interoperability. They differ along two independent dimensions: approach and scope.

**Approach**

- **CESDM** is system-centric: it describes what an energy system consists of — entities, their properties, and how they relate to each other.
- **CrossContracts** is data-centric: it defines, validates and publishes datasets as contracts.

**Scope**

- **CESDM** aims to represent the whole energy system as a simulation-ready package — all entities, relations and data a modelling tool needs to run an analysis, including the detailed results of that analysis. This spans a broad range of analysis types on the same underlying model: from higher-level investment planning and economic dispatch down to lower-level power-flow and dynamic analysis.
- **CrossContracts** focuses on scenario assumptions and results — the higher-level assumptions that lead to the concrete systems being analyzed, and the study-level outputs that come out of that analysis, varying across scenarios, models and analyses.

See also [Related work](../understand/related-work.md#what-is-the-difference-between-cesdm-and-crosscontracts-and-how-do-they-complement-each-other).

---

## Getting started (energy system modellers)

### Which tutorial should I start with?

The **[Build your first model](../get-started/first-model.md)** tutorial. When you want a full multi-domain walkthrough, use the [multi-domain example](../examples/building-first-model/overview.md).

The [multi-domain example](../examples/building-first-model/overview.md) covers a larger model as a script — use as reference, not as first contact.

---

### Do I need to read the schema reference before building a model?

No. Start with [Build your first model](../get-started/first-model.md), then read [Entities and relationships](../understand/entities-and-relationships.md). Look up specific classes in the [Schema reference](../reference/schema.md) only when needed.

---

### Core API vs Proxy API — which should I use?

| API | When to use |
|-----|-------------|
| **Core [EAR](../reference/glossary.md#ear) API** | Learning, debugging, understanding the underlying representation |
| **[Proxy API](../reference/glossary.md#proxy-api)** | Building and maintaining your own study models day to day |

---

### Do I need Python to use CESDM?

You need Python to **build or modify** models programmatically. You can read exported [YAML](../reference/glossary.md#yaml) and inspect [Frictionless](../reference/glossary.md#frictionless-data-package) exports without writing code.

---

### Can I edit a model in Excel and re-import?

Yes, for inspection and data editing. Excel is not the native exchange format — use [YAML](../reference/glossary.md#yaml) + [Frictionless](../reference/glossary.md#frictionless-data-package) for version control and tool exchange. Re-import via the toolbox export/import utilities.

---

### How do I connect to PyPSA or pandapower?

For **TYNDP 2024 CSVs** and a PyPSA **`elec.nc`**, follow [Convert TYNDP and PyPSA](../examples/import-tyndp-and-pypsa.md). Already converted CESDM files (YAML + Frictionless): `cesdm-download-converted-data`. Other adapters live in `tools/` (`import_pypsa.py`, `import_pandapower.py`, …). See [Import and export](../use/import-export.md).

To connect a tool that has no shipped converter, start with [Adapter development](../develop/adapter-development.md).

---

### Which schema version is current?

The CESDM core schema version is **1.0.0** (`schemas/cesdm/SCHEMA_MANIFEST.yaml`). Exported models record it. History: [Release log](changelog.md). Stable vs experimental: [Roadmap](roadmap.md).

---

### What's the difference between schema validation and analysis validation?

| Check | Question | Command |
|-------|----------|---------|
| Schema | Is this a valid CESDM model? | `model.validate()` |
| Analysis | Is it ready for my study type? | `model.validate_for_analysis("optimal_dispatch")` |

Study-facing fields (dispatch, power flow, dynamics/controllers) are often schema-optional and only required by the matching profile under `analysis_profiles/`. See [Validation](../use/validate-models.md).

---

### Do I model every technology explicitly or use library types?

Use **`hasTechnology`** to reference [library](../understand/libraries.md) templates for standard technologies. Set site-specific parameters (capacity, location, custom efficiency) on the asset itself.

---

### Where do profile numbers live vs YAML metadata?

**[YAML](../reference/glossary.md#yaml)** stores Profile metadata (`profile_type`, `data_reference`, relations). **Numerical arrays** live in HDF5 or Parquet files referenced by `data_reference`. See [Profiles](../understand/profiles.md).

---

## General

### What is the difference between CESDM and PyPSA or Calliope?

CESDM is the **shared system representation**. PyPSA, Calliope, pandapower and similar **modelling tools** run different **types of analysis**. CESDM is what they can **import** and **export**; each modelling tool remains the solver for its analysis type.

---

### Why not CIM/CGMES, ESDL or oemof?

CIM/CGMES exchange **electricity network** models among system operators. oemof **builds and solves** energy-system optimisation models. ESDL is the closest peer: another shared multi-carrier system representation, with a different foundation and GIS-first toolchain. CESDM is none of those substitutes: it is a schema-driven shared representation that modelling tools can import and export. See [Related work](../understand/related-work.md).

---

### Why is CESDM schema-driven?

The model structure is defined by human-readable schema files instead of program code. This makes models transparent, extensible and easy to validate.

---

### Is CESDM an ontology?

No. CESDM is a schema-driven semantic framework. An ontology would catalogue concepts and their relations; CESDM uses that kind of concept graph, but what you load and exchange is a [schema](../understand/schemas.md) plus a study model.

- **Schema** — what information is allowed or required
- **Semantics** — what that information means
- **Ontology** — what concepts exist and how they are related

See [Entities and relationships](../understand/entities-and-relationships.md#schema-semantics-and-ontology).

---

## Concepts

### What is an Entity?

An entity represents a real-world object, such as a generator, transmission line or demand. See [Entities and relationships](../understand/entities-and-relationships.md).

---

### Why are Attribute Groups used?

Attribute groups organize information by modelling perspective (dispatch, topology, power flow, capacity expansion, etc.) while keeping all data on the same entity. See [Schemas — Attribute groups](../understand/schemas.md#attribute-groups).

---

### What is the difference between a CarrierDomain and a Carrier?

A **Carrier** describes *what* is transported (electricity, gas, heat). A **CarrierDomain** describes *where* it is transported (the corresponding network or infrastructure).

---

## Data and Formats

### How are time series stored?

CESDM entities reference time-series profiles; numerical values are stored separately (typically HDF5). See [Profiles](../understand/profiles.md).

---

### Can I open a CESDM model in Excel?

Yes, for inspection and editing. [YAML](../reference/glossary.md#yaml) remains the primary exchange format for version control.

---

### What is the native exchange format?

[YAML](../reference/glossary.md#yaml) files together with external profile data (HDF5). [Frictionless Data Packages](../reference/glossary.md#frictionless-data-package) provide a tabular alternative.

---

### How do I know my model is ready for my analysis?

Run `model.validate()` then `model.validate_for_analysis("<profile>")`. Shipped profiles include `optimal_dispatch`, `power_flow`, and `dynamics` under `analysis_profiles/`.

→ [Roadmap](roadmap.md) · [Build models](../use/build-models.md)
