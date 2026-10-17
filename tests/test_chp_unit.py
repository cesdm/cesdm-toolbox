from cesdm import build_model_from_yaml


def test_compact_chp_unit_schema_and_validation():
    m = build_model_from_yaml("schemas/cesdm")
    gas = m.add_entity(entity_class="Carrier", entity_id="carrier.fuel.fossil.gas.natural_gas")
    electricity = m.add_entity(entity_class="Carrier", entity_id="carrier.electricity")
    heat = m.add_entity(entity_class="Carrier", entity_id="carrier.heat")
    gas_domain = m.add_entity(entity_class="CarrierDomain", entity_id="domain.gas")
    gas_domain.add_relation(relation_id="hasCarrier", target_entity_id=gas.id)
    electricity_domain = m.add_entity(entity_class="CarrierDomain", entity_id="domain.electricity")
    electricity_domain.add_relation(relation_id="hasCarrier", target_entity_id=electricity.id)
    heat_domain = m.add_entity(entity_class="CarrierDomain", entity_id="domain.heat")
    heat_domain.add_relation(relation_id="hasCarrier", target_entity_id=heat.id)
    gas_bus = m.add_entity(entity_class="GasBus", entity_id="bus.gas.test")
    electricity_bus = m.add_entity(entity_class="ElectricalBus", entity_id="bus.electricity.test")
    heat_bus = m.add_entity(entity_class="HeatBus", entity_id="bus.heat.test")
    chp = m.add_entity(entity_class="CHPUnit", entity_id="chp.test")
    chp.add_attribute(attribute_id="nominal_electrical_power_capacity", value=35, unit="MW")
    chp.add_attribute(attribute_id="nominal_thermal_power_capacity", value=45, unit="MW")
    chp.add_attribute(attribute_id="electrical_efficiency", value=0.35, unit="fraction")
    chp.add_attribute(attribute_id="thermal_efficiency", value=0.45, unit="fraction")
    chp.add_relation(relation_id="hasInputCarrier", target_entity_id=gas.id)
    chp.add_relation(relation_id="atFuelNode", target_entity_id=gas_bus.id)
    chp.add_relation(relation_id="atElectricityNode", target_entity_id=electricity_bus.id)
    chp.add_relation(relation_id="atHeatNode", target_entity_id=heat_bus.id)
    assert m.get_relation_targets(chp.id, "hasElectricityOutputCarrier") == [electricity.id]
    assert m.get_relation_targets(chp.id, "hasHeatOutputCarrier") == [heat.id]
    assert m.validate() == []
