# What is CESDM?

CESDM provides a **shared, machine-readable representation of an energy system** that can be reused across modelling tools (e.g. PyPSA, Calliope, pandapower) and types of analysis (e.g. planning, dispatch, power flow and dynamics).

## Why is that useful?

Imagine a TYNDP scenario needs to be represented and analysed across PyPSA, Calliope, pandapower and an in-house model. Without a shared system representation, exchanging the scenario can require a separate converter between each pair of modelling tools. Four modelling tools already imply **six pairwise converters**.

<p align="center" markdown="1">
![Every tool pair needs its own converter](../illustrations/tool_exchange_chain.svg){ width="85%" }
</p>

CESDM sits in the middle. Modelling tools **import** and **export** the shared system representation.

<p align="center" markdown="1">
![CESDM shared system representation imported and exported by modelling tools](../illustrations/cesdm_shared_representation.svg){ width="88%" }
</p>

CESDM therefore addresses two related problems:

### 1. Import / export

A modelling tool needs one mapping to CESDM rather than pairwise mappings to every other modelling tool.

### 2. Consistency

Different types of analysis can refer to the **same physical asset**. Dispatch, power flow and dynamics do not need three disconnected descriptions of the same generator.

> **CESDM provides the shared system representation, connecting modelling tools and enabling reuse across different types of analysis.**

## What does CESDM contain?

At a high level, a CESDM model contains:

- **objects** — for example buses, generators, demand and storage;
- **properties** of those objects — for example a generator:
    - general — capacity 500 MW;
    - planning — investment cost, lifetime;
    - dispatch — variable cost, efficiency;
    - power flow — voltage setpoint, reactive power limits;
    - dynamics — inertia, time constants;
- **relations** between them — for example:
    - general — a generator connected to a bus;
    - dynamics — an Automatic Voltage Regulator (AVR) connected to a generator.

Later, the documentation introduces the technical names *entities*, *attributes* and *relationships*. You do not need those terms to get started.

## What is CESDM not?

| CESDM is | CESDM is not |
|---|---|
| A shared system representation of an energy system | An optimisation or power-flow engine |
| A checked representation that modelling tools can import and export | A replacement for PyPSA, pandapower or other modelling tools |
| One mapping per modelling tool, not one per tool pair | A requirement that every modelling tool uses the same internal data structure |

Why a new representation rather than CIM/CGMES, ESDL or oemof is explained in [Related work](../understand/related-work.md).

The current schema version is **1.0.0**. See the [roadmap](../community/roadmap.md) (stable vs experimental) and the [release log](../community/changelog.md).

Next: **[Install the toolbox](install.md)**, then **[build a small electricity system](first-model.md)**.
