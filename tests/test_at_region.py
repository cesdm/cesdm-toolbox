"""Zonal assets attach with belongsToGeographicalRegion instead of an ElectricalBus."""

from pathlib import Path

from cesdm.default_library import Carriers, GeneratorTypes
from cesdm_toolbox import build_model_from_yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "cesdm"
LIBRARY = ROOT / "library" / "default_library"
REGIONS = ROOT / "library" / "regions_library"


def _zonal_model():
    model = build_model_from_yaml(str(SCHEMA))
    model.import_library(str(LIBRARY))
    model.import_library(str(REGIONS))
    return model


def test_demand_and_supply_attach_to_region_without_a_bus():
    model = _zonal_model()
    region = model.get_entity("region.country.CH")

    demand = model.add_entity("DemandUnit", "dem.ch")
    demand.annual_energy_demand = (60_000_000, "MWh/year")
    demand.belongsToGeographicalRegion = region

    supply = model.add_entity("ExternalSupply", "supply.ch.slack")
    supply.supply_capacity = (10_000, "MW")
    supply.is_slack = True
    supply.belongsToGeographicalRegion = region
    supply.hasOutputCarrier = Carriers.CARRIER_ELECTRICITY

    gen = model.add_entity("GenerationUnit", "gen.ch.wind")
    gen.nominal_power_capacity = (500, "MW")
    gen.hasTechnology = GeneratorTypes.GENERATION_RENEWABLE_WIND_ONSHORE
    gen.belongsToGeographicalRegion = region

    assert model.get_relation_targets(demand, "belongsToGeographicalRegion") == ["region.country.CH"]
    assert model.get_relation_targets(supply, "belongsToGeographicalRegion") == ["region.country.CH"]
    assert model.get_relation_targets(gen, "belongsToGeographicalRegion") == ["region.country.CH"]
    assert model.validate() == []
    assert "ElectricalBus" not in model.entities or not model.entities.get("ElectricalBus")


def test_dispatch_accepts_region_instead_of_at_node():
    model = _zonal_model()
    region = model.get_entity("region.country.CH")
    demand = model.add_entity("DemandUnit", "dem.ch")
    demand.annual_energy_demand = (60_000_000, "MWh/year")
    demand.belongsToGeographicalRegion = region
    demand.hasDemandProfile = model.add_entity("Profile", "profile.dem.ch")

    gen = model.add_entity("GenerationUnit", "gen.ch.ccgt")
    gen.nominal_power_capacity = (3000, "MW")
    gen.hasTechnology = GeneratorTypes.GENERATION_THERMAL_GAS_CCGT_NEW
    gen.belongsToGeographicalRegion = region

    errors = model.validate_for_analysis("optimal_dispatch")
    assert not any("atNode" in e for e in errors)


def test_zonal_ntc_uses_from_region_to_region():
    model = _zonal_model()
    ch = model.get_entity("region.country.CH")
    de = model.get_entity("region.country.DE")
    link = model.add_entity("GenericInterconnector", "ntc.ch.de")
    link.maximum_power_flow_from_to = (6000, "MW")
    link.maximum_power_flow_to_from = (5500, "MW")
    link.fromRegion = ch
    link.toRegion = de
    assert model.validate() == []
    assert not any("fromNode" in e for e in model.validate_for_analysis("optimal_dispatch"))
    assert not model.get_entities("ElectricalBus")
