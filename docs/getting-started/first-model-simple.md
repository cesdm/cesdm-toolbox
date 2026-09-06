# Build a Small Electricity System

!!! abstract "You will"
    - Build one bus, wind, PV, reservoir hydro, and demand
    - See how CESDM names those objects and their connections
    - Run the script, validate, and export YAML + profiles
    - **Time:** ~10 minutes after [Quickstart](quickstart.md) / [Installation](installation.md)

In 10 minutes you create this system, validate it, and export it.

The same script is `docs/examples/minimal_electricity_model.py`. This page walks through it.

The [CH + neighbours tutorial](../tutorials/building-first-model/overview.md) adds other countries, gas, heat, and interconnectors. Start here first.

---

## 1. What are we building?

```text
Wind 500 MW ───┐
PV 300 MW ─────┼──► Bus (380 kV) ───► Demand 2 TWh/year
Hydro 200 MW ──┘
      ▲
      └── Reservoir 50 GWh  +  seasonal inflow
```

One aggregated node. Wind and PV have hourly availability. Demand and reservoir inflow have hourly shapes. Everything sits in study `DEMO_2030` and the electricity carrier domain from the default library.

---

## 2. How does CESDM represent it?

| Physical object | CESDM entity | Key links |
|-----------------|--------------|-----------|
| Study | `EnergySystemModel` `DEMO_2030` | — |
| Electricity domain | `CarrierDomain` (from library) | `belongsToCarrierDomain` on the bus |
| Switzerland | `GeographicalRegion` `region.country.CH` | `belongsToGeographicalRegion` on the bus |
| Grid node | `ElectricalBus` `bus.demo` | 380 kV |
| Wind farm | `GenerationUnit` `gen.demo.wind` | `atNode` → bus; library wind technology |
| Utility PV | `GenerationUnit` `gen.demo.pv` | `atNode` → bus; library PV technology |
| Reservoir | `HydraulicStorageUnit` `storage.demo.reservoir` | stores water; inflow profile |
| Hydro turbines | `HydroGenerationUnit` `gen.demo.hydro` | `atNode` → bus; `drawsFromHydraulicStorage` |
| Load | `DemandUnit` `dem.demo` | `atNode` → bus; 2 TWh/year |
| Hourly shapes | `Profile` + `TimestampSeries` | demand, wind CF, PV CF, inflow |

```text
PHYSICAL SYSTEM                      CESDM MODEL

  Wind / PV / Hydro                    GenerationUnit / HydroGenerationUnit
       │                                        │
       ▼                                        │ atNode
     Bus ──────── Demand              ElectricalBus ◄── atNode ── DemandUnit
       ▲
    Reservoir                      HydraulicStorageUnit
```

You do not redefine wind or PV technology. You **reference** library types.

---

## 3. Python implementation

Run the complete script from the **repository root**:

```bash
python docs/examples/minimal_electricity_model.py
```

Expected output:

```text
Validated model and exported to output/minimal_electricity_model
  profiles: demand, wind CF, PV CF, hydro inflow (8760 h → profiles.h5)
```

Inspect `output/minimal_electricity_model/demo_2030.yaml`, `profiles.h5`, and `frictionless/`.

The same model, step by step:

### Load schema and libraries

```python
from cesdm_toolbox import build_model_from_yaml
from cesdm.default_library import CarrierDomains, GeneratorTypes, NaturalResources

model = build_model_from_yaml("schemas/cesdm")
model.import_library("library/default_library")
model.import_library("library/regions_library")
```

### Study container and shared objects

```python
model.add_entity(entity_class="EnergySystemModel", entity_id="DEMO_2030")
model.add_attribute(
    entity_id="DEMO_2030",
    attribute_id="long_name",
    value="Minimal electricity demo",
)

electricity = model.get_entity(CarrierDomains.DOMAIN_ELECTRICITY)
region_ch = model.get_entity("region.country.CH")

ts = model.add_entity("TimestampSeries", "ts.hourly.2030")
ts.start_datetime = "2030-01-01T00:00:00"
ts.resolution = "PT1H"
ts.length = 8760
ts.timezone = "UTC"
```

