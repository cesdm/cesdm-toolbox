# Glossary

**Adapter** — code that translates one representation (a group's files or a tool) to and from CESDM, with `to_cesdm` and `from_cesdm`. See [write an adapter](../guides/write-an-adapter.md).

**Analysis profile** — a YAML file listing what a model must contain for one use, e.g. `optimal_dispatch`. Checked with `validate_for_analysis`. Groups can write their own. See [validation](../concepts/validation.md).

**Attribute** — a value of an entity, with a unit, e.g. `nominal_power_capacity = 4000 MW`. See [Entity, attribute, relation](../concepts/ear.md).

**Attribute group** — a label in the schema that sorts an entity's attributes by use (`dispatch`, `power_flow`, `dynamics`, `topology`, …). The data stay on one entity. See [attribute groups](../concepts/schemas.md#attribute-groups).

**Augmentation** — attaching attributes or relations from an extension package to an existing class, without subclassing it. See [extending without forking](../concepts/schemas.md#extending-without-forking).

**Carrier** — what is transported: electricity, gas, heat, hydrogen, …

**Carrier domain** — the infrastructure that transports one carrier. See [carrier domains](../guides/carrier-domains.md).

**CESDM** — Common Energy System Domain Model: the energy-system domain built on the EAR engine — the CESDM schema packages plus the `cesdm` package. See [Why CESDM](../concepts/index.md).

**CesdmModel** — the model class returned by `cesdm_toolbox.build_model_from_yaml`: an `ear` model plus libraries, energy file formats and proxies. See [the EAR engine and CESDM](../concepts/engine.md#the-energy-system-domain-cesdm).

**Class** — a type of entity defined in the schema, e.g. `GenerationUnit`. An instance is one object of that class, e.g. `gen.CH_HYD_RES`. Classes inherit from each other. See [Entity, attribute, relation](../concepts/ear.md).

**Conversion unit** — an asset that links two carrier domains, e.g. a heat pump.

**EAR** — Entity–Attribute–Relation. An entity is one object, an attribute is a value on it, a relation points at another object. See [Entity, attribute, relation](../concepts/ear.md).

**EAR engine** — the `ear` package: loads a schema, builds and checks models, reads and writes files. It contains no energy classes and can serve any domain. CESDM is the energy-system domain built on it. See [the EAR engine and CESDM](../concepts/engine.md).

**Endogenous / exogenous** — whether a carrier's network is inside the model boundary or only its supply.

**Entity** — one object in a model, e.g. the generator `gen.CH_NUC`. See [Entity, attribute, relation](../concepts/ear.md).

**Extension package** — a schema package that builds on another (`extends: [../cesdm]`) and adds classes, attributes or augmentations. `schemas/cesdm_power_flow` and `schemas/cesdm_dynamic` are extension packages. See [Extend the schema](../guides/extend.md).

**Frictionless package** — a tabular export: `datapackage.json`, one CSV per class, and `relations.csv` for every link. Attribute columns are paired with `__unit` and `__provenance_ref`.

**Instance** — one object of a class, e.g. `gen.CH_HYD_RES` is an instance of `HydroGenerationUnit`. You create instances; the schema defines classes. See [classes and instances](../concepts/ear.md#classes-and-instances).

**Library** — a CESDM model of shared objects (technologies, carriers, regions) that other models link to. See [libraries](../concepts/energy-model.md#libraries).

**Profile** — an entity that describes a time series and points to its numbers in HDF5.

**Provenance** — the recorded source of a value (`provenance_ref`). See [provenance](../concepts/energy-model.md#provenance).

**Proxy API** — a shorter, attribute-style way of reading and writing entities in Python. See [the proxy API](../guides/proxy-api.md).

**Relation** — a link from one entity to another, e.g. `belongsToGeographicalRegion → region.country.CH`. See [Entity, attribute, relation](../concepts/ear.md).

**Representation** — the way one group or tool stores a system: its files, names, codes and units.

**Schema** — the agreed vocabulary of classes, attributes and relations. Three folders: `schemas/cesdm` (dispatch base, version 1.0.0), `schemas/cesdm_power_flow`, and `schemas/cesdm_dynamic`. The base version is in `schemas/cesdm/SCHEMA_MANIFEST.yaml`.

**Schema package** — one folder of schema files with its own `SCHEMA_MANIFEST.yaml`: `schemas/cesdm`, `schemas/cesdm_power_flow`, … See [Schemas](../concepts/schemas.md).

**Schema validation** — `model.validate()`: is the model correct CESDM? Analysis-independent; what a sender checks before exchanging a model.

**Timestamp series** — the time axis that profiles refer to.

**Zonal / nodal** — assets attached to regions (`belongsToGeographicalRegion`) or to buses (`atNode`).
