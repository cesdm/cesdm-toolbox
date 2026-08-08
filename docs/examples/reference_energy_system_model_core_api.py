#!/usr/bin/env python3
"""
reference_energy_system_model_core_api.py

Build the CESDM tutorial model using only the three core EAR operations
for model construction:

    model.add_entity(...)
    model.add_attribute(...)
    model.add_relation(...)

Schema loading, library import, validation, and export are separate workflow
operations and are intentionally retained.

Each major section also contains commented Proxy API equivalents. These
comments are educational only and are not executed.
"""

from __future__ import annotations

from pathlib import Path
import sys


def repository_root() -> Path:
    """Locate the repository from examples/, docs/examples/, or the working directory."""
    here = Path(__file__).resolve()
    candidates = list(here.parents) + [Path.cwd(), *Path.cwd().parents]
    for candidate in candidates:
        if (candidate / "schemas" / "cesdm").exists():
            return candidate
    raise FileNotFoundError(
        "Could not locate the repository. Run this script from the CESDM "
        "repository or place it under examples/ or docs/examples/."
    )


_REPO_ROOT = repository_root()
sys.path.insert(0, str(_REPO_ROOT))

from cesdm_toolbox import build_model_from_yaml
from cesdm.default_library import GeneratorTypes, Carriers


def main() -> None:
    repo = _REPO_ROOT
    schema_dir = repo / "schemas" / "cesdm"
    library_dir = repo / "library" / "default_library"
    output_dir = repo / "output" / "reference_energy_system_model_core_api"

    model = build_model_from_yaml(str(schema_dir))
    model.import_library(str(library_dir))

    # ------------------------------------------------------------------
    # 1. System container and electricity Carrier Domain
# Proxy API equivalent:
# system = model.add_entity("EnergySystemModel", "CH_NEIGHBOURS_2030")
# system.long_name = "CH + neighbours multi-domain energy system, 2030"
# system.co2_price = 80.0
#
# electricity_domain = model.add_entity(
#     "CarrierDomain",
#     "domain.electricity",
# )
# electricity_domain.name = "Electricity"
# electricity_domain.hasCarrier = Carriers.CARRIER_ELECTRICITY
    # ------------------------------------------------------------------
    model.add_entity(
        entity_class='EnergySystemModel',
        entity_id='CH_NEIGHBOURS_2030',
    )
    model.add_attribute(
        entity_id='CH_NEIGHBOURS_2030',
        attribute_id='long_name',
        value='CH + neighbours multi-domain energy system, 2030',
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id='CH_NEIGHBOURS_2030',
        attribute_id='co2_price',
        value=80.0,
        unit=None,
        provenance_ref=None,
    )

    model.add_entity(
        entity_class='CarrierDomain',
        entity_id='domain.electricity',
    )
    model.add_attribute(
        entity_id='domain.electricity',
        attribute_id='name',
        value='Electricity',
        unit=None,
        provenance_ref=None,
    )
    model.add_relation(
        entity_id='domain.electricity',
        relation_id='hasCarrier',
        target_entity_id=Carriers.CARRIER_ELECTRICITY,
    )

    # ------------------------------------------------------------------
    # 2. Geographic regions
