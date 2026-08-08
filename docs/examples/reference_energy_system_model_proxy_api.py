#!/usr/bin/env python3
"""
reference_energy_system_model_proxy_api.py

Build the CESDM tutorial model using the Proxy API — assign attributes and
relations on entity handles returned by model.add_entity(...).

Compact non-interactive equivalent of notebooks/building_your_cesdm_model.ipynb.
Run from the cesdm-toolbox repository root:

    python docs/examples/reference_energy_system_model_proxy_api.py
"""

from __future__ import annotations

from pathlib import Path
import sys


def repository_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in list(here.parents) + [Path.cwd(), *Path.cwd().parents]:
        if (candidate / "schemas" / "cesdm").exists():
            return candidate
    raise FileNotFoundError(
        "Could not locate the CESDM repository. Run this script from the "
        "repository root or from docs/examples/."
    )


_REPO_ROOT = repository_root()
sys.path.insert(0, str(_REPO_ROOT))

from cesdm_toolbox import build_model_from_yaml
from cesdm.default_library import GeneratorTypes, Carriers


def main() -> None:
    repo = _REPO_ROOT
    schema_dir = repo / "schemas" / "cesdm"
    library_dir = repo / "library" / "default_library"
    output_dir = repo / "output" / "reference_energy_system_model_proxy_api"

    model = build_model_from_yaml(str(schema_dir))
    model.import_library(str(library_dir))

    system = model.add_entity("EnergySystemModel", "CH_NEIGHBOURS_2030")
    system.long_name = "CH + neighbours multi-domain energy system, 2030"
    system.co2_price = 80.0

    electricity_domain = model.add_entity("CarrierDomain", "domain.electricity")
    electricity_domain.name = "Electricity"
    electricity_domain.hasCarrier = Carriers.CARRIER_ELECTRICITY

    countries = [
        ("region.ch", "Switzerland"),
        ("region.de", "Germany"),
        ("region.fr", "France"),
        ("region.it", "Italy"),
        ("region.at", "Austria"),
    ]
    for region_id, name in countries:
        region = model.add_entity("GeographicalRegion", region_id)
        region.name = name

    buses = [
        ("bus.ch", "region.ch", "Switzerland 380kV", 380.0, 47.0, 8.0),
        ("bus.de", "region.de", "Germany 380kV", 380.0, 51.0, 10.0),
        ("bus.fr", "region.fr", "France 400kV", 400.0, 46.0, 2.0),
        ("bus.it", "region.it", "Italy 380kV", 380.0, 42.0, 12.0),
        ("bus.at", "region.at", "Austria 380kV", 380.0, 47.5, 14.0),
    ]
    for bus_id, region_id, name, voltage_kv, latitude, longitude in buses:
        bus = model.add_entity("ElectricalBus", bus_id)
        bus.name = name
        bus.nominal_voltage = (voltage_kv, "kV")
        bus.latitude = latitude
        bus.longitude = longitude
        bus.locatedIn = model.get_entity(region_id)
        bus.belongsToCarrierDomain = electricity_domain

    demands = [
        ("dem.ch", "CH electricity demand", 60_000, "bus.ch"),
        ("dem.de", "DE electricity demand", 500_000, "bus.de"),
        ("dem.fr", "FR electricity demand", 450_000, "bus.fr"),
        ("dem.it", "IT electricity demand", 300_000, "bus.it"),
        ("dem.at", "AT electricity demand", 70_000, "bus.at"),
    ]
    for demand_id, name, annual_gwh, bus_id in demands:
        demand = model.add_entity("DemandUnit", demand_id)
        demand.name = name
        demand.annual_energy_demand = (annual_gwh * 1000, "MWh/year")
        demand.atNode = model.get_entity(bus_id)

    timestamps = model.add_entity("TimestampSeries", "ts.hourly.2030")
    timestamps.name = "Hourly, 2030"
    timestamps.start_datetime = "2030-01-01T00:00:00"
    timestamps.resolution = "PT1H"
    timestamps.length = 8760
    timestamps.timezone = "Europe/Zurich"

    generators = [
        (
            "gen.ch.gas",
            "CH Gas CCGT",
            GeneratorTypes.GENERATION_THERMAL_GAS_CCGT_NEW,
            3_000,
            "bus.ch",
            "thermal",
            None,
        ),
        (
            "gen.ch.nuc",
            "CH Nuclear",
            GeneratorTypes.GENERATION_THERMAL_NUCLEAR_STANDARD,
            2_000,
            "bus.ch",
            "nuclear",
            None,
        ),
        (
            "gen.ch.wind",
            "CH Wind",
            GeneratorTypes.GENERATION_RENEWABLE_WIND_ONSHORE,
            500,
            "bus.ch",
            "wind",
            900_000,
        ),
        (
            "gen.ch.solar",
            "CH Solar PV",
            GeneratorTypes.GENERATION_RENEWABLE_SOLAR_PV_UTILITY,
            2_000,
            "bus.ch",
            "solar",
            2_000_000,
        ),
    ]

    for (
        generator_id,
        name,
        technology_id,
        capacity_mw,
        bus_id,
        family,
        annual_mwh,
    ) in generators:
        generator = model.add_entity("GenerationUnit", generator_id)
        generator.name = name
        generator.nominal_power_capacity = (capacity_mw, "MW")
        generator.hasTechnology = technology_id
        generator.atNode = model.get_entity(bus_id)

        if family == "thermal":
            generator.hasInputCarrier = Carriers.CARRIER_FUEL_FOSSIL_GAS_NATURAL_GAS
        elif family == "wind":
            generator.hasInputResource = "resource.renewable.wind"
        elif family == "solar":
            generator.hasInputResource = "resource.renewable.solar"

        if annual_mwh is not None:
            generator.annual_resource_potential = annual_mwh

            profile_id = f"profile.{generator_id}.capacity_factor"
            profile = model.add_entity("Profile", profile_id)
            profile.profile_type = "as_capacity_factor"
            profile.profile_unit = "pu"
            profile.data_reference = f"/profiles/{profile_id}"
            profile.hasTimestampSeries = timestamps
            generator.hasAvailabilityProfile = profile

    reservoir_id = "storage.ch.hydro.reservoir"
    hydro_id = "gen.ch.hydro.reservoir"
    inflow_profile_id = f"profile.{reservoir_id}.inflow"

    reservoir = model.add_entity("ReservoirStorageUnit", reservoir_id)
    reservoir.name = "CH Alpine seasonal reservoir"
    reservoir.energy_storage_capacity = (8_800_000, "MWh")
    reservoir.annual_natural_inflow_energy = (20_000_000, "MWh/year")
    reservoir.storesResource = "resource.water"

    hydro = model.add_entity("HydroGenerationUnit", hydro_id)
    hydro.name = "CH Reservoir hydro turbines"
    hydro.machine_role = "turbine"
    hydro.nominal_power_capacity = (8_000, "MW")
    hydro.annual_resource_potential = 20_000_000
    hydro.hasTechnology = "Generation.Renewable.Hydro.Reservoir"
    hydro.hasInputResource = "resource.water"
    hydro.atNode = model.get_entity("bus.ch")
    hydro.drawsFromReservoir = reservoir
    reservoir.suppliesResourceTo = hydro

    inflow_profile = model.add_entity("Profile", inflow_profile_id)
    inflow_profile.profile_type = "as_normalized_annual_energy"
    inflow_profile.profile_unit = "pu"
    inflow_profile.data_reference = f"/profiles/{inflow_profile_id}"
    inflow_profile.hasTimestampSeries = timestamps
    reservoir.hasNaturalInflowProfile = inflow_profile

    interconnectors = [
        ("ntc.ch.de", "CH-DE NTC", "bus.ch", "bus.de", 6_000, 5_500),
        ("ntc.ch.fr", "CH-FR NTC", "bus.ch", "bus.fr", 4_000, 3_500),
        ("ntc.ch.it", "CH-IT NTC", "bus.ch", "bus.it", 5_000, 4_500),
        ("ntc.ch.at", "CH-AT NTC", "bus.ch", "bus.at", 2_000, 2_000),
    ]
    for (
        interconnector_id,
        name,
        from_bus,
        to_bus,
        capacity_from_to,
        capacity_to_from,
    ) in interconnectors:
        interconnector = model.add_entity("Interconnector", interconnector_id)
        interconnector.name = name
        interconnector.maximum_power_flow_from_to = (capacity_from_to, "MW")
        interconnector.maximum_power_flow_to_from = (capacity_to_from, "MW")
        interconnector.fromNode = model.get_entity(from_bus)
        interconnector.toNode = model.get_entity(to_bus)

    heat_carrier = model.add_entity("Carrier", "carrier.heat")
    heat_carrier.name = "Heat"

    domains = [
        (
            "domain.gas.ch",
            "Swiss gas domain",
            Carriers.CARRIER_FUEL_FOSSIL_GAS_NATURAL_GAS,
        ),
        (
            "domain.heat.ch",
            "Swiss heat domain",
            "carrier.heat",
        ),
    ]
    domain_entities = {}
    for domain_id, name, carrier_id in domains:
        domain = model.add_entity("CarrierDomain", domain_id)
        domain.name = name
        domain.hasCarrier = carrier_id
        domain_entities[domain_id] = domain

    region_ch = model.get_entity("region.ch")

    nodes = [
        ("GasBus", "bus.ch.gas", "Swiss gas bus", "domain.gas.ch"),
        ("HeatBus", "bus.ch.heat", "Swiss heat bus", "domain.heat.ch"),
    ]
    for entity_class, node_id, name, domain_id in nodes:
        node = model.add_entity(entity_class, node_id)
        node.name = name
        node.locatedIn = region_ch
        node.belongsToCarrierDomain = domain_entities[domain_id]

    gas_bus = model.get_entity("bus.ch.gas")
    electricity_bus = model.get_entity("bus.ch")
    heat_bus = model.get_entity("bus.ch.heat")

    gas_supply = model.add_entity("ExternalSupply", "supply.ch.gas")
    gas_supply.name = "Swiss gas import"
    gas_supply.supply_capacity = (10_000.0, "MW")
    gas_supply.is_slack = True
    gas_supply.hasOutputCarrier = Carriers.CARRIER_FUEL_FOSSIL_GAS_NATURAL_GAS
    gas_supply.atNode = gas_bus

    chp = model.add_entity("CHPUnit", "chp.ch")
    chp.name = "Swiss CHP plant"
    chp.nominal_electrical_power_capacity = (350.0, "MW")
    chp.nominal_thermal_power_capacity = (450.0, "MW")
    chp.electrical_efficiency = 0.35
    chp.thermal_efficiency = 0.45
    chp.total_efficiency = 0.80
    chp.power_to_heat_ratio = 350.0 / 450.0
    chp.hasInputCarrier = Carriers.CARRIER_FUEL_FOSSIL_GAS_NATURAL_GAS
    chp.hasElectricityOutputCarrier = Carriers.CARRIER_ELECTRICITY
    chp.hasHeatOutputCarrier = "carrier.heat"
    chp.atFuelNode = gas_bus
    chp.atElectricityNode = electricity_bus
    chp.atHeatNode = heat_bus

    heat_demand = model.add_entity("DemandUnit", "dem.ch.heat")
    heat_demand.name = "Swiss heat demand"
    heat_demand.annual_energy_demand = (20_000_000.0, "MWh/year")
    heat_demand.atNode = heat_bus

    errors = model.validate()
    if errors:
        print(f"{len(errors)} validation issue(s):")
        for error in errors[:20]:
            print(" -", error)
        raise SystemExit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    model.export_yaml_hierarchical(output_dir / "ch_neighbours_2030.yaml")
    model.export_frictionless(
        output_dir / "frictionless",
        name="ch-neighbours-2030",
        title="CH + Neighbours 2030 — CESDM tutorial model",
    )

    print("Model validated and exported successfully.")
    print(model.summary())


if __name__ == "__main__":
    main()
