# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

"""Typed buses fix belongsToCarrierDomain to a library entity."""

from pathlib import Path

import pytest

from cesdm.default_library import (
    CarrierDomains,
    Carriers,
    NaturalResources,
    StorageTypes,
)
from cesdm_toolbox import build_model_from_yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "cesdm" / "schemas" / "base"
LIBRARY = ROOT / "cesdm" / "library" / "default_library"


def _model_with_library():
    model = build_model_from_yaml(str(SCHEMA))
    model.import_library(str(LIBRARY))
    return model


def test_demand_unit_defaults_has_carrier_to_electricity():
    model = _model_with_library()
    demand = model.add_entity("DemandUnit", "dem.ch")
    assert model.get_relation_targets(demand, "hasCarrier") == [
        Carriers.CARRIER_ELECTRICITY
    ]
    demand.hasCarrier = Carriers.CARRIER_HEAT
    assert model.get_relation_targets(demand, "hasCarrier") == [
        Carriers.CARRIER_HEAT
    ]
    assert model.classes["DemandUnit"].relations["hasCarrier"].default == (
        "carrier.electricity"
    )


def test_electrical_bus_gets_electricity_domain():
    model = _model_with_library()
    bus = model.add_entity("ElectricalBus", "bus.ch")
    assert model.get_relation_targets(bus, "belongsToCarrierDomain") == [
        CarrierDomains.DOMAIN_ELECTRICITY
    ]
    assert model.validate() == []


def test_gas_heat_hydrogen_buses_get_matching_domains():
    model = _model_with_library()
    gas = model.add_entity("GasBus", "bus.gas")
    heat = model.add_entity("HeatBus", "bus.heat")
    h2 = model.add_entity("HydrogenBus", "bus.h2")
    assert model.get_relation_targets(gas, "belongsToCarrierDomain") == [
        CarrierDomains.DOMAIN_GAS
    ]
    assert model.get_relation_targets(heat, "belongsToCarrierDomain") == [
        CarrierDomains.DOMAIN_HEAT
    ]
    assert model.get_relation_targets(h2, "belongsToCarrierDomain") == [
        CarrierDomains.DOMAIN_HYDROGEN
    ]


def test_wrong_domain_assignment_is_rejected():
    model = _model_with_library()
    bus = model.add_entity("ElectricalBus", "bus.custom")
    with pytest.raises(ValueError, match="fixed"):
        bus.belongsToCarrierDomain = CarrierDomains.DOMAIN_GAS
    assert model.get_relation_targets(bus, "belongsToCarrierDomain") == [
        CarrierDomains.DOMAIN_ELECTRICITY
    ]


def test_other_domain_id_is_rejected():
    model = build_model_from_yaml(str(SCHEMA))
    carrier = model.add_entity("Carrier", "carrier.electricity.study")
    domain = model.add_entity("CarrierDomain", "domain.electricity.study")
    domain.hasCarrier = carrier
    bus = model.add_entity("ElectricalBus", "bus.study")
    with pytest.raises(ValueError, match="fixed"):
        bus.belongsToCarrierDomain = domain


def test_fixed_fills_when_predefined_entity_exists():
    model = build_model_from_yaml(str(SCHEMA))
    carrier = model.add_entity("Carrier", "carrier.electricity")
    domain = model.add_entity("CarrierDomain", "domain.electricity")
    domain.hasCarrier = carrier
    bus = model.add_entity("ElectricalBus", "bus.ch")
    assert model.get_relation_targets(bus, "belongsToCarrierDomain") == [
        "domain.electricity"
    ]


def test_fixed_target_comes_from_the_schema_class():
    model = build_model_from_yaml(str(SCHEMA))
    rdef = model.classes["ElectricalBus"].relations["belongsToCarrierDomain"]
    assert rdef.fixed == "domain.electricity"
    assert model.classes["GasBus"].relations["belongsToCarrierDomain"].fixed == "domain.gas"