# Proxy API equivalent:
# region = model.add_entity("GeographicalRegion", region_id)
# region.name = name
    # ------------------------------------------------------------------
    countries = [
        ("region.ch", "Switzerland"),
        ("region.de", "Germany"),
        ("region.fr", "France"),
        ("region.it", "Italy"),
        ("region.at", "Austria"),
    ]
    for region_id, name in countries:
        model.add_entity(
            entity_class='GeographicalRegion',
            entity_id=region_id,
        )
        model.add_attribute(
            entity_id=region_id,
            attribute_id='name',
            value=name,
            unit=None,
            provenance_ref=None,
        )

    # ------------------------------------------------------------------
    # 3. Electricity buses
    # Proxy API equivalent:
    # bus = model.add_entity("ElectricalBus", bus_id)
    # bus.name = name
    # bus.nominal_voltage = voltage_kv
    # bus.spatial.latitude = latitude
    # bus.spatial.longitude = longitude
    # bus.spatial.locatedIn = region
    # bus.belongsToCarrierDomain = electricity_domain
    # ------------------------------------------------------------------
    buses = [
        ("bus.ch", "region.ch", "Switzerland 380kV", 380.0, 47.0, 8.0),
        ("bus.de", "region.de", "Germany 380kV", 380.0, 51.0, 10.0),
        ("bus.fr", "region.fr", "France 400kV", 400.0, 46.0, 2.0),
        ("bus.it", "region.it", "Italy 380kV", 380.0, 42.0, 12.0),
        ("bus.at", "region.at", "Austria 380kV", 380.0, 47.5, 14.0),
    ]
    for bus_id, region_id, name, voltage_kv, latitude, longitude in buses:
        model.add_entity(
            entity_class='ElectricalBus',
            entity_id=bus_id,
        )
        model.add_attribute(
            entity_id=bus_id,
            attribute_id='name',
            value=name,
            unit=None,
            provenance_ref=None,
        )
        model.add_attribute(
            entity_id=bus_id,
            attribute_id='nominal_voltage',
            value=voltage_kv,
            unit=None,
            provenance_ref=None,
        )
        model.add_attribute(
            entity_id=bus_id,
            attribute_id='latitude',
            value=latitude,
            unit=None,
            provenance_ref=None,
        )
        model.add_attribute(
            entity_id=bus_id,
            attribute_id='longitude',
            value=longitude,
            unit=None,
            provenance_ref=None,
        )
        model.add_relation(
            entity_id=bus_id,
            relation_id='locatedIn',
            target_entity_id=region_id,
        )
        model.add_relation(
            entity_id=bus_id,
            relation_id='belongsToCarrierDomain',
            target_entity_id='domain.electricity',
        )

    # ------------------------------------------------------------------
    # 4. Electricity demand
    # Proxy API equivalent:
    # demand = model.add_entity("DemandUnit", demand_id)
    # demand.name = name
    # demand.dispatch.annual_energy_demand = annual_gwh * 1_000
    # demand.topology.atNode = bus
    # ------------------------------------------------------------------
    demands = [
        ("dem.ch", "CH electricity demand", 60_000, "bus.ch"),
        ("dem.de", "DE electricity demand", 500_000, "bus.de"),
        ("dem.fr", "FR electricity demand", 450_000, "bus.fr"),
        ("dem.it", "IT electricity demand", 300_000, "bus.it"),
        ("dem.at", "AT electricity demand", 70_000, "bus.at"),
    ]
    for demand_id, name, annual_gwh, bus_id in demands:
        model.add_entity(
            entity_class='DemandUnit',
            entity_id=demand_id,
        )
        model.add_attribute(
            entity_id=demand_id,
            attribute_id='name',
            value=name,
            unit=None,
            provenance_ref=None,
        )
        model.add_attribute(
            entity_id=demand_id,
            attribute_id='annual_energy_demand',
            value=annual_gwh * 1000,
            unit=None,
            provenance_ref=None,
        )
        model.add_relation(
            entity_id=demand_id,
            relation_id='atNode',
            target_entity_id=bus_id,
        )

    # ------------------------------------------------------------------
    # 5. Shared time axis
    # Proxy API equivalent:
    # timestamps = model.add_entity("TimestampSeries", "ts.hourly.2030")
    # timestamps.name = "Hourly, 2030"
    # timestamps.start_datetime = "2030-01-01T00:00:00"
    # timestamps.resolution = "PT1H"
    # timestamps.length = 8760
    # timestamps.timezone = "Europe/Zurich"
    #
    # Wind, solar, and water resources are already reusable entities in
    # the imported Default Library. The project model references them
    # directly and does not recreate them.
    # ------------------------------------------------------------------
    model.add_entity(
        entity_class='TimestampSeries',
        entity_id='ts.hourly.2030',
    )
    model.add_attribute(
        entity_id='ts.hourly.2030',
        attribute_id='name',
        value='Hourly, 2030',
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id='ts.hourly.2030',
        attribute_id='start_datetime',
        value='2030-01-01T00:00:00',
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id='ts.hourly.2030',
        attribute_id='resolution',
        value='PT1H',
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id='ts.hourly.2030',
        attribute_id='length',
        value=8760,
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id='ts.hourly.2030',
        attribute_id='timezone',
        value='Europe/Zurich',
        unit=None,
        provenance_ref=None,
    )

    # ------------------------------------------------------------------
    # 6. Generation fleet and explicit availability Profiles
    # Proxy API equivalent:
    # generator = model.add_entity("GenerationUnit", generator_id)
    # generator.name = name
    # generator.dispatch.nominal_power_capacity = capacity_mw
    # generator.hasTechnology = technology_id
    # generator.topology.atNode = bus
    #
    # if family == "thermal":
    #     generator.hasInputCarrier = (
    #         Carriers.CARRIER_FUEL_FOSSIL_GAS_NATURAL_GAS
    #     )
    # elif family == "wind":
    #     generator.hasInputResource = "resource.renewable.wind"
    # elif family == "solar":
    #     generator.hasInputResource = "resource.renewable.solar"
    #
    # profile = model.add_entity("Profile", profile_id)
    # profile.profile_type = "as_capacity_factor"
    # profile.profile_unit = "pu"
    # profile.data_reference = f"/profiles/{profile_id}"
    # profile.hasTimestampSeries = timestamps
    # generator.dispatch.hasAvailabilityProfile = profile
    # ------------------------------------------------------------------
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
        model.add_entity(
            entity_class='GenerationUnit',
            entity_id=generator_id,
        )
        model.add_attribute(
            entity_id=generator_id,
            attribute_id='name',
            value=name,
            unit=None,
            provenance_ref=None,
        )
        model.add_attribute(
            entity_id=generator_id,
            attribute_id='nominal_power_capacity',
            value=capacity_mw,
            unit=None,
            provenance_ref=None,
        )
        model.add_relation(
            entity_id=generator_id,
            relation_id='hasTechnology',
            target_entity_id=technology_id,
        )
        model.add_relation(
            entity_id=generator_id,
            relation_id='atNode',
            target_entity_id=bus_id,
        )

        if family == "thermal":
            model.add_relation(
                entity_id=generator_id,
                relation_id='hasInputCarrier',
                target_entity_id=Carriers.CARRIER_FUEL_FOSSIL_GAS_NATURAL_GAS,
            )
        elif family == "wind":
            model.add_relation(
                entity_id=generator_id,
                relation_id='hasInputResource',
                target_entity_id='resource.renewable.wind',
            )
        elif family == "solar":
            model.add_relation(
                entity_id=generator_id,
                relation_id='hasInputResource',
                target_entity_id='resource.renewable.solar',
            )

        if annual_mwh is not None:
            model.add_attribute(
                entity_id=generator_id,
                attribute_id='annual_resource_potential',
                value=annual_mwh,
                unit=None,
                provenance_ref=None,
            )

            profile_id = f"profile.{generator_id}.capacity_factor"
            model.add_entity(
                entity_class='Profile',
                entity_id=profile_id,
            )
            model.add_attribute(
                entity_id=profile_id,
                attribute_id='profile_type',
                value='as_capacity_factor',
                unit=None,
                provenance_ref=None,
            )
            model.add_attribute(
                entity_id=profile_id,
                attribute_id='profile_unit',
                value='pu',
                unit=None,
                provenance_ref=None,
            )
            model.add_attribute(
                entity_id=profile_id,
                attribute_id='data_reference',
                value=f'/profiles/{profile_id}',
                unit=None,
                provenance_ref=None,
            )
            model.add_relation(
                entity_id=profile_id,
                relation_id='hasTimestampSeries',
                target_entity_id='ts.hourly.2030',
            )
            model.add_relation(
                entity_id=generator_id,
                relation_id='hasAvailabilityProfile',
                target_entity_id=profile_id,
            )

    # ------------------------------------------------------------------
    # 7. Reservoir hydro with explicit storage and inflow Profile
    # Proxy API equivalent:
    # reservoir = model.add_entity(
    #     "ReservoirStorageUnit",
    #     reservoir_id,
    # )
    # reservoir.name = "CH Alpine seasonal reservoir"
    # reservoir.dispatch.energy_storage_capacity = 8_800_000
    # reservoir.dispatch.annual_natural_inflow_energy = 20_000_000
    # reservoir.storesResource = "resource.water"
    #
    # hydro = model.add_entity("HydroGenerationUnit", hydro_id)
    # hydro.name = "CH Reservoir hydro turbines"
    # hydro.dispatch.machine_role = "turbine"
    # hydro.dispatch.nominal_power_capacity = 8_000
    # hydro.drawsFromReservoir = reservoir
    # reservoir.suppliesResourceTo = hydro
    #
    # inflow_profile = model.add_entity("Profile", inflow_profile_id)
    # inflow_profile.profile_type = "as_normalized_annual_energy"
    # inflow_profile.profile_unit = "pu"
    # inflow_profile.data_reference = f"/profiles/{inflow_profile_id}"
    # inflow_profile.hasTimestampSeries = timestamps
    # reservoir.dispatch.hasNaturalInflowProfile = inflow_profile
    # ------------------------------------------------------------------
    reservoir_id = "storage.ch.hydro.reservoir"
    hydro_id = "gen.ch.hydro.reservoir"
    inflow_profile_id = f"profile.{reservoir_id}.inflow"

    model.add_entity(
        entity_class='ReservoirStorageUnit',
        entity_id=reservoir_id,
    )
    model.add_attribute(
        entity_id=reservoir_id,
        attribute_id='name',
        value='CH Alpine seasonal reservoir',
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id=reservoir_id,
        attribute_id='energy_storage_capacity',
        value=8800000,
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id=reservoir_id,
        attribute_id='annual_natural_inflow_energy',
        value=20000000,
        unit=None,
        provenance_ref=None,
    )
    model.add_relation(
        entity_id=reservoir_id,
        relation_id='storesResource',
        target_entity_id='resource.water',
    )

    model.add_entity(
        entity_class='HydroGenerationUnit',
        entity_id=hydro_id,
    )
    model.add_attribute(
        entity_id=hydro_id,
        attribute_id='name',
        value='CH Reservoir hydro turbines',
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id=hydro_id,
        attribute_id='machine_role',
        value='turbine',
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id=hydro_id,
        attribute_id='nominal_power_capacity',
        value=8000,
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id=hydro_id,
        attribute_id='annual_resource_potential',
        value=20000000,
        unit=None,
        provenance_ref=None,
    )
    model.add_relation(
        entity_id=hydro_id,
        relation_id='hasTechnology',
        target_entity_id='Generation.Renewable.Hydro.Reservoir',
    )
    model.add_relation(
        entity_id=hydro_id,
        relation_id='hasInputResource',
        target_entity_id='resource.water',
    )
    model.add_relation(
        entity_id=hydro_id,
        relation_id='atNode',
        target_entity_id='bus.ch',
    )
    model.add_relation(
        entity_id=hydro_id,
        relation_id='drawsFromReservoir',
        target_entity_id=reservoir_id,
    )
    model.add_relation(
        entity_id=reservoir_id,
        relation_id='suppliesResourceTo',
        target_entity_id=hydro_id,
    )

    model.add_entity(
        entity_class='Profile',
        entity_id=inflow_profile_id,
    )
    model.add_attribute(
        entity_id=inflow_profile_id,
        attribute_id='profile_type',
        value='as_normalized_annual_energy',
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id=inflow_profile_id,
        attribute_id='profile_unit',
        value='pu',
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id=inflow_profile_id,
        attribute_id='data_reference',
        value=f'/profiles/{inflow_profile_id}',
        unit=None,
        provenance_ref=None,
    )
    model.add_relation(
        entity_id=inflow_profile_id,
        relation_id='hasTimestampSeries',
        target_entity_id='ts.hourly.2030',
    )
    model.add_relation(
        entity_id=reservoir_id,
        relation_id='hasNaturalInflowProfile',
        target_entity_id=inflow_profile_id,
    )

    # ------------------------------------------------------------------
    # 8. Cross-border interconnectors
