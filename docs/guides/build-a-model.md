# Build a model directly

Most groups reach CESDM through an [adapter](write-an-adapter.md). If you start a new study without an existing representation, you can write CESDM directly. This uses the same calls as an adapter, and the same Swiss system as the [tutorial](../tutorial/index.md): 58 TWh/year of demand, gas, nuclear, wind, photovoltaics, reservoir hydro and run-of-river. The same steps, cell by cell, are in `notebooks/build_a_model.ipynb`.

## The tutorial system, written directly

Wind and photovoltaics have no conversion efficiency in that system, so the attribute is left unset. Reservoir and run-of-river are each a `HydroGenerationUnit` drawing from its own `HydraulicStorageUnit`. This page is a dispatch model, so it loads `schemas/cesdm`. A power-flow study loads `schemas/cesdm_power_flow`. A study that also needs machine models loads that folder together with `schemas/cesdm_dynamic`.

```python
from cesdm_toolbox import build_model_from_yaml

model = build_model_from_yaml("schemas/cesdm")         # the vocabulary
model.import_library("library/default_library")         # shared technologies, carriers
model.import_library("library/regions_library")         # countries and regions
CH = "region.country.CH"

model.add_entity("DemandUnit", "demand.CH")
model.add_relation("demand.CH", "belongsToGeographicalRegion", CH)
model.add_attribute("demand.CH", "annual_energy_demand", 58_000_000, unit="MWh/year")

model.add_entity("GenerationUnit", "gen.CH_GAS")
model.add_relation("gen.CH_GAS", "belongsToGeographicalRegion", CH)
model.add_attribute("gen.CH_GAS", "generator_technology_type", "ccgt")
model.add_attribute("gen.CH_GAS", "nominal_power_capacity", 400, unit="MW")
model.add_attribute("gen.CH_GAS", "energy_conversion_efficiency", 0.58, unit="fraction")
model.add_attribute("gen.CH_GAS", "variable_operating_cost", 45, unit="MU/MWh")

model.add_entity("GenerationUnit", "gen.CH_NUC")
model.add_relation("gen.CH_NUC", "belongsToGeographicalRegion", CH)
model.add_attribute("gen.CH_NUC", "generator_technology_type", "nuclear")
model.add_attribute("gen.CH_NUC", "nominal_power_capacity", 3000, unit="MW")
model.add_attribute("gen.CH_NUC", "energy_conversion_efficiency", 0.33, unit="fraction")
model.add_attribute("gen.CH_NUC", "variable_operating_cost", 9, unit="MU/MWh")

model.add_entity("WindGenerationUnit", "gen.CH_WIND")
model.add_relation("gen.CH_WIND", "belongsToGeographicalRegion", CH)
model.add_attribute("gen.CH_WIND", "generator_technology_type", "wind")
model.add_attribute("gen.CH_WIND", "nominal_power_capacity", 100, unit="MW")
model.add_attribute("gen.CH_WIND", "variable_operating_cost", 0, unit="MU/MWh")

model.add_entity("SolarGenerationUnit", "gen.CH_PV")
model.add_relation("gen.CH_PV", "belongsToGeographicalRegion", CH)
model.add_attribute("gen.CH_PV", "generator_technology_type", "solar")
model.add_attribute("gen.CH_PV", "nominal_power_capacity", 6500, unit="MW")
model.add_attribute("gen.CH_PV", "variable_operating_cost", 0, unit="MU/MWh")

model.add_entity("HydroGenerationUnit", "gen.CH_HYD_RES")
model.add_relation("gen.CH_HYD_RES", "belongsToGeographicalRegion", CH)
model.add_attribute("gen.CH_HYD_RES", "generator_technology_type", "reservoir_hydro")
model.add_attribute("gen.CH_HYD_RES", "nominal_power_capacity", 8500, unit="MW")
model.add_attribute("gen.CH_HYD_RES", "energy_conversion_efficiency", 0.9, unit="fraction")
model.add_attribute("gen.CH_HYD_RES", "variable_operating_cost", 0, unit="MU/MWh")
model.add_entity("HydraulicStorageUnit", "storage.CH_RES")
model.add_attribute("storage.CH_RES", "energy_storage_capacity", 8_800_000, unit="MWh")
model.add_attribute("storage.CH_RES", "annual_natural_inflow_energy", 20_000_000, unit="MWh/year")
model.add_relation("gen.CH_HYD_RES", "drawsFromHydraulicStorage", "storage.CH_RES")

model.add_entity("HydroGenerationUnit", "gen.CH_HYD_ROR")
model.add_relation("gen.CH_HYD_ROR", "belongsToGeographicalRegion", CH)
model.add_attribute("gen.CH_HYD_ROR", "generator_technology_type", "run_of_river")
model.add_attribute("gen.CH_HYD_ROR", "nominal_power_capacity", 4000, unit="MW")
model.add_attribute("gen.CH_HYD_ROR", "energy_conversion_efficiency", 0.9, unit="fraction")
model.add_attribute("gen.CH_HYD_ROR", "variable_operating_cost", 0, unit="MU/MWh")
model.add_entity("HydraulicStorageUnit", "storage.CH_ROR")
model.add_attribute("storage.CH_ROR", "energy_storage_capacity", 0, unit="MWh")
model.add_attribute("storage.CH_ROR", "annual_natural_inflow_energy", 16_000_000, unit="MWh/year")
model.add_relation("gen.CH_HYD_ROR", "drawsFromHydraulicStorage", "storage.CH_ROR")
```

The pattern is always the same: create an object of a known class, give it values with units, link it to other objects. This is a zonal model — assets belong to a region. A nodal model attaches them to an `ElectricalBus` with `atNode` instead.

## Check it

```python
model.validate()                                   # [] — correct CESDM
model.validate_for_analysis("optimal_dispatch")    # what an hourly dispatch still needs
```

The first check is analysis-independent: the model is correct CESDM and can be exchanged. The second is analysis-dependent: the `optimal_dispatch` profile shipped with the toolbox also asks, among other things, for hourly shapes of demand (`hasDemandProfile`) and inflow (`hasNaturalInflowProfile`). The model is correct, but not yet complete for an hourly dispatch. See [validation](../concepts/validation.md) and [time series](../concepts/energy-model.md#time-series).

Mistakes in units are caught when you make them:

```python
model.add_attribute("demand.CH", "annual_energy_demand", 58, unit="TWh")
# ValueError: [DemandUnit:demand.CH] Unit 'TWh' is not allowed for 'annual_energy_demand'. Allowed: ['MWh/year']
```

## Save it

```python
model.export_yaml("output/my_model.yaml")                 # flat EAR file
model.export_frictionless("output/frictionless/", name="my-model",
                          include_library="referenced")  # one CSV per class
```

Time series are stored in HDF5 next to the YAML; see [profiles](../concepts/energy-model.md#time-series).

## Going further

- Larger walk-throughs with profiles, interconnectors, gas and heat are in `notebooks/building_your_cesdm_model.ipynb`.
- A multi-carrier example with heat pumps, electrolysers and CHP is in `examples/example_conversion_units.py`; background in [carrier domains](../guides/carrier-domains.md).
- Every class and attribute is in the [schema reference](../reference/index.md).

??? note "Shorter syntax: the proxy API"
    `model.get_entity(id)` returns an object on which you can set values as attributes, with autocomplete in your editor. The core calls above (`add_entity`, `add_attribute`, `add_relation`) work everywhere and are what the adapters use. See [the proxy API](proxy-api.md).
