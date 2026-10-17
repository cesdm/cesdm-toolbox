# Write models with the proxy API

The three calls `add_entity`, `add_attribute` and `add_relation` work everywhere and are what the tutorial adapters use. For your own scripts and notebooks, a CESDM model also offers a shorter, attribute-style way of writing the same thing: the **proxy API**. Both write the same entity; nothing is duplicated.

```python
from cesdm_toolbox import build_model_from_yaml

model = build_model_from_yaml("schemas/cesdm")
model.import_library("library/regions_library")
```

=== "Proxy API"

    ```python
    gen = model.add_entity("HydroGenerationUnit", "gen.CH_HYD_RES")
    gen.nominal_power_capacity = (8500, "MW")
    gen.belongsToGeographicalRegion = "region.country.CH"
    ```

=== "Core calls"

    ```python
    model.add_entity("HydroGenerationUnit", "gen.CH_HYD_RES")
    model.add_attribute("gen.CH_HYD_RES", "nominal_power_capacity", 8500, unit="MW")
    model.add_relation("gen.CH_HYD_RES", "belongsToGeographicalRegion", "region.country.CH")
    ```

`add_entity` returns a proxy: an object that behaves like the entity id (`gen == "gen.CH_HYD_RES"`) and exposes the schema's attributes and relations as Python attributes. `model.get_entity(id)` returns the proxy of an existing object.

## Writing

| Write | Proxy | Core call |
|---|---|---|
| a value with its unit | `gen.nominal_power_capacity = (8500, "MW")` | `add_attribute(..., 8500, unit="MW")` |
| a value without unit | `gen.turbine_efficiency = 0.9` | `add_attribute(..., 0.9)` |
| a link | `gen.drawsFromHydraulicStorage = basin` (a proxy or an id) | `add_relation(..., "storage.CH_RES")` |
| several at once | `gen.add_attribute("turbine_efficiency", 0.9).add_relation("drawsFromHydraulicStorage", "storage.CH_RES")` | — |

Pass the unit whenever the value has one. A bare number is taken in the schema's unit — `gen.nominal_power_capacity = 3` means 3 MW, whatever you had in mind.

## Reading

```python
gen.nominal_power_capacity            # 8500.0 — the value in the schema's unit
gen.belongsToGeographicalRegion       # the target, as a proxy: region.country.CH
```

For value, unit and source together, use `get_attr_value_unit_prov` from `ear` ([provenance](../concepts/energy-model.md#provenance)).

## Attribute groups

The schema sorts each class's attributes into [attribute groups](../concepts/schemas.md#attribute-groups). The proxy exposes them as namespaces, which keeps a large class readable and makes clear which analysis a value is for:

```python
gen.dispatch.nominal_power_capacity            # same value as gen.nominal_power_capacity
gen.topology.atNode                            # where it is connected

model = build_model_from_yaml("schemas/cesdm_power_flow")
gen = model.add_entity("GenerationUnit", "gen.CH_NUC")
gen.power_flow.active_power_setpoint = (3000, "MW")   # added by the power-flow package
```

A group added by an [extension package](../concepts/schemas.md#extending-without-forking) appears the same way, as soon as the package is loaded.

## Mistakes are refused

The proxy checks against the loaded schema just as the core calls do:

```text
gen.nominal_power_capacty = 1
AttributeError: 'nominal_power_capacty' is not an attribute or relation of 'HydroGenerationUnit'. Did you mean: nominal_power_capacity?

gen.nominal_power_capacity = (8.5, "GW")
ValueError: [HydroGenerationUnit:gen.CH_HYD_RES] Unit 'GW' is not allowed for 'nominal_power_capacity'. Allowed: ['MW']
```

Links to missing or wrong objects are reported by `model.validate()`, as always.

## Types in the editor

The proxies are generated from the schema (`cesdm/generated_proxies.py`), with type stubs in `typings/`, so an editor with a type checker (Pyright, Pylance) autocompletes attribute names and flags typos before you run anything. To narrow a looked-up object to its class:

```python
from cesdm.generated_proxies import HydroGenerationUnitProxy

gen = model.get_entity_as("gen.CH_HYD_RES", HydroGenerationUnitProxy)
```

After a schema change, regenerate the proxies and the stubs from the repository root:

```bash
python -m tools.generate_convenience_api   # cesdm/generated_proxies.py
python -m tools.generate_typings           # typings/
```

## Which one to use

| Use | For |
|---|---|
| the core calls | adapters, code that others read, anything generic — they work on any `ear` model, also outside CESDM |
| the proxy API | your own scripts and notebooks, exploring a model interactively |