### Bus, generation, storage, demand

```python
bus = model.add_entity("ElectricalBus", "bus.demo")
bus.name = "Demo bus 380 kV"
bus.nominal_voltage = (380, "kV")
bus.belongsToCarrierDomain = electricity
bus.belongsToGeographicalRegion = region_ch

wind = model.add_entity("GenerationUnit", "gen.demo.wind")
wind.name = "Demo wind farm"
wind.nominal_power_capacity = (500, "MW")
wind.hasTechnology = GeneratorTypes.GENERATION_RENEWABLE_WIND_ONSHORE
wind.hasInputResource = NaturalResources.RESOURCE_RENEWABLE_WIND
wind.atNode = bus

pv = model.add_entity("GenerationUnit", "gen.demo.pv")
pv.name = "Demo utility PV"
pv.nominal_power_capacity = (300, "MW")
pv.hasTechnology = GeneratorTypes.GENERATION_RENEWABLE_SOLAR_PV_UTILITY
pv.hasInputResource = NaturalResources.RESOURCE_RENEWABLE_SOLAR
pv.atNode = bus

reservoir = model.add_entity("HydraulicStorageUnit", "storage.demo.reservoir")
reservoir.energy_storage_capacity = (50_000, "MWh")
reservoir.annual_natural_inflow_energy = (200_000, "MWh/year")
reservoir.storesResource = NaturalResources.RESOURCE_WATER

hydro = model.add_entity("HydroGenerationUnit", "gen.demo.hydro")
hydro.nominal_power_capacity = (200, "MW")
hydro.atNode = bus
hydro.drawsFromHydraulicStorage = reservoir

demand = model.add_entity("DemandUnit", "dem.demo")
demand.annual_energy_demand = (2_000_000, "MWh/year")  # 2 TWh/year
demand.atNode = bus
```

The script also attaches **hourly profiles** (demand shape, wind and PV capacity factors, reservoir inflow) and writes them to `profiles.h5`. See [Profiles](../guides/profiles.md) for the pattern.

!!! tip "Units"
    `annual_energy_demand` must use **`MWh/year`** (not `GWh`). 1 GWh = 1,000 MWh.

!!! abstract "Two Python styles"
    This tutorial assigns attributes on entity handles (`bus.name = …`, `gen.atNode = bus`). That is the day-to-day style. The same model can be built with explicit `add_attribute` / `add_relation` calls — see [Proxy API](../guides/proxy-api.md) when you need that distinction.

### Validate and export

```python
errors = model.validate()
if errors:
    for e in errors:
        print(e)
else:
    print("Schema validation passed.")

model.export_yaml_hierarchical("output/minimal_electricity_model/demo_2030.yaml")
model.export_frictionless(
    "output/minimal_electricity_model/frictionless",
    name="minimal-electricity-demo",
    title="Minimal electricity demo model",
)
```

---

## 4. Result

| Output | Meaning |
|--------|---------|
| `validate()` with no errors | Schema-ready system description |
| `demo_2030.yaml` | Hierarchical model you can version-control |
| `profiles.h5` | 8760-hour demand, wind CF, PV CF, inflow |
| `frictionless/` | Tabular package for spreadsheets and pipelines |

Optional in Jupyter:

```python
%run docs/examples/minimal_electricity_model.py
```

---

## What this tutorial skips

- Neighbouring countries and interconnectors
- Gas, heat, and conversion units
- Multi-bus network detail

Those are in [Building your CESDM Model](../tutorials/building-first-model/overview.md).

---

## Next step

1. **[How CESDM represents your system](core-concepts.md)** — class vs instance, attributes, relations
2. **[Modelling workflow](../guides/modelling-workflow.md)** — build → validate → export
3. **[Building your CESDM Model](../tutorials/building-first-model/overview.md)** — full multi-domain reference

→ [Cheat sheet](modeller-cheat-sheet.md)
