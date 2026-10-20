# Roadmap and releases

## Current release: toolbox 1.0.0, schema 1.0.0

The first public release of the toolbox is 1.0.0. The schema is 1.0.0, in three folders:

- `cesdm/schemas/base` — dispatch base, package name `cesdm`. Version in `cesdm/schemas/base/SCHEMA_MANIFEST.yaml`.
- `cesdm/schemas/powerflow` — bus type, line impedance, voltage setpoints, `ShuntUnit`. Package name `cesdm-powerflow`. Extends the base.
- `cesdm/schemas/dynamics` — machine models and controllers. Package name `cesdm-dynamics`. Extends the base.

It is a usable foundation that we want to develop together with modelling groups — through use cases, adapters, schema extensions and critique. CESDM is developed in Task 1.9 of [SWEET-CoSi](https://www.sweet-cosi.ch/) — conceptual and methodological foundations for common energy-system representations — and this toolbox is its reference implementation. The schemas will evolve with new use cases; the rules below say how, so that models built today stay usable.

When you share a model, record the toolbox commit and the schema packages the file lists. An export records the package name from each manifest (`cesdm`, `cesdm-powerflow`, `cesdm-dynamics`), not the folder name, together with that package's version.

## What is stable

Intended for long-term use. Breaking changes are rare and raise the major version.

- core classes: assets, nodes, carriers, technologies, profiles
- dispatch and topology attributes on `cesdm/schemas/base`
- electricity transmission classes used by the shipped importers

## What is experimental

Working, but expected to change with use:

- `cesdm/schemas/powerflow` and `cesdm/schemas/dynamics`
- capacity-expansion and some technical attribute groups on the base
- the spatial attribute group

Prefer the stable parts for models you need to keep valid across releases. Each package declares the stability of its parts under `stability:` in its `SCHEMA_MANIFEST.yaml`; in Python, `model.schema_manifest.stability_for("assets")` returns `"stable"`.

## Versioning

Schemas use semantic versioning. The rule: **if an existing model no longer validates without changes, it is a major change.** New optional classes or attributes are minor; documentation fixes are patches. How a change is classified is decided in the open, through issues and pull requests.

## Next

- **Community workshop**: groups that model energy systems try CESDM on their own data and tell us what is missing or hard to use — in the schema, the adapters and this documentation. Their feedback sets the priorities for the next release. To take part, [open an issue](contribute.md) or write to us
- **Entities, attributes and relations, with the community**: the shared vocabulary grows from studies that need a class, an attribute or a relation the core does not have. A group adds it in its own schema package first, and proposes it for the core when other groups need the same thing. The [versioning rule](#versioning) decides whether that change is minor or major
- **More tools for modellers**: tools for routine tasks, like the existing [aggregation tool](../use-cases/tyndp-pypsa.md#reduce-it-to-the-scale-you-need), and more adapters, including an export to PyPSA. Which ones come first depends on community feedback
- **Analysis results**: classes that store a dispatch, power-flow or dynamic run next to the system it was computed on, so two groups can compare results on the same model. Schema 1.0.0 does not include them yet
- **Scenarios as variants**: a scenario file that lists only what changes against a base model — "nuclear 0 MW, PV 12 000 MW" — and is applied to it. Groups share the small file instead of a second copy of the model, and the differences between scenarios are visible at a glance