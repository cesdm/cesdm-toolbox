# `example_simple.py` — Step by Step

## Why this example matters

One small system (3 electricity nodes) touching almost every core
entity type in one place: carriers, carrier domains, regions, three
different bus types, demand, two kinds of generation (dispatchable
and non-dispatchable), storage, interconnectors, and a multi-port
conversion unit. If you want to see how much of the schema fits
together without reading a huge system, this is the fastest way in.

Built with core EAR calls (`add_entity`/`add_attribute`/`add_relation`)
throughout, plus the proxy layer for convenient reading/writing
afterward — see [`docs/getting_started.md`](../docs/getting_started.md)
for the same style, and
[`docs/architecture/proxy_api.md`](../docs/architecture/proxy_api.md)
for the full proxy design.

---

## Carriers, domains, regions, buses

```python
for eid, name, co2, cost in [
    ("Electricity", "Electricity", 0.0,  0.0),
    ("Gas",         "Gas",         0.20, 60.0),
    ("Heat",        "Heat",        0.0,  0.0),
    ("Water",       "Water",       0.0,  5.0),
    ("Uranium",     "Uranium",     0.0,  10.0),
]:
    m.ensure_carrier(eid, name=name)
    carrier = m.get_entity(eid)
    carrier.co2_emission_intensity = co2
    carrier.energy_carrier_cost = cost

for did, name, carrier in [("ELEC", "Electricity", "Electricity"), ("HEAT", "Heat", "Heat"), ("GAS", "Gas", "Gas")]:
    m.add_entity("CarrierDomain", did)
    m.add_attribute(did, "name", name)
    m.add_relation(did, "hasCarrier", carrier)
```

`ensure_carrier()` creates the `Carrier` only if it doesn't
already exist and returns it wrapped in a typed proxy directly —
useful here since the default library may already define some of these
carriers.

Three bus classes, not one generic "bus":

```python
m.add_entity("ElectricalBus", "N_E1")
m.add_attribute("N_E1", "nominal_voltage", 220.0)
m.add_relation("N_E1", "locatedIn", "R_A")
m.add_relation("N_E1", "belongsToCarrierDomain", "ELEC")

m.add_entity("GasBus", "N_G1")
m.add_attribute("N_G1", "name", "Gas node G1")
m.add_relation("N_G1", "belongsToCarrierDomain", "GAS")
m.add_relation("N_G1", "locatedIn", "R_A")

m.add_entity("HeatBus", "N_H1")
m.add_attribute("N_H1", "name", "Heat node H1")
m.add_relation("N_H1", "belongsToCarrierDomain", "HEAT")
m.add_relation("N_H1", "locatedIn", "R_A")
```

`ElectricalBus`/`GasBus`/`HeatBus` are genuinely distinct classes with
their own typed nodes, not one generic bus with a carrier field.

---

## Two kinds of generation: dispatchable and not

```python
# Dispatchable: a gas turbine, carriers assigned directly (no technology template)
m.add_entity("GenerationUnit", "GT_A")
m.add_relation("GT_A", "atNode", "N_E1")
m.add_relation("GT_A", "hasInputCarrier", "Gas")
m.add_relation("GT_A", "hasOutputCarrier", "Electricity")
gt_a = m.get_entity("GT_A")
gt_a.dispatch.generator_technology_type = "gas"
gt_a.dispatch.energy_conversion_efficiency = 0.50
gt_a.dispatch.nominal_power_capacity = 200.0

# Non-dispatchable: run-of-river hydro -- a different concrete class
# (HydroGenerationUnit), dispatch_type set explicitly
m.add_entity("HydroGenerationUnit", "HYD_B")
m.add_relation("HYD_B", "atNode", "N_E3")
m.add_relation("HYD_B", "hasInputCarrier", "Water")
m.add_relation("HYD_B", "hasOutputCarrier", "Electricity")
hyd_b = m.get_entity("HYD_B")
hyd_b.dispatch.dispatch_type = "nondispatchable"
hyd_b.dispatch.turbine_efficiency = 0.90
hyd_b.dispatch.nominal_power_capacity = 150.0
hyd_b.dispatch.annual_resource_potential = 1_500_000.0
```

