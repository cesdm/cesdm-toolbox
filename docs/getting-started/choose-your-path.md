# Choose Your Path

Pick the shortest path for what you want to do. Lost? Use the [map](#documentation-map) at the bottom.

!!! tip "Default path (energy-system modeller)"
    [CESDM in 5 Minutes](cesdm-in-5-minutes.md) → [Build a Small Electricity System](first-model-simple.md) → [How CESDM represents your system](core-concepts.md) → [Schemas](schemas.md) → [Validation](validation.md)

---

## Energy-system modeller

*I want to build or exchange models.*

**Start:** [Build a Small Electricity System](first-model-simple.md) (or [Quickstart](quickstart.md) if you still need to install).

| Step | Page | Why |
|------|------|-----|
| 1 | [CESDM in 5 Minutes](cesdm-in-5-minutes.md) | Problem and picture, no install |
| 2 | [Quickstart](quickstart.md) | Install and run the script (~20 min) |
| 3 | [Build a Small Electricity System](first-model-simple.md) | Wind, PV, hydro, demand — validate and export |
| 4 | [How CESDM represents your system](core-concepts.md) | Entities, attributes, relations |
| 5 | [Schemas](schemas.md) · [Validation](validation.md) | Vocabulary and checks |
| 6 | [Libraries](../guides/libraries.md) · [Profiles](../guides/profiles.md) | Shared types and time series |
| 7 | [Building your CESDM Model](../tutorials/building-first-model/overview.md) | CH + neighbours, multi-carrier (optional) |
| 8 | [Cheat sheet](modeller-cheat-sheet.md) | Patterns while modelling |

Python style for day-to-day work lives under [Develop — Proxy API](../guides/proxy-api.md) when you need it — not in the first hour.

---

## Existing PyPSA / pandapower user

*I want to convert an existing model.*

**Start:** [Tool adapters](../guides/tool-adapters.md).

Then: [Validation](validation.md) → export formats in [Modelling workflow](../guides/modelling-workflow.md).

---

## Tool developer

*I want to integrate CESDM into my software.*

**Start:** [Schemas](schemas.md) → [Schema augmentation](schemas-in-depth.md) → [EAR API Reference](../reference/api-reference.md).

See also [Project status](project-status.md) and [CESDM vs other tools](cesdm-vs-others.md).

---

## Curious reader

*Understand CESDM before installing.*

[CESDM in 5 Minutes](cesdm-in-5-minutes.md) → [What is CESDM?](what-is-cesdm.md) → [CESDM vs other tools](cesdm-vs-others.md) → [FAQ](../community/faq.md)

No Python required.

---

## Documentation map

### Learn

| Page | Content |
|------|---------|
| [CESDM in 5 Minutes](cesdm-in-5-minutes.md) | Physical system → CESDM names |
| [What is CESDM?](what-is-cesdm.md) | Motivation and hub vs chain |
| [CESDM vs other tools](cesdm-vs-others.md) | PyPSA, CIM, CrossContract |
| [Project status](project-status.md) | Available / experimental / planned |
| [How CESDM represents your system](core-concepts.md) | Entities, attributes, relations |
| [Schemas](schemas.md) · [Validation](validation.md) | Rules and checks |

### Build

| Page | Content |
|------|---------|
| [Build a Small Electricity System](first-model-simple.md) | Canonical first tutorial |
| [Quickstart](quickstart.md) · [Installation](installation.md) | Install and run |
| [Building your CESDM Model](../tutorials/building-first-model/overview.md) | Full reference model |
| [Modelling workflow](../guides/modelling-workflow.md) | Build → validate → export |

### Use

| Page | Content |
|------|---------|
| [Profiles](../guides/profiles.md) | Time series |
| [Libraries](../guides/libraries.md) | Shared technologies and carriers |
| [Tool adapters](../guides/tool-adapters.md) | PyPSA, pandapower, MATPOWER |
| [Carrier domains](../guides/carrier-domains.md) | Electricity, gas, heat |

### Look up / Develop

| Page | Content |
|------|---------|
| **[Schema Reference](../reference/schema-reference.html)** | Classes, attributes, relations |
| [Cheat sheet](modeller-cheat-sheet.md) · [Glossary](../community/glossary.md) | Patterns and terms |
| [Proxy API](../guides/proxy-api.md) · [EAR API](../reference/api-reference.md) | Python interfaces |
| [Schema augmentation](schemas-in-depth.md) | Extend the vocabulary |

---

→ [CESDM in 5 Minutes](cesdm-in-5-minutes.md)
