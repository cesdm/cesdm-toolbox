# Roadmap and releases

## Current release: toolbox 1.0.0, schema 1.0.0

The first public release of the toolbox is 1.0.0. The schema is 1.0.0, in three folders:

- `schemas/cesdm` — dispatch base. Version in `schemas/cesdm/SCHEMA_MANIFEST.yaml`.
- `schemas/cesdm_power_flow` — bus type, line impedance, voltage setpoints, `ShuntUnit`, power-flow results. Extends the base.
- `schemas/cesdm_dynamic` — machine models, controllers, dynamic results. Extends the base.

It is a usable foundation that we want to develop together with modelling groups — through use cases, adapters, schema extensions and critique. CESDM is developed in Task 1.9 of [SWEET-CoSi](https://www.sweet-cosi.ch/) — conceptual and methodological foundations for common energy-system representations — and this toolbox is its reference implementation. The schemas will evolve with new use cases; the rules below say how, so that models built today stay usable.

When you share a model, record the toolbox commit, the base schema version, and which of the three folders you loaded. Exported models record the version of the schema that was loaded.

## What is stable

Intended for long-term use. Breaking changes are rare and raise the major version.

- core classes: assets, nodes, carriers, technologies, profiles
- dispatch and topology attributes on `schemas/cesdm`
- dispatch run records
- electricity transmission classes used by the shipped importers

## What is experimental

Working, but expected to change with use:

- `schemas/cesdm_power_flow` and `schemas/cesdm_dynamic`, including their result classes
- capacity-expansion and some technical attribute groups on the base
- the spatial attribute group
- market and bidding-zone classes
- gas and heat transmission (abstract classes, no pipe classes yet)

Prefer the stable parts for models you need to keep valid across releases. Each package declares the stability of its parts under `stability:` in its `SCHEMA_MANIFEST.yaml`; in Python, `model.schema_manifest.stability_for("assets")` returns `"stable"`.

## Versioning

Schemas use semantic versioning. The rule: **if an existing model no longer validates without changes, it is a major change.** New optional classes or attributes are minor; documentation fixes are patches. How a change is classified is decided in the open, through issues and pull requests.

## Next

- **More adapters**, including an export to PyPSA
- **Analysis results.** Result classes for dispatch, power flow and dynamics are part of the schema. The next release demonstrates how an analysis stores its output in those classes.
- **Multi-carrier completeness** for gas and heat transmission
- **System variants**: describe a variant only by its differences from a base — also a way to create scenarios
- **Semantic alignment** with neighbouring vocabularies

CESDM will not become a solver or a replacement for CIM/CGMES.
