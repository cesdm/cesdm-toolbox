# Release log

This is the **initial public release** of the CESDM documentation and the CESDM core schema **1.0.0**.

This first release is a starting point: a usable, flexible framework for a shared energy-system representation. The aim is that modelling communities can develop that objective together — through new use cases, adapters, schema extensions and critique. Pin the toolbox commit or release together with schema **1.0.0** when you share a model. What is stable vs experimental: [Roadmap](roadmap.md). How versions work: [Schema governance](../develop/governance.md).

## CESDM 1.0.0 — initial release

**Shared system representation.** CESDM describes an energy system so modelling tools can **import** and **export** it and reuse it across **types of analysis** (planning, dispatch, power flow, dynamics).

**Get Started**

- [What is CESDM?](../get-started/what-is-cesdm.md)
- [Installation](../get-started/install.md)
- [Build your first model](../get-started/first-model.md)

**Use**

- Build, [validate](../use/validate-models.md), and [import/export](../use/import-export.md)
- [Spatial aggregation](../use/spatial-aggregation.md) to NUTS and country scales
- Shipped converters for [TYNDP 2024 and PyPSA `elec.nc`](../examples/import-tyndp-and-pypsa.md); source data via `cesdm-download-external-data`, ready-made CESDM packages via `cesdm-download-converted-data`

**Understand**

- [Entities and relationships](../understand/entities-and-relationships.md), [schemas](../understand/schemas.md), [profiles](../understand/profiles.md), [libraries](../understand/libraries.md), [carrier domains](../understand/carrier-domains.md)
- [Related work](../understand/related-work.md) — CESDM beside CIM/CGMES, ESDL, oemof and modelling tools

**Develop**

- [Adapter development](../develop/adapter-development.md) for your own modelling tool
- Python API, schema extensions, [governance](../develop/governance.md)

**Community**

- [FAQ](faq.md), [citation](citation.md), [contributing](contributing.md), [roadmap](roadmap.md)

The schema version is declared in `schemas/cesdm/SCHEMA_MANIFEST.yaml` and recorded on export.

→ [Roadmap](roadmap.md) · [How to cite CESDM](citation.md)
