# Reference Energy System Model Tutorial

This is the canonical executable example used throughout the CESDM documentation.

It builds a simplified 2030 system for Switzerland, Germany, France, Italy, and Austria. The first part represents the interconnected electricity system. The final step extends Switzerland with gas and heat domains and a CHP conversion unit.

## Why this example matters

The tutorial demonstrates the central CESDM idea: one common, schema-driven model can describe multiple infrastructures and support several downstream uses without redefining the same physical assets for every tool.

It covers:

- schema loading and reusable default libraries;
- entities, attributes, and relations;
- geographic regions and stable identifiers;
- carrier domains and typed network nodes;
- generation units and technology templates;
- demand, hydro reservoirs, and pumped storage;
- renewable and inflow profiles;
- cross-border interconnectors;
- multi-energy conversion through explicit ports;
- model exploration and statistics;
- structural validation;
- hierarchical YAML and Frictionless export.

## Tutorial stages

| Step | Model extension | Main CESDM concept |
|---|---|---|
| 0 | Load schema and library | Schema versus reusable master data |
| 1 | System and electricity domain | Containers, carriers, domains |
| 2 | CH, DE, FR, IT, AT | Geographic entities |
| 3 | One electricity bus per country | Typed nodes and spatial attributes |
| 4 | Electricity demand | Assets and dispatch attributes |
| 5 | Thermal, nuclear, wind, and solar fleet | Technology templates and defaults |
| 6 | Hydro portfolio | Storage and explicit asset relations |
| 7 | Cross-border NTC links | Two-node topology and directional limits |
| 8 | Gas and heat extension with CHP | Multi-energy domains and conversion ports |

## Recommended API style

The tutorial uses the schema-defined entity object API:

```python
bus = model.add_entity(
    entity_class="ElectricalBus",
    entity_id="bus.ch",
)

bus.add_attribute(
    attribute_id="nominal_voltage",
    value=380.0,
)
# Equivalent proxy syntax:
# bus.nominal_voltage = 380.0

bus.add_relation(
    relation_id="locatedIn",
    target_entity_id="region.ch",
)
# Equivalent proxy syntax:
# bus.spatial.locatedIn = "region.ch"
```

The explicit calls are valid for every schema-defined class. Proxy syntax provides a shorter, typed alternative over the same underlying data.

## Technology templates

The generator instance stores plant-specific values such as capacity and location. The linked technology entity provides reusable defaults:

```python
generator.add_relation(
    relation_id="hasTechnology",
    target_entity_id=GeneratorTypes.GENERATION_THERMAL_GAS_CCGT_NEW,
)
```

When a value such as efficiency is not set on the generator, CESDM can resolve it from the linked technology template.

## Multi-energy extension

Step 8 adds gas and heat domains to the Swiss part of the model:

```text
Gas Domain ──▶ CHP ──▶ Electricity Domain
                  └──▶ Heat Domain
```

The CHP is represented as a `ConversionUnit` with three explicit `ConversionPort` entities:

- gas input, coefficient `-1.0` and reference port;
- electricity output, coefficient `0.35`;
- heat output, coefficient `0.45`.

This same pattern supports heat pumps, electrolysers, fuel cells, power-to-gas plants, and other multi-input/multi-output conversions.

## Validation and export

The finished model is validated against the schemas and exported in two interoperable forms:

```python
errors = model.validate()
model.export_yaml_hierarchical("output/ch_neighbours_2030.yaml")
model.export_frictionless("output/frictionless", name="ch-neighbours-2030")
```

## Run it

```bash
python examples/reference_energy_system_model.py
```

The generated outputs are written to:

```text
output/tutorial_ch_neighbours/
```
