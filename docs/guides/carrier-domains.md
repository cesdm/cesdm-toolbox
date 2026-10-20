# Carrier domains

Use this page when your study involves more than electricity. It answers two questions: where a heat pump, a gas turbine or an electrolyser is attached, and whether you model the gas or heat network at all or only its supply. Both answers travel with the model: a group that receives a model with exogenous gas knows it cannot ask that model about gas flows.

## Where assets are attached

Electricity, gas, heat and hydrogen each move through their own infrastructure. In CESDM each of these is a **carrier domain**. Inside a domain, assets transport, inject, withdraw or store one carrier. Between domains, only **conversion units** move energy — a gas turbine, a heat pump, an electrolyser.

![Carrier domains linked by conversion units](../illustrations/carrier_domains.svg)

| Role | Classes | Attached with |
|---|---|---|
| Domain | `CarrierDomain` (`domain.electricity`, `domain.gas`, …) | — |
| Node in a domain | `ElectricalBus`, `GasBus`, `HeatBus`, `HydrogenBus` | `belongsToCarrierDomain` |
| Transport | `TransmissionLine`, `GenericInterconnector`, … | `fromNode` / `toNode`, or `fromRegion` / `toRegion` in a zonal model |
| One-port asset | `GenerationUnit`, `DemandUnit`, `StorageUnit`, `ExternalSupply`, … | `atNode`, or `belongsToGeographicalRegion` in a zonal model |
| Between domains | `CHPUnit`, `HeatPumpUnit`, `ElectrolyserUnit`, `BoilerUnit`, `FuelCellUnit`, … | one node per carrier, e.g. `atFuelNode`, `atElectricityNode`, `atHeatNode` |

A typed bus fixes its domain: an `ElectricalBus` always belongs to `domain.electricity`.

## Model a network, or only its supply

Not every carrier needs a network in your study. That is a choice of system boundary, not of physics.

=== "Endogenous"

    The domain's nodes and assets are part of the model.

    ![Gas and electricity networks both inside the boundary](../illustrations/domain_endogenous.svg)

=== "Exogenous"

    The carrier comes from outside the boundary; only the receiving side is modelled.

    ![External gas supply, electricity network inside the boundary](../illustrations/domain_exogenous.svg)

| Study | Gas or heat network? |
|---|---|
| Electricity-only capacity expansion | no — fuel is exogenous at gas and CHP units |
| Sector-coupled dispatch | often yes |
| European scenario, TYNDP-style | mixed |

When in doubt: electricity endogenous, everything else exogenous, and widen the boundary only when the study needs it.

## In code

A heat pump between an electricity bus and a heat bus, and gas taken as exogenous: no gas network, only a supply at the receiving bus.

```python
from cesdm_toolbox import build_model_from_yaml

model = build_model_from_yaml("cesdm/schemas/base")
model.import_library("cesdm/library/default_library")      # carriers and carrier domains

model.add_entity("ElectricalBus", "bus.elec")
model.add_relation("bus.elec", "belongsToCarrierDomain", "domain.electricity")
model.add_entity("HeatBus", "bus.heat")
model.add_relation("bus.heat", "belongsToCarrierDomain", "domain.heat")
model.add_entity("GasBus", "bus.gas")
model.add_relation("bus.gas", "belongsToCarrierDomain", "domain.gas")

# Between domains: one node per carrier
model.add_entity("HeatPumpUnit", "conv.heat_pump")
model.add_attribute("conv.heat_pump", "coefficient_of_performance", 3.5)
model.add_attribute("conv.heat_pump", "nominal_thermal_power_capacity", 25, unit="MW")
model.add_relation("conv.heat_pump", "atElectricityNode", "bus.elec")
model.add_relation("conv.heat_pump", "atHeatNode", "bus.heat")

# Exogenous gas: no gas network, only a supply at the receiving bus
model.add_entity("ExternalSupply", "supply.gas")
model.add_attribute("supply.gas", "supply_capacity", 200, unit="MW")
model.add_relation("supply.gas", "atNode", "bus.gas")

model.validate()    # []
```

To model the gas network itself, add its buses in `domain.gas` and connect them with `GenericInterconnector`. Keep `ExternalSupply` at the import points.

A worked multi-carrier example with heat pump, electrolyser, boiler, fuel cell and CHP: `examples/example_conversion_units.py`.
