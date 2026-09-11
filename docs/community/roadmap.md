# Roadmap

This first release is a starting point: a usable, flexible framework for a shared energy-system representation. The aim is that modelling communities can develop that objective together — through new use cases, adapters, schema extensions and critique. This page states what is stable enough to build on, what is still experimental, and the direction of the next work — not a dated product plan.

The current CESDM core schema version is **1.0.0** (`schemas/cesdm/SCHEMA_MANIFEST.yaml`). Exported models record that version. See [Schema governance](../develop/governance.md) for how versions and stability tiers work, and the [release log](changelog.md) for what this release contains.

## Stable today

These families are intended for long-term use. Breaking changes should be rare and would bump the **major** schema version.

- Core types, assets, nodes, carriers, technologies, profiles
- Dispatch and topology fields; power-flow parameters on the relevant types
- Dispatch run records
- Electricity transmission leaves used by the shipped importers

Round-trips against PyPSA and TYNDP imports exercise much of this backbone.

## Experimental

Functional, but still expected to evolve with use cases and feedback:

| Area | Status |
|------|--------|
| Power-flow and dynamics **run records** and **result** entities | Experimental |
| Dynamics, controllers, capacity-expansion and some technical field groups | Experimental |
| Spatial attribute group | Experimental |
| Market / bidding-zone types | Experimental |
| Gas and heat **transmission** (abstract types; no pipe leaves yet) | Experimental |

Prefer the stable families for work you need to keep valid across toolbox releases. Pin the schema version and toolbox commit when you share models — see [How to cite CESDM](citation.md).

## Direction

Work currently concentrates on:

- **More adapters** — mappings for tools beyond the shipped TYNDP, PyPSA and related importers ([Adapter development](../develop/adapter-development.md))
- **Multi-carrier completeness** — gas and heat transmission beyond placeholders
- **Analysis results** *(soon)* — integrating results of different types of analysis (investment analysis, economic dispatch, power flow, dynamics)
- **Semantics and ontology alignment** — agreed meaning of types and relations without turning CESDM into “an ontology” ([Entities and relationships](../understand/entities-and-relationships.md#schema-semantics-and-ontology))
- **System variants** — alternative representations of an energy system by defining only the differences from a common base. The same mechanism can support **scenario creation**.

Contributions are welcome in those areas; contacts are on [Contributing](contributing.md).

## What will not become CESDM

CESDM will not become an optimiser, a power-flow engine, or a replacement for CIM/CGMES electricity-network exchange. Neighbouring standards and tools are compared in [Related work](../understand/related-work.md).

→ [Release log](changelog.md) · [Schema governance](../develop/governance.md)