# Proxy API equivalent:
# interconnector = model.add_entity("Interconnector", interconnector_id)
# interconnector.name = name
# interconnector.power_flow.maximum_power_flow_from_to = capacity_from_to
# interconnector.power_flow.maximum_power_flow_to_from = capacity_to_from
# interconnector.topology.fromNode = from_bus
# interconnector.topology.toNode = to_bus
    # ------------------------------------------------------------------
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
        model.add_entity(
            entity_class='Interconnector',
            entity_id=interconnector_id,
        )
        model.add_attribute(
            entity_id=interconnector_id,
            attribute_id='name',
            value=name,
            unit=None,
            provenance_ref=None,
        )
        model.add_attribute(
            entity_id=interconnector_id,
            attribute_id='maximum_power_flow_from_to',
            value=capacity_from_to,
            unit=None,
            provenance_ref=None,
        )
        model.add_attribute(
            entity_id=interconnector_id,
            attribute_id='maximum_power_flow_to_from',
            value=capacity_to_from,
            unit=None,
            provenance_ref=None,
        )
        model.add_relation(
            entity_id=interconnector_id,
            relation_id='fromNode',
            target_entity_id=from_bus,
        )
        model.add_relation(
            entity_id=interconnector_id,
            relation_id='toNode',
            target_entity_id=to_bus,
        )

    # ------------------------------------------------------------------
    # 9. Gas and heat domains
    # Proxy API equivalent:
    # heat_carrier = model.add_entity("Carrier", "carrier.heat")
    # heat_carrier.name = "Heat"
    #
    # domain = model.add_entity("CarrierDomain", domain_id)
    # domain.name = name
    # domain.hasCarrier = carrier
    #
    # gas_bus = model.add_entity("GasBus", "bus.ch.gas")
    # gas_bus.name = "Swiss gas bus"
    # gas_bus.locatedIn = region_ch
    # gas_bus.belongsToCarrierDomain = gas_domain
    # ------------------------------------------------------------------
    model.add_entity(
        entity_class='Carrier',
        entity_id='carrier.heat',
    )
    model.add_attribute(
        entity_id='carrier.heat',
        attribute_id='name',
        value='Heat',
        unit=None,
        provenance_ref=None,
    )

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
    for domain_id, name, carrier_id in domains:
        model.add_entity(
            entity_class='CarrierDomain',
            entity_id=domain_id,
        )
        model.add_attribute(
            entity_id=domain_id,
            attribute_id='name',
            value=name,
            unit=None,
            provenance_ref=None,
        )
        model.add_relation(
            entity_id=domain_id,
            relation_id='hasCarrier',
            target_entity_id=carrier_id,
        )

    nodes = [
        (
            "GasBus",
            "bus.ch.gas",
            "Swiss gas bus",
            "domain.gas.ch",
        ),
        (
            "HeatBus",
            "bus.ch.heat",
            "Swiss heat bus",
            "domain.heat.ch",
        ),
    ]
    for entity_class, node_id, name, domain_id in nodes:
        model.add_entity(
            entity_class=entity_class,
            entity_id=node_id,
        )
        model.add_attribute(
            entity_id=node_id,
            attribute_id='name',
            value=name,
            unit=None,
            provenance_ref=None,
        )
        model.add_relation(
            entity_id=node_id,
            relation_id='locatedIn',
            target_entity_id='region.ch',
        )
        model.add_relation(
            entity_id=node_id,
            relation_id='belongsToCarrierDomain',
            target_entity_id=domain_id,
        )

    # ------------------------------------------------------------------
    # 10. Gas supply, CHP conversion, and heat demand
    # Proxy API equivalent:
    # gas_supply = model.add_entity("ExternalSupply", "supply.ch.gas")
    # gas_supply.name = "Swiss gas import"
    # gas_supply.dispatch.supply_capacity = 10_000.0
    # gas_supply.dispatch.is_slack = True
    # gas_supply.hasOutputCarrier = natural_gas
    # gas_supply.topology.atNode = gas_bus
    #
    # chp = model.add_entity("CHPUnit", "chp.ch")
    # chp.name = "Swiss CHP plant"
    # chp.dispatch.nominal_electrical_power_capacity = 350.0
    # chp.dispatch.nominal_thermal_power_capacity = 450.0
    # chp.dispatch.electrical_efficiency = 0.35
    # chp.dispatch.thermal_efficiency = 0.45
    # chp.technical.total_efficiency = 0.80
    # chp.technical.power_to_heat_ratio = 350.0 / 450.0
    # chp.hasInputCarrier = natural_gas
    # chp.hasElectricityOutputCarrier = electricity
    # chp.hasHeatOutputCarrier = heat_carrier
    # chp.topology.atFuelNode = gas_bus
    # chp.topology.atElectricityNode = electricity_bus
    # chp.topology.atHeatNode = heat_bus
    # ------------------------------------------------------------------
    model.add_entity(
        entity_class='ExternalSupply',
        entity_id='supply.ch.gas',
    )
    model.add_attribute(
        entity_id='supply.ch.gas',
        attribute_id='name',
        value='Swiss gas import',
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id='supply.ch.gas',
        attribute_id='supply_capacity',
        value=10000.0,
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id='supply.ch.gas',
        attribute_id='is_slack',
        value=True,
        unit=None,
        provenance_ref=None,
    )
    model.add_relation(
        entity_id='supply.ch.gas',
        relation_id='hasOutputCarrier',
        target_entity_id=Carriers.CARRIER_FUEL_FOSSIL_GAS_NATURAL_GAS,
    )
    model.add_relation(
        entity_id='supply.ch.gas',
        relation_id='atNode',
        target_entity_id='bus.ch.gas',
    )

    model.add_entity(
        entity_class='CHPUnit',
        entity_id='chp.ch',
    )
    chp_attributes = {
        "name": "Swiss CHP plant",
        "nominal_electrical_power_capacity": 350.0,
        "nominal_thermal_power_capacity": 450.0,
        "electrical_efficiency": 0.35,
        "thermal_efficiency": 0.45,
        "total_efficiency": 0.80,
        "power_to_heat_ratio": 350.0 / 450.0,
    }
    for attribute_id, value in chp_attributes.items():
        model.add_attribute(
            entity_id='chp.ch',
            attribute_id=attribute_id,
            value=value,
            unit=None,
            provenance_ref=None,
        )

    chp_relations = {
        "hasInputCarrier": (
            Carriers.CARRIER_FUEL_FOSSIL_GAS_NATURAL_GAS
        ),
        "hasElectricityOutputCarrier": Carriers.CARRIER_ELECTRICITY,
        "hasHeatOutputCarrier": "carrier.heat",
        "atFuelNode": "bus.ch.gas",
        "atElectricityNode": "bus.ch",
        "atHeatNode": "bus.ch.heat",
    }
    for relation_id, target_id in chp_relations.items():
        model.add_relation(
            entity_id='chp.ch',
            relation_id=relation_id,
            target_entity_id=target_id,
        )

    model.add_entity(
        entity_class='DemandUnit',
        entity_id='dem.ch.heat',
    )
    model.add_attribute(
        entity_id='dem.ch.heat',
        attribute_id='name',
        value='Swiss heat demand',
        unit=None,
        provenance_ref=None,
    )
    model.add_attribute(
        entity_id='dem.ch.heat',
        attribute_id='annual_energy_demand',
        value=20000000.0,
        unit=None,
        provenance_ref=None,
    )
    model.add_relation(
        entity_id='dem.ch.heat',
        relation_id='atNode',
        target_entity_id='bus.ch.heat',
    )

    # ------------------------------------------------------------------
    # 11. Validate and export
    # ------------------------------------------------------------------
    errors = model.validate()
    if errors:
        print(f"{len(errors)} validation issue(s):")
        for error in errors[:20]:
            print(" -", error)
        raise SystemExit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    model.export_yaml_hierarchical(
        output_dir / "ch_neighbours_2030.yaml",
    )
    model.export_frictionless(
        output_dir / "frictionless",
        name="ch-neighbours-2030",
        title="CH + Neighbours 2030 — CESDM tutorial model",
    )

    print("Model validated and exported successfully.")
    print(model.summary())


if __name__ == "__main__":
    main()