Both are `GenerationUnit` (or its `HydroGenerationUnit` subclass) with
`hasInputCarrier`/`hasOutputCarrier` set directly, rather than resolved
from a technology template — the dispatch attributes (`.dispatch.*`)
are flattened directly onto the asset either way (see
[`docs/architecture/proxy_api.md`](../docs/architecture/proxy_api.md)).
A reservoir-coupled dispatchable unit would instead use
`drawsFromReservoir` pointing at a `ReservoirStorageUnit` — see
[`README_HYDRO_RESERVOIR_EXAMPLE.md`](README_HYDRO_RESERVOIR_EXAMPLE.md).

---

## Storage

```python
m.add_entity("StorageUnit", "BAT_E2")
m.add_relation("BAT_E2", "atNode", "N_E2")
m.add_relation("BAT_E2", "storesCarrier", "Electricity")
bat_e2 = m.get_entity("BAT_E2")
bat_e2.dispatch.energy_storage_capacity = 500.0
bat_e2.dispatch.nominal_power_capacity = 100.0
bat_e2.dispatch.maximum_charging_power = 100.0
bat_e2.dispatch.charging_efficiency = 0.95
bat_e2.dispatch.discharging_efficiency = 0.95
bat_e2.dispatch.initial_state_of_charge = 0.50
```

---

## Interconnectors

```python
m.add_entity("Interconnector", "NTC_E1_E2")
m.add_attribute("NTC_E1_E2", "name", "NTC E1-E2")
ntc = m.get_entity("NTC_E1_E2")
ntc.connect(n_e1, n_e2)  # fromNode + toNode
ntc.power_flow.maximum_power_flow_from_to = 300.0
ntc.power_flow.maximum_power_flow_to_from = 300.0
```

`.connect(a, b)` wires `fromNode`/`toNode` in one call for any
two-port class (lines, transformers, interconnectors, ...); a
single-port class (generators, demand, storage) uses `.connect(bus)`
instead, wiring `atNode`.

---

## A multi-port fuel cell (Tier 2 MIMO)

A PEM fuel cell (H₂ → electricity + heat) needs three separate
`ConversionPort` entities — one per physical port, each with its own
flow coefficient defining the conversion ratio:

```python
m.add_entity("ConversionUnit", "FC_A")
m.add_attribute("FC_A", "name", "PEM Fuel Cell A")
fuel_cell = m.get_entity("FC_A")

# Reference port: H2 input (negative = withdrawal)
m.add_entity("ConversionPort", "port.FC_A.h2_in")
m.add_attribute("port.FC_A.h2_in", "port_direction", "input")
m.add_attribute("port.FC_A.h2_in", "flow_coefficient", -1.0)
m.add_attribute("port.FC_A.h2_in", "is_reference_port", True)
m.add_relation("port.FC_A.h2_in", "belongsToUnit", fuel_cell)
m.add_relation("port.FC_A.h2_in", "atNode", n_h2)
m.add_relation("port.FC_A.h2_in", "hasCarrier", h2)

# Electricity output port
m.add_entity("ConversionPort", "port.FC_A.elec_out")
m.add_attribute("port.FC_A.elec_out", "port_direction", "output")
m.add_attribute("port.FC_A.elec_out", "flow_coefficient", 0.55)
m.add_attribute("port.FC_A.elec_out", "maximum_output_power", 55.0)
m.add_relation("port.FC_A.elec_out", "belongsToUnit", fuel_cell)
m.add_relation("port.FC_A.elec_out", "atNode", n_e1)
m.add_relation("port.FC_A.elec_out", "hasCarrier", m.get_entity("Electricity"))

# Heat output port (identical shape, atNode=n_h1, hasCarrier=Heat) ...

# Operational parameters are held directly on the unit itself
m.add_relation("FC_A", "referencePort", "port.FC_A.h2_in")
```

`ConversionUnit`'s own dispatch attributes/relations (flattened
directly onto the asset, like every other asset class) only declare
dispatch participation and the reference port — port-level
coefficients and the `is_reference_port` flag define the conversion
ratios and reference scale. There's no composite builder for wiring up
a whole multi-port unit in one call; each port is created individually
with plain EAR calls, exactly the kind of "long tail" case the
low-level API exists for.

---

## Result

```
DemandUnit                2
GenerationUnit            2
TransmissionElement       2
ConversionUnit            1
StorageUnit               1

Model validated successfully.
```

---

## Run it yourself

```bash
python examples/example_simple.py
```
