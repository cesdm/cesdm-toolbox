from cesdm import build_model_from_yaml


def _carrier_domain_bus(m, carrier_id, domain_id, bus_class, bus_id):
    carrier = m.add_entity(entity_class="Carrier", entity_id=carrier_id)
    domain = m.add_entity(entity_class="CarrierDomain", entity_id=domain_id)
    domain.add_relation(relation_id="hasCarrier", target_entity_id=carrier.id)
    bus = m.add_entity(entity_class=bus_class, entity_id=bus_id)
    return carrier, bus


def test_heat_pump_unit_schema_and_validation():
    m = build_model_from_yaml("schemas/cesdm")
    electricity, elec_bus = _carrier_domain_bus(
        m, "carrier.electricity", "domain.electricity", "ElectricalBus", "bus.electricity.hp",
    )
    heat, heat_bus = _carrier_domain_bus(
        m, "carrier.heat", "domain.heat", "HeatBus", "bus.heat.hp",
    )
    hp = m.add_entity(entity_class="HeatPumpUnit", entity_id="hp.test")
    hp.add_attribute(attribute_id="coefficient_of_performance", value=3.5)
    hp.add_attribute(attribute_id="nominal_thermal_power_capacity", value=10, unit="MW")
    hp.add_relation(relation_id="atElectricityNode", target_entity_id=elec_bus.id)
    hp.add_relation(relation_id="atHeatNode", target_entity_id=heat_bus.id)
    assert m.get_relation_targets(hp.id, "hasInputCarrier") == [electricity.id]
    assert m.get_relation_targets(hp.id, "hasHeatOutputCarrier") == [heat.id]
    assert m.get_relation_targets(hp.id, "atElectricityNode") == [elec_bus.id]
    assert m.validate() == []


def test_electrolyser_unit_schema_and_validation():
    m = build_model_from_yaml("schemas/cesdm")
    electricity, elec_bus = _carrier_domain_bus(
        m, "carrier.electricity", "domain.electricity", "ElectricalBus", "bus.electricity.el",
    )
    hydrogen, h2_bus = _carrier_domain_bus(
        m, "carrier.hydrogen", "domain.hydrogen", "HydrogenBus", "bus.hydrogen.el",
    )
    el = m.add_entity(entity_class="ElectrolyserUnit", entity_id="el.test")
    el.add_attribute(attribute_id="energy_conversion_efficiency", value=0.7, unit="fraction")
    el.add_attribute(attribute_id="nominal_electrical_power_capacity", value=50, unit="MW")
    el.add_relation(relation_id="atElectricityNode", target_entity_id=elec_bus.id)
    el.add_relation(relation_id="atHydrogenNode", target_entity_id=h2_bus.id)
    assert m.get_relation_targets(el.id, "hasInputCarrier") == [electricity.id]
    assert m.get_relation_targets(el.id, "hasHydrogenOutputCarrier") == [hydrogen.id]
    assert m.get_relation_targets(el.id, "atHydrogenNode") == [h2_bus.id]
    assert m.validate() == []


def test_boiler_unit_schema_and_validation():
    m = build_model_from_yaml("schemas/cesdm")
    gas, gas_bus = _carrier_domain_bus(
        m, "carrier.fuel.fossil.gas.natural_gas", "domain.gas", "GasBus", "bus.gas.boiler",
    )
    heat, heat_bus = _carrier_domain_bus(
        m, "carrier.heat", "domain.heat", "HeatBus", "bus.heat.boiler",
    )
    boiler = m.add_entity(entity_class="BoilerUnit", entity_id="boiler.test")
    boiler.add_attribute(attribute_id="thermal_efficiency", value=0.9, unit="fraction")
    boiler.add_attribute(attribute_id="nominal_thermal_power_capacity", value=20, unit="MW")
    boiler.add_relation(relation_id="hasInputCarrier", target_entity_id=gas.id)
    boiler.add_relation(relation_id="atFuelNode", target_entity_id=gas_bus.id)
    boiler.add_relation(relation_id="atHeatNode", target_entity_id=heat_bus.id)
    assert m.get_relation_targets(boiler.id, "hasHeatOutputCarrier") == [heat.id]
    assert m.get_relation_targets(boiler.id, "atFuelNode") == [gas_bus.id]
    assert m.validate() == []


def test_fuel_cell_unit_schema_and_validation():
    m = build_model_from_yaml("schemas/cesdm")
    hydrogen, h2_bus = _carrier_domain_bus(
        m, "carrier.hydrogen", "domain.hydrogen", "HydrogenBus", "bus.hydrogen.fc",
    )
    electricity, elec_bus = _carrier_domain_bus(
        m, "carrier.electricity", "domain.electricity", "ElectricalBus", "bus.electricity.fc",
    )
    heat, heat_bus = _carrier_domain_bus(
        m, "carrier.heat", "domain.heat", "HeatBus", "bus.heat.fc",
    )
    fc = m.add_entity(entity_class="FuelCellUnit", entity_id="fc.test")
    fc.add_attribute(attribute_id="electrical_efficiency", value=0.55, unit="fraction")
    fc.add_attribute(attribute_id="nominal_electrical_power_capacity", value=5, unit="MW")
    fc.add_attribute(attribute_id="nominal_thermal_power_capacity", value=2, unit="MW")
    fc.add_relation(relation_id="hasInputCarrier", target_entity_id=hydrogen.id)
    fc.add_relation(relation_id="hasHeatOutputCarrier", target_entity_id=heat.id)
    fc.add_relation(relation_id="atHydrogenNode", target_entity_id=h2_bus.id)
    fc.add_relation(relation_id="atElectricityNode", target_entity_id=elec_bus.id)
    fc.add_relation(relation_id="atHeatNode", target_entity_id=heat_bus.id)
    assert m.get_relation_targets(fc.id, "hasElectricityOutputCarrier") == [electricity.id]
    assert m.get_relation_targets(fc.id, "atHydrogenNode") == [h2_bus.id]
    assert m.validate() == []
