# CESDM in 5 Minutes

!!! abstract "You will"
    - Understand the problem CESDM solves — without installing anything
    - See one physical system and how CESDM names its parts
    - Know the next step: [Build a Small Electricity System](first-model-simple.md)

**Time:** ~5 minutes. **Prerequisite:** none.

---

## The energy system

A small electricity system:

```text
Wind ───┐
PV ─────┼──► Bus ───► Demand
Hydro ──┘
         ▲
    Reservoir inflow
```

Wind, PV, and hydro inject power at one bus. Demand draws from the same bus. The reservoir that supplies hydro has a seasonal inflow.

---

## How CESDM represents it

CESDM does not invent a new solver. It names the **same physical objects** and how they connect:

```text
GenerationUnit (wind)  ──atNode──►  ElectricalBus  ◄──atNode──  DemandUnit
GenerationUnit (PV)    ──atNode──►       │
HydroGenerationUnit    ──atNode──►       │
        ▲
        └──drawsFromHydraulicStorage──  HydraulicStorageUnit
```

You can also attach numbers and library types:

```text
PV unit
  technology = utility solar PV
  capacity   = 300 MW
  atNode     = the same bus
```

The **same description** can later be used by different modelling tools.

---

## Use CESDM when you want to

- describe an energy system independently of a particular tool;
- reuse the same system across dispatch, grid analysis, or other studies;
- exchange models between partners without a converter for every tool pair;
- validate that a model contains the information an analysis needs.

---

## CESDM is — and is not

| CESDM is | CESDM is not |
|----------|--------------|
| A common description of the energy system | An optimisation model |
| A semantic data model + validation | A power-flow solver |
| An interoperability layer | Another PyPSA |
| A place to store inputs and results | A scenario database or CIM operations standard |

---

## 10 lines of Python (optional)

After [installation](installation.md), creating a bus and a generator looks like this:

```python
from cesdm_toolbox import build_model_from_yaml

model = build_model_from_yaml("schemas/cesdm")
model.import_library("library/default_library")

bus = model.add_entity("ElectricalBus", "bus.demo")
bus.name = "Demo bus 380 kV"

gen = model.add_entity("GenerationUnit", "gen.demo.pv")
gen.nominal_power_capacity = (300, "MW")
gen.atNode = bus
```

You do not need to understand the internals yet. Run the full first model next.

---

## Next step

1. **[Build a Small Electricity System](first-model-simple.md)** — same picture, complete script, validate and export (~10 min)
2. Or **[Quickstart](quickstart.md)** if you still need to install (~20 min)

[Choose your path](choose-your-path.md) if you already have a PyPSA model or you integrate CESDM into a tool.
