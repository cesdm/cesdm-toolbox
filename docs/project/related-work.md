# Related work

CESDM is a shared model *between* tools. Several neighbouring projects solve different, adjacent problems.

| Project | Its job | Relation to CESDM |
|---|---|---|
| **CIM / CGMES** | Standard exchange of electricity grid models between system operators | Different setting. CESDM covers several carriers and research tools that do not speak CGMES. A study can use both. |
| **ESDL** | Shared multi-carrier description with map-based tools | Closest peer; different foundation (below). |
| **oemof, TIMES, OSeMOSYS, FINE** | Formulate and solve an energy system model | These are tools. CESDM is what they would import from or export to. |
| **PyPSA, Calliope, pandapower** | Run an analysis | Same: tools at the ends of an adapter. |
| **[CrossContracts](https://sweet-cross.github.io/crosscontract/)** | Contracts for scenario assumptions and results | Complementary, see below. |

## ESDL

The [Energy System Description Language](https://energytransition.github.io/), developed by TNO, is an open, multi-carrier representation used by several tools since 2018, with map-based editing and GIS integration.

| | CESDM | ESDL |
|---|---|---|
| Foundation | generic entity–attribute–relation core, domain structure in versioned schema files | UML/Ecore metamodel |
| Constraints | in schema YAML, checked on load | in the metamodel |
| Typical entry point | Python, adapters to analysis tools | graphical, GIS-first |
| Extension | add a schema package, without touching the core | change the shared metamodel, regenerate |

Neither is more correct. A team invested in ESDL's GIS tooling has little reason to switch. CESDM fits teams whose work starts in Python and who move one system between analysis tools — dispatch, power flow, dynamics — on the same assets.

## CrossContracts

Both are activities of [SWEET-CoSi](https://www.sweet-cosi.ch/).

- **CESDM is system-centric:** what the energy system consists of — assets, their properties and relations — complete enough for a tool to run an analysis.
- **CrossContracts is data-centric:** it defines, validates and publishes datasets as contracts, with a focus on scenario assumptions and study-level results across models.

A scenario assumption (“PV capacity in 2035”) can live in CrossContracts; the concrete system built from it, which a tool runs, lives in CESDM.
