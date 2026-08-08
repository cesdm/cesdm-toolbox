# `example_in_readme.py` — Step by Step

## Why this example matters

This is the complete lifecycle in one file — build, validate, export,
reload, explore, compute statistics — the shape almost every real
project follows. Steps 2–9 use core EAR calls plus the object-oriented
proxy layer; steps 13–15 deliberately switch to the generic, low-level
introspection API instead, since reading arbitrary, not-statically-known
fields across a *whole* model is genuinely a different job than typed
access to a *specific* known asset. Seeing both in one script shows
where each tool is the right one.

---

## Steps 2–6: Root entity, carriers, domain, region, buses

```python
model.add_entity("EnergySystemModel", "DEMO")
model.add_attribute("DEMO", "long_name", "Small CESDM demo system")

for carrier_id, name, co2, cost in [
    ("Electricity", "Electricity", 0.0, 0.0),
    ("Gas", "Gas", 0.20, 60.0),
]:
    model.ensure_carrier(carrier_id, name=name)
    carrier = model.get_entity(carrier_id)
    carrier.co2_emission_intensity = co2
    carrier.energy_carrier_cost = cost

model.add_entity("CarrierDomain", "ELEC")
model.add_attribute("ELEC", "name", "Electricity")
model.add_relation("ELEC", "hasCarrier", "Electricity")

model.add_entity("GeographicalRegion", "CH")
model.add_attribute("CH", "name", "Switzerland")

model.add_entity("ElectricalBus", "N_E1")
model.add_attribute("N_E1", "nominal_voltage", 220.0)
model.add_relation("N_E1", "locatedIn", "CH")
model.add_relation("N_E1", "belongsToCarrierDomain", "ELEC")
n_e1 = model.get_entity("N_E1")
n_e1.name = "Electricity node 1"
```

`model.ensure_carrier(carrier_id, name=...)` creates the `Carrier`
only if it doesn't already exist (some carriers may already come from
the default library) and returns it wrapped in a typed proxy directly
— `carrier.co2_emission_intensity = 0.20` can then be set directly, the
same "any id can become a proxy" pattern used throughout the
object-oriented layer.

## Steps 7–9: Generator, demand, interconnector

```python
model.add_entity("GenerationUnit", "GT_1")
model.add_relation("GT_1", "atNode", "N_E1")
model.add_relation("GT_1", "hasInputCarrier", "Gas")
model.add_relation("GT_1", "hasOutputCarrier", "Electricity")
gt_1 = model.get_entity("GT_1")
gt_1.dispatch.energy_conversion_efficiency = 0.50
gt_1.dispatch.nominal_power_capacity = 200.0

model.add_entity("DemandUnit", "LOAD_1")
model.add_relation("LOAD_1", "atNode", "N_E2")
load_1 = model.get_entity("LOAD_1")
load_1.dispatch.annual_energy_demand = 500_000.0

model.add_entity("Interconnector", "LINE_1")
model.add_attribute("LINE_1", "name", "Line between node 1 and node 2")
line_1 = model.get_entity("LINE_1")
line_1.connect(n_e1, n_e2)
line_1.power_flow.maximum_power_flow_from_to = 150.0
line_1.power_flow.maximum_power_flow_to_from = 150.0
```

## Step 10–12: Validate, export three ways, reload

```python
errors = model.validate()

model.export_yaml_hierarchical(output_dir / "demo_hierarchical.yaml")
model.export_yaml(output_dir / "demo_flat.yaml")
model.export_frictionless(output_dir / "frictionless", name="cesdm-readme-demo", title="CESDM README Demo Model")

loaded_model = build_model_from_yaml(schema_dir)
loaded_model.import_yaml_hierarchical(yaml_path)
```

Three export formats side by side from the same model: hierarchical
YAML (any remaining linked entities nested under their asset), flat
YAML, and a Frictionless Data Package — then the hierarchical one is
reloaded into a fresh model to confirm nothing was lost in translation.

---

## Steps 13–15: Generic exploration and statistics

This is the deliberately-not-proxy-API part. `entity.data` is the raw
attribute/relation dict for any entity, regardless of class:

```python
for class_name, entities in loaded_model.entities.items():
    for entity_id, entity in entities.items():
        for field_name, field_value in entity.data.items():
            print(f"{field_name}: {raw_value(field_value)}")
```

```
CarrierDomain
  - ELEC
      name: Electricity
      hasCarrier: Electricity

GenerationUnit
  - GT_1
      name: Gas turbine
      hasInputCarrier: Gas
      hasOutputCarrier: Electricity
...
```

Statistics are computed the same generic way — no `class_attributes()`
call, no knowledge of specific classes baked in, just field names read
directly off whatever's actually present. Since every asset class now
holds its own dispatch/topology attributes directly (the flattened
pattern — see
[`docs/guide/03_schemas.md`](../docs/guide/03_schemas.md)), most of this
reads straight off the entity itself; the `representsAsset`-based
fallback in the code is only there for any remaining linked entity
(e.g. a `Result`) that isn't the asset itself:

```python
capacity = get_field(entity, "nominal_power_capacity")
if capacity is not None and capacity_source is not None:
    energy_stats["generation_capacity_mw"] += capacity
    for carrier in as_list(get_field(capacity_source, "hasOutputCarrier")):
        energy_stats["capacity_by_carrier"][carrier] += capacity
```

```
Energy-system statistics
------------------------
Generation capacity:       200.0 MW
Annual demand:             500000.0 MWh/year
Transmission capacity:     150.0 MW
Topology nodes:            2
Topology branches:         1

Capacity by carrier
-------------------
Electricity: 200.0 MW

Demand by carrier
-----------------
Electricity: 500000.0 MWh/year
```

`node_to_carrier()` shows the same generic pattern used to infer a
demand's carrier: walk from the demand's `atNode` to its node, then
from the node to its `CarrierDomain`, then to that domain's carrier —
three hops, all through plain relation lookups, no energy-specific
shortcut anywhere.

---

## Run it yourself

```bash
python examples/example_in_readme.py
```