def test_without_library_domain_relation_stays_required():
    model = build_model_from_yaml(str(SCHEMA))
    model.add_entity("ElectricalBus", "bus.orphan")
    errors = model.validate()
    assert any("belongsToCarrierDomain" in e for e in errors)


def test_generator_type_output_is_fixed_to_electricity():
    model = _model_with_library()
    tech = model.get_entity("Generation.Renewable.Wind.Onshore")
    assert model.get_relation_targets(tech, "hasOutputCarrier") == [
        Carriers.CARRIER_ELECTRICITY
    ]
    with pytest.raises(ValueError, match="fixed"):
        tech.hasOutputCarrier = Carriers.CARRIER_FUEL_FOSSIL_GAS_NATURAL_GAS


def test_heat_pump_carriers_are_fixed():
    model = _model_with_library()
    hp = model.add_entity("HeatPumpUnit", "hp.ch")
    assert model.get_relation_targets(hp, "hasInputCarrier") == [
        Carriers.CARRIER_ELECTRICITY
    ]
    assert model.get_relation_targets(hp, "hasHeatOutputCarrier") == [
        Carriers.CARRIER_HEAT
    ]
    with pytest.raises(ValueError, match="fixed"):
        hp.hasInputCarrier = Carriers.CARRIER_FUEL_FOSSIL_GAS_NATURAL_GAS


def test_library_technology_input_is_fixed():
    model = _model_with_library()
    ccgt = model.get_entity("Generation.Thermal.Gas.CCGT.New")
    assert model.get_relation_targets(ccgt, "hasInputCarrier") == [
        Carriers.CARRIER_FUEL_FOSSIL_GAS_NATURAL_GAS
    ]
    with pytest.raises(ValueError, match="fixed"):
        ccgt.hasInputCarrier = Carriers.CARRIER_FUEL_FOSSIL_COAL_HARD_COAL

    wind = model.get_entity("Generation.Renewable.Wind.Onshore")
    assert model.get_relation_targets(wind, "hasInputResource") == [
        NaturalResources.RESOURCE_RENEWABLE_WIND
    ]
    with pytest.raises(ValueError, match="fixed"):
        wind.hasInputResource = NaturalResources.RESOURCE_RENEWABLE_SOLAR


def test_plant_inherits_technology_fixed_relations():
    model = _model_with_library()
    gen = model.add_entity("GenerationUnit", "gen.ch.wind")
    gen.hasTechnology = "Generation.Renewable.Wind.Onshore"
    assert model.get_relation_targets(gen, "hasInputResource") == [
        NaturalResources.RESOURCE_RENEWABLE_WIND
    ]
    with pytest.raises(ValueError, match="fixed"):
        gen.hasInputResource = NaturalResources.RESOURCE_RENEWABLE_SOLAR

    ccgt = model.add_entity("GenerationUnit", "gen.ch.ccgt")
    ccgt.hasTechnology = "Generation.Thermal.Gas.CCGT.New"
    assert model.get_relation_targets(ccgt, "hasInputCarrier") == [
        Carriers.CARRIER_FUEL_FOSSIL_GAS_NATURAL_GAS
    ]
    with pytest.raises(ValueError, match="fixed"):
        ccgt.hasInputCarrier = Carriers.CARRIER_FUEL_FOSSIL_COAL_HARD_COAL


def test_library_domain_and_storage_carriers_are_fixed():
    model = _model_with_library()
    domain = model.get_entity(CarrierDomains.DOMAIN_ELECTRICITY)
    assert model.get_relation_targets(domain, "hasCarrier") == [
        Carriers.CARRIER_ELECTRICITY
    ]
    with pytest.raises(ValueError, match="fixed"):
        domain.hasCarrier = Carriers.CARRIER_HEAT

    battery = model.get_entity(StorageTypes.STORAGE_ELECTROCHEMICAL_BATTERY)
    assert model.get_relation_targets(battery, "hasCarrier") == [
        Carriers.CARRIER_ELECTRICITY
    ]
    with pytest.raises(ValueError, match="fixed"):
        battery.hasCarrier = Carriers.CARRIER_HEAT

