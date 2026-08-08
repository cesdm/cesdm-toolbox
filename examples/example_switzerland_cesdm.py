"""Simplified Switzerland example for CESDM.

Demonstrates regions, carriers, domains, nodes, generation, storage,
conversion, demand, transmission, profiles, validation, and export.

The exact required fields can differ between CESDM schema versions.
"""

from cesdm_toolbox import build_model_from_yaml


def build_switzerland_example():
    m = build_model_from_yaml(schema_path="schemas/cesdm")

    # ------------------------------------------------------------------
    # Regions
    # ------------------------------------------------------------------
    ch = m.add_entity(
        entity_class="GeographicalRegion",
        entity_id="region.ch",
    )
    ch.add_attribute(
        attribute_id="name",
        value="Switzerland",
    )

    zh = m.add_entity(
        entity_class="GeographicalRegion",
        entity_id="region.ch.zh",
    )
    zh.add_attribute(
        attribute_id="name",
        value="Zurich",
    )
    zh.add_relation(
        relation_id="isSubRegionOf",
        target_entity_id="region.ch",
    )
    # Equivalent proxy syntax:
    # zh.isSubRegionOf = "region.ch"

    vs = m.add_entity(
        entity_class="GeographicalRegion",
        entity_id="region.ch.vs",
    )
    vs.add_attribute(
        attribute_id="name",
        value="Valais",
    )
    vs.add_relation(
        relation_id="isSubRegionOf",
        target_entity_id="region.ch",
    )
    # Equivalent proxy syntax:
    # vs.isSubRegionOf = "region.ch"

    de = m.add_entity(
        entity_class="GeographicalRegion",
        entity_id="region.de",
    )
    de.add_attribute(
        attribute_id="name",
        value="Germany",
    )

    # ------------------------------------------------------------------
    # Carriers, resources, and domains
    # ------------------------------------------------------------------
    electricity = m.add_entity(
        entity_class="Carrier",
        entity_id="carrier.electricity",
    )
    electricity.add_attribute(
        attribute_id="name",
        value="Electricity",
    )

    heat = m.add_entity(
        entity_class="Carrier",
        entity_id="carrier.heat",
    )
    heat.add_attribute(
        attribute_id="name",
        value="Heat",
    )

    water = m.add_entity(
        entity_class="NaturalResource",
        entity_id="resource.water",
    )
    water.add_attribute(
        attribute_id="name",
        value="Water",
    )

    electricity_domain = m.add_entity(
        entity_class="CarrierDomain",
        entity_id="domain.ch.electricity",
    )
    electricity_domain.add_attribute(
        attribute_id="name",
        value="Swiss electricity system",
    )
    electricity_domain.add_relation(
        relation_id="hasCarrier",
        target_entity_id="carrier.electricity",
    )
    # Equivalent proxy syntax:
    # electricity_domain.hasCarrier = "carrier.electricity"

    heat_domain = m.add_entity(
        entity_class="CarrierDomain",
        entity_id="domain.zh.heat",
    )
    heat_domain.add_attribute(
        attribute_id="name",
        value="Zurich district heating system",
    )
    heat_domain.add_relation(
        relation_id="hasCarrier",
        target_entity_id="carrier.heat",
    )
    # Equivalent proxy syntax:
    # heat_domain.hasCarrier = "carrier.heat"

    # ------------------------------------------------------------------
    # Network nodes
    # ------------------------------------------------------------------
    bus_zh = m.add_entity(
        entity_class="ElectricalBus",
        entity_id="bus.ch.zh.380",
    )
    bus_zh.add_attribute(
        attribute_id="name",
        value="Zurich 380 kV bus",
    )
    bus_zh.add_attribute(
        attribute_id="nominal_voltage",
        value=380,
        unit="kV",
    )
    # Equivalent proxy syntax:
    # bus_zh.nominal_voltage = 380
    bus_zh.add_relation(
        relation_id="locatedIn",
        target_entity_id="region.ch.zh",
    )
    # Equivalent proxy syntax:
    # bus_zh.spatial.locatedIn = "region.ch.zh"
    bus_zh.add_relation(
        relation_id="belongsToCarrierDomain",
        target_entity_id="domain.ch.electricity",
    )
    # Equivalent proxy syntax:
    # bus_zh.belongsToCarrierDomain = "domain.ch.electricity"

    bus_vs = m.add_entity(
        entity_class="ElectricalBus",
        entity_id="bus.ch.vs.380",
    )
    bus_vs.add_attribute(
        attribute_id="name",
        value="Valais 380 kV bus",
    )
    bus_vs.add_attribute(
        attribute_id="nominal_voltage",
        value=380,
        unit="kV",
    )
    # Equivalent proxy syntax:
    # bus_vs.nominal_voltage = 380
    bus_vs.add_relation(
        relation_id="locatedIn",
        target_entity_id="region.ch.vs",
    )
    # Equivalent proxy syntax:
    # bus_vs.spatial.locatedIn = "region.ch.vs"
    bus_vs.add_relation(
        relation_id="belongsToCarrierDomain",
        target_entity_id="domain.ch.electricity",
    )
    # Equivalent proxy syntax:
    # bus_vs.belongsToCarrierDomain = "domain.ch.electricity"

    bus_de = m.add_entity(
        entity_class="ElectricalBus",
        entity_id="bus.de.south.380",
    )
    bus_de.add_attribute(
        attribute_id="name",
        value="Southern Germany 380 kV bus",
    )
    bus_de.add_attribute(
        attribute_id="nominal_voltage",
        value=380,
        unit="kV",
    )
    # Equivalent proxy syntax:
    # bus_de.nominal_voltage = 380
    bus_de.add_relation(
        relation_id="locatedIn",
        target_entity_id="region.de",
    )
    # Equivalent proxy syntax:
    # bus_de.spatial.locatedIn = "region.de"
    bus_de.add_relation(
        relation_id="belongsToCarrierDomain",
        target_entity_id="domain.ch.electricity",
    )
    # Equivalent proxy syntax:
    # bus_de.belongsToCarrierDomain = "domain.ch.electricity"

    heat_bus = m.add_entity(
        entity_class="HeatBus",
        entity_id="bus.zh.heat",
    )
    heat_bus.add_attribute(
        attribute_id="name",
        value="Zurich heat bus",
    )
    heat_bus.add_relation(
        relation_id="locatedIn",
        target_entity_id="region.ch.zh",
    )
    # Equivalent proxy syntax:
    # heat_bus.spatial.locatedIn = "region.ch.zh"
    heat_bus.add_relation(
        relation_id="belongsToCarrierDomain",
        target_entity_id="domain.zh.heat",
    )
    # Equivalent proxy syntax:
    # heat_bus.belongsToCarrierDomain = "domain.zh.heat"

    # ------------------------------------------------------------------
    # Transmission and cross-border exchange
    # ------------------------------------------------------------------
    line = m.add_entity(
        entity_class="TransmissionLine",
        entity_id="line.ch.vs.zh.380",
    )
    line.add_attribute(
        attribute_id="name",
        value="Valais-Zurich transmission line",
    )
    line.add_relation(
        relation_id="fromNode",
        target_entity_id="bus.ch.vs.380",
    )
    # Equivalent proxy syntax:
    # line.topology.fromNode = "bus.ch.vs.380"
    line.add_relation(
        relation_id="toNode",
        target_entity_id="bus.ch.zh.380",
    )
    # Equivalent proxy syntax:
    # line.topology.toNode = "bus.ch.zh.380"

    interconnector = m.add_entity(
        entity_class="Interconnector",
        entity_id="interconnector.ch.de",
    )
    interconnector.add_attribute(
        attribute_id="name",
        value="Switzerland-Germany interconnector",
    )
    interconnector.add_relation(
        relation_id="fromNode",
        target_entity_id="bus.ch.zh.380",
    )
    # Equivalent proxy syntax:
    # interconnector.topology.fromNode = "bus.ch.zh.380"
    interconnector.add_relation(
        relation_id="toNode",
        target_entity_id="bus.de.south.380",
    )
    # Equivalent proxy syntax:
    # interconnector.topology.toNode = "bus.de.south.380"
    interconnector.add_attribute(
        attribute_id="maximum_power_flow_from_to",
        value=1200,
        unit="MW",
    )
    # Equivalent proxy syntax:
    # interconnector.power_flow.maximum_power_flow_from_to = 1200
    interconnector.add_attribute(
        attribute_id="maximum_power_flow_to_from",
        value=1000,
        unit="MW",
    )
    # Equivalent proxy syntax:
    # interconnector.power_flow.maximum_power_flow_to_from = 1000

    # ------------------------------------------------------------------
    # Hydro generation and reservoir
    # ------------------------------------------------------------------
    reservoir = m.add_entity(
        entity_class="ReservoirStorageUnit",
        entity_id="storage.ch.vs.reservoir",
    )
    reservoir.add_attribute(
        attribute_id="name",
        value="Valais hydro reservoir",
    )
    reservoir.add_attribute(
        attribute_id="energy_storage_capacity",
        value=8000,
        unit="MWh",
    )
    # Equivalent proxy syntax:
    # reservoir.dispatch.energy_storage_capacity = 8000
    reservoir.add_relation(
        relation_id="storesResource",
        target_entity_id="resource.water",
    )
    # Equivalent proxy syntax:
    # reservoir.storesResource = "resource.water"

    hydro = m.add_entity(
        entity_class="HydroGenerationUnit",
        entity_id="gen.ch.vs.hydro",
    )
    hydro.add_attribute(
        attribute_id="name",
        value="Valais reservoir hydropower plant",
    )
    hydro.add_attribute(
        attribute_id="nominal_power_capacity",
        value=1200,
        unit="MW",
    )
    # Equivalent proxy syntax:
    # hydro.dispatch.nominal_power_capacity = 1200
    hydro.add_relation(
        relation_id="atNode",
        target_entity_id="bus.ch.vs.380",
    )
    # Equivalent proxy syntax:
    # hydro.topology.atNode = "bus.ch.vs.380"
    hydro.add_relation(
        relation_id="drawsFromReservoir",
        target_entity_id="storage.ch.vs.reservoir",
    )
    # Equivalent proxy syntax:
    # hydro.drawsFromReservoir = "storage.ch.vs.reservoir"

    # ------------------------------------------------------------------
    # Wind generation
    # ------------------------------------------------------------------
    wind = m.add_entity(
        entity_class="GenerationUnit",
        entity_id="gen.ch.zh.wind",
    )
    wind.add_attribute(
        attribute_id="name",
        value="Zurich wind generation",
    )
    wind.add_attribute(
        attribute_id="nominal_power_capacity",
        value=200,
        unit="MW",
    )
    # Equivalent proxy syntax:
    # wind.dispatch.nominal_power_capacity = 200
    wind.add_relation(
        relation_id="atNode",
        target_entity_id="bus.ch.zh.380",
    )
    # Equivalent proxy syntax:
    # wind.topology.atNode = "bus.ch.zh.380"

    # ------------------------------------------------------------------
    # Battery storage
    # ------------------------------------------------------------------
    battery = m.add_entity(
        entity_class="StorageUnit",
        entity_id="storage.ch.zh.battery",
    )
    battery.add_attribute(
        attribute_id="name",
        value="Zurich battery",
    )
    battery.add_attribute(
        attribute_id="energy_storage_capacity",
        value=400,
        unit="MWh",
    )
    # Equivalent proxy syntax:
    # battery.dispatch.energy_storage_capacity = 400
    battery.add_relation(
        relation_id="atNode",
        target_entity_id="bus.ch.zh.380",
    )
    # Equivalent proxy syntax:
    # battery.topology.atNode = "bus.ch.zh.380"
    battery.add_relation(
        relation_id="storesCarrier",
        target_entity_id="carrier.electricity",
    )
    # Equivalent proxy syntax:
    # battery.storesCarrier = "carrier.electricity"

    # ------------------------------------------------------------------
    # Electricity and heat demand
    # ------------------------------------------------------------------
    electricity_demand = m.add_entity(
        entity_class="DemandUnit",
        entity_id="demand.ch.zh.electricity",
    )
    electricity_demand.add_attribute(
        attribute_id="name",
        value="Zurich electricity demand",
    )
    electricity_demand.add_attribute(
        attribute_id="maximum_energy_demand",
        value=900,
        unit="MW",
    )
    # Equivalent proxy syntax:
    # electricity_demand.dispatch.maximum_energy_demand = 900
    electricity_demand.add_relation(
        relation_id="atNode",
        target_entity_id="bus.ch.zh.380",
    )
    # Equivalent proxy syntax:
    # electricity_demand.topology.atNode = "bus.ch.zh.380"

    heat_demand = m.add_entity(
        entity_class="DemandUnit",
        entity_id="demand.ch.zh.heat",
    )
    heat_demand.add_attribute(
        attribute_id="name",
        value="Zurich district heat demand",
    )
    heat_demand.add_attribute(
        attribute_id="maximum_energy_demand",
        value=300,
        unit="MW",
    )
    # Equivalent proxy syntax:
    # heat_demand.dispatch.maximum_energy_demand = 300
    heat_demand.add_relation(
        relation_id="atNode",
        target_entity_id="bus.zh.heat",
    )
    # Equivalent proxy syntax:
    # heat_demand.topology.atNode = "bus.zh.heat"

    # ------------------------------------------------------------------
    # Heat pump with explicit conversion ports
    # ------------------------------------------------------------------
    heat_pump = m.add_entity(
        entity_class="ConversionUnit",
        entity_id="conversion.ch.zh.heat_pump",
    )
    heat_pump.add_attribute(
        attribute_id="name",
        value="Zurich large-scale heat pump",
    )

    electricity_input = m.add_entity(
        entity_class="ConversionPort",
        entity_id="port.heat_pump.electricity_in",
    )
    electricity_input.add_attribute(
        attribute_id="port_direction",
        value="input",
    )
    # Equivalent proxy syntax:
    # electricity_input.port_direction = "input"
    electricity_input.add_attribute(
        attribute_id="flow_coefficient",
        value=-1.0,
    )
    # Equivalent proxy syntax:
    # electricity_input.flow_coefficient = -1.0
    electricity_input.add_relation(
        relation_id="belongsToUnit",
        target_entity_id="conversion.ch.zh.heat_pump",
    )
    # Equivalent proxy syntax:
    # electricity_input.belongsToUnit = "conversion.ch.zh.heat_pump"
    electricity_input.add_relation(
        relation_id="atNode",
        target_entity_id="bus.ch.zh.380",
    )
    # Equivalent proxy syntax:
    # electricity_input.topology.atNode = "bus.ch.zh.380"
    electricity_input.add_relation(
        relation_id="hasCarrier",
        target_entity_id="carrier.electricity",
    )
    # Equivalent proxy syntax:
    # electricity_input.hasCarrier = "carrier.electricity"

    heat_output = m.add_entity(
        entity_class="ConversionPort",
        entity_id="port.heat_pump.heat_out",
    )
    heat_output.add_attribute(
        attribute_id="port_direction",
        value="output",
    )
    # Equivalent proxy syntax:
    # heat_output.port_direction = "output"
    heat_output.add_attribute(
        attribute_id="flow_coefficient",
        value=3.5,
    )
    # Equivalent proxy syntax:
    # heat_output.flow_coefficient = 3.5
    heat_output.add_relation(
        relation_id="belongsToUnit",
        target_entity_id="conversion.ch.zh.heat_pump",
    )
    # Equivalent proxy syntax:
    # heat_output.belongsToUnit = "conversion.ch.zh.heat_pump"
    heat_output.add_relation(
        relation_id="atNode",
        target_entity_id="bus.zh.heat",
    )
    # Equivalent proxy syntax:
    # heat_output.topology.atNode = "bus.zh.heat"
    heat_output.add_relation(
        relation_id="hasCarrier",
        target_entity_id="carrier.heat",
    )
    # Equivalent proxy syntax:
    # heat_output.hasCarrier = "carrier.heat"

    # ------------------------------------------------------------------
    # Time series and profiles
    # ------------------------------------------------------------------
    timestamps = m.add_entity(
        entity_class="TimestampSeries",
        entity_id="ts.ch.2030.hourly",
    )
    timestamps.add_attribute(
        attribute_id="start_datetime",
        value="2030-01-01T00:00:00",
    )
    # Equivalent proxy syntax:
    # timestamps.start_datetime = "2030-01-01T00:00:00"
    timestamps.add_attribute(
        attribute_id="resolution",
        value="PT1H",
    )
    # Equivalent proxy syntax:
    # timestamps.resolution = "PT1H"
    timestamps.add_attribute(
        attribute_id="length",
        value=8760,
    )
    # Equivalent proxy syntax:
    # timestamps.length = 8760
    timestamps.add_attribute(
        attribute_id="timezone",
        value="Europe/Zurich",
    )
    # Equivalent proxy syntax:
    # timestamps.timezone = "Europe/Zurich"

    wind_profile = m.add_entity(
        entity_class="Profile",
        entity_id="profile.ch.zh.wind.2030",
    )
    wind_profile.add_attribute(
        attribute_id="profile_type",
        value="as_capacity_factor",
    )
    # Equivalent proxy syntax:
    # wind_profile.profile_type = "as_capacity_factor"
    wind_profile.add_attribute(
        attribute_id="profile_unit",
        value="p.u.",
    )
    # Equivalent proxy syntax:
    # wind_profile.profile_unit = "p.u."
    wind_profile.add_attribute(
        attribute_id="data_reference",
        value="profiles.h5:/profiles/profile.ch.zh.wind.2030/values",
    )
    # Equivalent proxy syntax:
    # wind_profile.data_reference = "profiles.h5:/profiles/profile.ch.zh.wind.2030/values"
    wind_profile.add_relation(
        relation_id="hasTimestampSeries",
        target_entity_id="ts.ch.2030.hourly",
    )
    # Equivalent proxy syntax:
    # wind_profile.hasTimestampSeries = "ts.ch.2030.hourly"
    wind.add_relation(
        relation_id="hasAvailabilityProfile",
        target_entity_id="profile.ch.zh.wind.2030",
    )
    # Equivalent proxy syntax:
    # wind.dispatch.hasAvailabilityProfile = "profile.ch.zh.wind.2030"

    demand_profile = m.add_entity(
        entity_class="Profile",
        entity_id="profile.ch.zh.demand.2030",
    )
    demand_profile.add_attribute(
        attribute_id="profile_type",
        value="as_normalized_annual_energy",
    )
    # Equivalent proxy syntax:
    # demand_profile.profile_type = "as_normalized_annual_energy"
    demand_profile.add_attribute(
        attribute_id="profile_unit",
        value="p.u.",
    )
    # Equivalent proxy syntax:
    # demand_profile.profile_unit = "p.u."
    demand_profile.add_attribute(
        attribute_id="data_reference",
        value="profiles.h5:/profiles/profile.ch.zh.demand.2030/values",
    )
    # Equivalent proxy syntax:
    # demand_profile.data_reference = "profiles.h5:/profiles/profile.ch.zh.demand.2030/values"
    demand_profile.add_relation(
        relation_id="hasTimestampSeries",
        target_entity_id="ts.ch.2030.hourly",
    )
    # Equivalent proxy syntax:
    # demand_profile.hasTimestampSeries = "ts.ch.2030.hourly"
    electricity_demand.add_relation(
        relation_id="hasDemandProfile",
        target_entity_id="profile.ch.zh.demand.2030",
    )
    # Equivalent proxy syntax:
    # electricity_demand.dispatch.hasDemandProfile = "profile.ch.zh.demand.2030"

    # ------------------------------------------------------------------
    # Validation and inspection
    # ------------------------------------------------------------------
    errors = m.validate()
    if errors:
        print("Structural validation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("The Switzerland example is structurally valid.")

    print(m.summary())

    # Optional:
    analysis_errors = m.validate_for_analysis("optimal_dispatch")
    m.export_yaml("switzerland_example.yaml")

    return m


if __name__ == "__main__":
    build_switzerland_example()
