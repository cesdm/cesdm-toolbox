# Related work

CESDM is a **shared system representation**, not a new solver and not a replacement for established electricity-network exchange standards. Experienced readers often ask why another format exists. The short answer: neighbouring work solves **different jobs**.

| Neighbour | Primary job | CESDM's job |
|-----------|-------------|-------------|
| **CIM / CGMES** | Standardised **electricity-network** information exchange (operations and planning) | Tool-independent **multi-carrier** energy-system models reused across analysis types |
| **oemof, TIMES, OSeMOSYS, FINE** | Build and **optimise** a (often multi-carrier) energy-system model | Shared system representation that several modelling tools can import and export |
| **ESDL** | Shared, multi-carrier system representation, with its own modelling and GIS tools | Same job, different foundation — see [Why not ESDL?](#why-not-esdl) below |
| **[CrossContracts](https://sweet-cross.github.io/crosscontract/)** | Data contracts for **scenario assumptions and results** | Shared **system** representation a modelling tool can run — see [below](#what-is-the-difference-between-cesdm-and-crosscontracts-and-how-do-they-complement-each-other) |
| **PyPSA, Calliope, pandapower, …** | Run types of analysis (planning, dispatch, power flow, …) | Hold one checked shared system representation those modelling tools can import and export |

CESDM therefore sits **beside** these projects. It does not replace a TSO grid-exchange process, and it does not replace an optimisation or power-flow engine.

## Why not CIM / CGMES?

[CIM](https://www.iec.ch/) (IEC 61970 / 61968) and ENTSO-E [CGMES](https://www.entsoe.eu/data/cim/cim-for-grid-models-exchange/) are the established way to exchange **electricity** network models among system operators and vendors. They are strong where the problem is a grid model for operations or planning in one carrier.

CESDM is aimed at a different workflow:

- **several carriers** in one model (electricity, gas, heat, hydrogen, …);
- the **same physical asset** used for planning, dispatch, power flow and dynamics;
- research and planning tools that do **not** all speak CGMES (PyPSA, Calliope, pandapower, in-house models).

The concepts overlap for electrical buses and generators. The primary exchange setting does not: CGMES is the electricity-sector grid-model standard; CESDM is a schema-driven research representation for **interoperable multi-tool, multi-analysis** models. A study can use both — CGMES for the grid exchange, CESDM for the shared research model — rather than treating one as a substitute for the other.

## Why not oemof (or TIMES / OSeMOSYS / FINE)?

[oemof](https://oemof.org/) (in particular oemof.solph), [TIMES](https://iea-etsap.org/index.php/etsap-tools/model-generators/times), [OSeMOSYS](https://osemosys.org/) and [FINE](https://github.com/FZJ-IEK3-VSA/FINE) are **modelling and optimisation frameworks**: you formulate a system — several of them already multi-carrier — and solve it. That is the job of a modelling tool, not a shared representation.

CESDM does not formulate or solve an optimisation. A model built in any of these frameworks is that framework's own internal representation. CESDM is the **shared system representation** you would **import from or export to** one of them (or any other modelling tool) so the same system can also be used for a different type of analysis elsewhere.

If you already work in one of these frameworks, you still need a mapping if you want that system in PyPSA, pandapower or an in-house model. That mapping is an [adapter](../develop/adapter-development.md), not a reason to skip a shared system representation.

## Why not ESDL?

The [Energy System Description Language (ESDL)](https://energytransition.github.io/), developed by TNO ([source](https://github.com/EnergyTransition/ESDL)), is the closest peer to CESDM: an open, machine-readable, multi-carrier representation meant to be imported and exported by several independent tools, with an active ecosystem (MapEditor, the ESSIM simulator, GIS integrations) in use since 2018.

The two differ in how the shared representation is built:

| | CESDM | ESDL |
| --- | --- | --- |
| Foundation | Generic entity–attribute–relation (EAR) core, with domain structure added as a schema layer | UML/Ecore metamodel (Eclipse Modeling Framework) |
| Where constraints live | In versioned schema files, validated on load | In the metamodel itself |
| What the model generates | Validated data + a Python API | Client code, generated UI (MapEditor) and documentation, all from one Ecore source |
| Typical entry point | Python, adapters to PyPSA / Calliope / pandapower | Graphical, map-based modelling, GIS-first |
| Extending it | Add or version a schema file | Change the shared Ecore model, regenerate dependents |

Neither is "more correct" — they are different trade-offs between structural guarantees (ESDL) and modular, incremental extensibility (CESDM). A team already invested in ESDL's tooling, especially spatial/GIS workflows, has little reason to switch. CESDM's case is for teams whose workflow starts in Python and needs to move a system between analysis-focused tools without adopting a full modelling-language toolchain.

## What is the difference between CESDM and CrossContracts, and how do they complement each other?

CESDM and [CrossContracts](https://sweet-cross.github.io/crosscontract/) are both activities within [SWEET-CoSi](https://www.sweet-cosi.ch/), and address different but complementary aspects of energy-system modelling interoperability. They differ along two independent dimensions: approach and scope.

**Approach**

- **CESDM** is system-centric: it describes what an energy system consists of — entities, their properties, and how they relate to each other.
- **CrossContracts** is data-centric: it defines, validates and publishes datasets as contracts.

**Scope**

- **CESDM** aims to represent the whole energy system as a simulation-ready package — all entities, relations and data a modelling tool needs to run an analysis, including the detailed results of that analysis. This spans a broad range of analysis types on the same underlying model: from higher-level investment planning and economic dispatch down to lower-level power-flow and dynamic analysis.
- **CrossContracts** focuses on scenario assumptions and results — the higher-level assumptions that lead to the concrete systems being analyzed, and the study-level outputs that come out of that analysis, varying across scenarios, models and analyses.

The same comparison is in the [FAQ](../community/faq.md#what-is-the-difference-between-cesdm-and-crosscontracts-and-how-do-they-complement-each-other).

## Modelling tools

PyPSA, Calliope, pandapower and similar **modelling tools** run **types of analysis**. CESDM is the shared system representation those analyses use. See [What is CESDM?](../get-started/what-is-cesdm.md) and [Import and export](../use/import-export.md).

## Next

- New to CESDM: [What is CESDM?](../get-started/what-is-cesdm.md)
- Connect your own tool: [Adapter development](../develop/adapter-development.md)
