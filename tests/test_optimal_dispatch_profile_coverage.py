"""
Regression tests for the optimal_dispatch analysis profile's expanded
coverage: DemandUnit, WindGenerationUnit/SolarGenerationUnit/
HydroGenerationUnit resource profiles, StorageUnit/ReservoirStorageUnit,
and every TransmissionElement subclass, on top of the original
GenerationUnit/TransmissionLine-only checks.

Two real domain gaps were found and fixed while writing these checks,
plus a schema-level redesign that superseded the first one:

1. ReservoirStorageUnit was originally a StorageUnit subclass, but
   deliberately had no atNode, maximum_charging_power/
   maximum_discharging_power, or charging_efficiency/
   discharging_efficiency of its own -- those live on its paired
   HydroGenerationUnit instead. A first version of this profile
   required them at the shared StorageUnit level, which would have
   flagged every reservoir in a model as incomplete, so they were
   `required: false` there as a compromise. ReservoirStorageUnit is now
   a standalone class (not a StorageUnit subclass at all -- see
   schemas/cesdm/.../ReservoirStorageUnit.yaml for the full reasoning:
   a battery is one physical device that both stores and converts
   energy, while a reservoir is only the water vessel, with the
   power-conversion machinery a separate physical asset). That removes
   the conflict entirely: the StorageUnit block below now requires
   every one of those fields for real (a genuine battery-style
   StorageUnit needs all of them), and ReservoirStorageUnit has its own
   block with only what actually applies to it, confirmed directly
   against both a battery-style StorageUnit and a ReservoirStorageUnit
   below.

2. DemandUnit's dispatch-readiness comes from annual_energy_demand (the
   energy budget) plus hasDemandProfile (its temporal shape) -- not
   maximum_energy_demand, which only bounds the peak and says nothing
   about the total energy consumed. Wind, solar, and run-of-river hydro
   are resource-driven the same way: annual_resource_potential plus a
   profile (hasAvailabilityProfile / hasRunOfRiverInflowProfile), not a
   freely dispatchable nominal_power_capacity alone. HydroGenerationUnit
   covers both run-of-river and reservoir/PHS-coupled hydro, and a
   profile check can't tell which one a given entity is from its class
   alone -- so its resource-profile fields stay required: false (value-
   checked if set) rather than incorrectly demanding them on
   reservoir-coupled hydro too, mirroring the ReservoirStorageUnit fix.

3. ReservoirStorageUnit's inflow co-requirement (see #1) first used
   `when: {attribute_set: annual_natural_inflow_energy}` to decide
   whether hasNaturalInflowProfile is required. That's wrong: the
   schema itself documents that a closed-loop PHS reservoir may "leave
   annual_natural_inflow_energy unset OR ZERO" -- attribute_set treats
   an explicit 0 as "set" (it isn't None/""/[]), so an explicitly-zero
   reservoir was incorrectly flagged as needing a profile too. Fixed
   with `attribute_compare: {attribute: ..., operator: ">", value: 0}`
   instead, which correctly treats "unset" and "explicitly zero" the
   same way -- confirmed directly below.
"""
import pytest

from cesdm_toolbox import build_model_from_yaml


def _model():
    model = build_model_from_yaml("schemas/cesdm")
    model.add_entity("ElectricalBus", "bus.1")
    model.add_entity("ElectricalBus", "bus.2")
    return model


def test_demand_unit_requires_atnode_annual_energy_demand_and_profile():
    model = _model()
    model.add_entity("DemandUnit", "dem.bare")

    errors = model.validate_for_analysis("optimal_dispatch")
    assert any("dem.bare" in e and "atNode" in e for e in errors)
    assert any("dem.bare" in e and "annual_energy_demand" in e for e in errors)
    assert any("dem.bare" in e and "hasDemandProfile" in e for e in errors)


def test_demand_unit_maximum_energy_demand_alone_is_not_enough():
    """maximum_energy_demand only bounds the peak -- annual_energy_demand
    (the actual energy budget) and hasDemandProfile (its temporal
    shape) are what a dispatch study needs, not the peak alone."""
    model = _model()
    dem = model.add_entity("DemandUnit", "dem.1")
    dem.atNode = "bus.1"
    dem.dispatch.maximum_energy_demand = 250

    errors = model.validate_for_analysis("optimal_dispatch")
    assert any("dem.1" in e and "annual_energy_demand" in e for e in errors)
    assert any("dem.1" in e and "hasDemandProfile" in e for e in errors)


def test_demand_unit_passes_once_populated():
    model = _model()
    model.add_entity("TimestampSeries", "ts.1")
    profile = model.add_entity("Profile", "profile.dem.1")
    profile.add_relation(relation_id="hasTimestampSeries", target_entity_id="ts.1")

    dem = model.add_entity("DemandUnit", "dem.1")
    dem.atNode = "bus.1"
    dem.dispatch.annual_energy_demand = 1_200_000
    dem.add_relation(relation_id="hasDemandProfile", target_entity_id="profile.dem.1")

    errors = model.validate_for_analysis("optimal_dispatch")
    assert not any("dem.1" in e for e in errors)


def test_wind_and_solar_require_availability_profile_and_resource_potential():
    model = _model()
    model.add_entity("WindGenerationUnit", "wind.bare")
    model.add_entity("SolarGenerationUnit", "solar.bare")

    errors = model.validate_for_analysis("optimal_dispatch")
    for eid in ("wind.bare", "solar.bare"):
        assert any(eid in e and "hasAvailabilityProfile" in e for e in errors)
        assert any(eid in e and "annual_resource_potential" in e for e in errors)


def test_wind_passes_once_profile_and_resource_potential_are_set():
    model = _model()
    model.add_entity("TimestampSeries", "ts.1")
    profile = model.add_entity("Profile", "profile.wind.1")
    profile.add_relation(relation_id="hasTimestampSeries", target_entity_id="ts.1")

    wind = model.add_entity("WindGenerationUnit", "wind.1")
    wind.atNode = "bus.1"
    wind.add_relation(relation_id="hasTechnology", target_entity_id="Generation.Renewable.Wind.Onshore")
    wind.dispatch.nominal_power_capacity = 100
    wind.dispatch.variable_operating_cost = 0
    wind.dispatch.annual_resource_potential = 250_000
    wind.add_relation(relation_id="hasAvailabilityProfile", target_entity_id="profile.wind.1")

    errors = model.validate_for_analysis("optimal_dispatch")
    assert not any("wind.1" in e for e in errors)


def test_reservoir_coupled_hydro_is_not_penalised_for_missing_run_of_river_fields():
    """A HydroGenerationUnit linked to a reservoir (drawsFromReservoir
    set) is genuinely not run-of-river -- it must not be required to
    have hasRunOfRiverInflowProfile/annual_resource_potential, since
    those are meaningless once the generator draws from a reservoir
    instead."""
    model = _model()
    reservoir = model.add_entity("ReservoirStorageUnit", "res.1")
    reservoir.dispatch.energy_storage_capacity = 8_000_000

    hydro = model.add_entity("HydroGenerationUnit", "hydro.reservoir")
    hydro.atNode = "bus.1"
    hydro.add_relation(relation_id="hasTechnology", target_entity_id="Generation.Renewable.Hydro.Reservoir")
    hydro.dispatch.nominal_power_capacity = 500
    hydro.dispatch.variable_operating_cost = 2
    hydro.add_relation(relation_id="drawsFromReservoir", target_entity_id="res.1")

    errors = model.validate_for_analysis("optimal_dispatch")
    assert not any("hydro.reservoir" in e for e in errors)
    assert not any("res.1" in e for e in errors)


def test_run_of_river_hydro_resource_potential_is_still_value_checked_if_set():
    """hasRunOfRiverInflowProfile/annual_resource_potential are
    required: false on HydroGenerationUnit (can't distinguish
    run-of-river from reservoir-coupled by class alone), but a
    run-of-river plant that does set annual_resource_potential still
    gets it checked for a sane value."""
    model = _model()
    ror = model.add_entity("HydroGenerationUnit", "ror.1")
    ror.atNode = "bus.1"
    ror.add_relation(relation_id="hasTechnology", target_entity_id="Generation.Renewable.Hydro.RunOfRiver")
    ror.dispatch.nominal_power_capacity = 300
    ror.dispatch.variable_operating_cost = 0
    ror.dispatch.annual_resource_potential = -5  # invalid: must be >= 0

    errors = model.validate_for_analysis("optimal_dispatch")
    assert any("ror.1" in e and "annual_resource_potential" in e for e in errors)


def test_reservoir_storage_unit_inflow_fields_are_mutually_required():
    """Matches the schema's own documented design (see
    ReservoirStorageUnit.yaml): a closed-loop PHS upper reservoir
    correctly has no natural inflow at all, so neither field is
    required on its own -- but setting one without the other (a
    profile with no stated annual total, or vice versa) is genuinely
    incomplete, enforced via `when:` conditions rather than leaving
    both merely optional."""
    model = build_model_from_yaml("schemas/cesdm")
    closed_loop = model.add_entity("ReservoirStorageUnit", "res.closed_loop")
    closed_loop.dispatch.energy_storage_capacity = 250_000
    # Neither field set, per the schema's own closed-loop PHS convention.

    errors = model.validate_for_analysis("optimal_dispatch")
    assert not any("res.closed_loop" in e for e in errors)

    only_energy = model.add_entity("ReservoirStorageUnit", "res.only_energy")
    only_energy.dispatch.energy_storage_capacity = 1_200_000
    only_energy.dispatch.annual_natural_inflow_energy = 5_000_000
    # hasNaturalInflowProfile deliberately left unset.

    errors = model.validate_for_analysis("optimal_dispatch")
    assert any("res.only_energy" in e and "hasNaturalInflowProfile" in e for e in errors)

    ts = model.add_entity("TimestampSeries", "ts.1")
    profile = model.add_entity("Profile", "profile.res.1")
    profile.add_relation(relation_id="hasTimestampSeries", target_entity_id="ts.1")

    only_profile = model.add_entity("ReservoirStorageUnit", "res.only_profile")
    only_profile.dispatch.energy_storage_capacity = 1_200_000
    only_profile.add_relation(relation_id="hasNaturalInflowProfile", target_entity_id="profile.res.1")
    # annual_natural_inflow_energy deliberately left unset.

    errors = model.validate_for_analysis("optimal_dispatch")
    assert any("res.only_profile" in e and "annual_natural_inflow_energy" in e for e in errors)


def test_reservoir_storage_unit_inflow_energy_is_value_checked_regardless_of_profile():
    """annual_natural_inflow_energy's own range constraint applies
    whenever the field is set, independent of whether
    hasNaturalInflowProfile happens to be linked too."""
    model = build_model_from_yaml("schemas/cesdm")
    res = model.add_entity("ReservoirStorageUnit", "res.bad_value")
    res.dispatch.energy_storage_capacity = 1_200_000
    res.dispatch.annual_natural_inflow_energy = -10  # invalid: must be >= 0

    errors = model.validate_for_analysis("optimal_dispatch")
    assert any("res.bad_value" in e and "annual_natural_inflow_energy" in e and "minimum" in e for e in errors)


def test_reservoir_storage_unit_explicit_zero_inflow_does_not_require_a_profile():
    """The real bug attribute_compare fixed: the schema itself
    documents that a closed-loop PHS reservoir may "leave
    annual_natural_inflow_energy unset OR ZERO" -- an attribute_set
    condition would have treated an explicit 0 as "set" and incorrectly
    demanded hasNaturalInflowProfile for it too. attribute_compare
    (> 0) correctly treats "unset" and "explicitly zero" the same way."""
    model = build_model_from_yaml("schemas/cesdm")
    res = model.add_entity("ReservoirStorageUnit", "res.explicit_zero")
    res.dispatch.energy_storage_capacity = 250_000
    res.dispatch.annual_natural_inflow_energy = 0

    errors = model.validate_for_analysis("optimal_dispatch")
    assert not any("res.explicit_zero" in e for e in errors)


def test_battery_storage_unit_requires_capacity_power_atnode_and_efficiency():
    """Now that ReservoirStorageUnit is a standalone class (see module
    docstring), the StorageUnit block only ever applies to genuine
    battery-style storage -- so every field below is a real
    requirement, not the required:false compromise an inherited
    ReservoirStorageUnit used to force on all but
    energy_storage_capacity."""
    model = _model()
    model.add_entity("StorageUnit", "bat.bare")

    errors = model.validate_for_analysis("optimal_dispatch")
    assert any("bat.bare" in e and "energy_storage_capacity" in e for e in errors)
    assert any("bat.bare" in e and "atNode" in e for e in errors)
    assert any("bat.bare" in e and "maximum_charging_power" in e for e in errors)
    assert any("bat.bare" in e and "maximum_discharging_power" in e for e in errors)
    assert any("bat.bare" in e and "charging_efficiency" in e for e in errors)
    assert any("bat.bare" in e and "discharging_efficiency" in e for e in errors)


def test_battery_storage_unit_passes_once_fully_populated():
    model = _model()
    bat = model.add_entity("StorageUnit", "bat.1")
    bat.atNode = "bus.1"
    bat.dispatch.energy_storage_capacity = 400
    bat.dispatch.maximum_charging_power = 100
    bat.dispatch.maximum_discharging_power = 100
    bat.dispatch.charging_efficiency = 0.95
    bat.dispatch.discharging_efficiency = 0.95

    errors = model.validate_for_analysis("optimal_dispatch")
    assert not any("bat.1" in e for e in errors)


def test_reservoir_storage_unit_is_not_penalised_for_missing_atnode_or_power():
    """ReservoirStorageUnit is a standalone class now (see module
    docstring) -- atNode, charging/discharging power, and efficiency
    aren't merely required:false here, they don't exist on this
    class's schema at all (everything except
    energy_storage_capacity/annual_natural_inflow_energy/
    hasNaturalInflowProfile lives on its paired HydroGenerationUnit
    instead). A ReservoirStorageUnit with only energy_storage_capacity
    set must pass cleanly."""
    model = _model()
    reservoir = model.add_entity("ReservoirStorageUnit", "res.1")
    reservoir.dispatch.energy_storage_capacity = 8_800_000

    errors = model.validate_for_analysis("optimal_dispatch")
    assert not any("res.1" in e for e in errors)


def test_reservoir_storage_unit_has_no_atnode_at_the_schema_level_at_all():
    """Confirms the schema change directly, not just its effect on the
    analysis profile: ReservoirStorageUnit is no longer a StorageUnit
    subclass, so atNode (and nominal_power_capacity, charging/
    discharging power and efficiency) aren't just unrequired, they're
    not known fields of this class at all."""
    model = _model()
    reservoir = model.add_entity("ReservoirStorageUnit", "res.1")
    assert model.classes["ReservoirStorageUnit"].parents == ["EnergyAssetInstance"]
    with pytest.raises(AttributeError):
        reservoir.atNode = "bus.1"


def test_reservoir_storage_unit_still_requires_energy_storage_capacity():
    model = _model()
    model.add_entity("ReservoirStorageUnit", "res.bare")

    errors = model.validate_for_analysis("optimal_dispatch")
    assert any("res.bare" in e and "energy_storage_capacity" in e for e in errors)


def test_generation_unit_now_requires_atnode():
    """atNode was missing from the original profile entirely --
    without a network location, a dispatch study has nowhere to
    deliver a generator's output to."""
    model = _model()
    model.add_entity("GenerationUnit", "gen.floating")

    errors = model.validate_for_analysis("optimal_dispatch")
    assert any("gen.floating" in e and "atNode" in e for e in errors)


def test_transformer_requires_fromnode_tonode_and_thermal_capacity_rating():
    model = _model()
    trafo = model.add_entity("Transformer", "trafo.1")
    trafo.fromNode = "bus.1"
    trafo.toNode = "bus.2"

    errors = model.validate_for_analysis("optimal_dispatch")
    assert any("trafo.1" in e and "thermal_capacity_rating" in e for e in errors)

    trafo.power_flow.thermal_capacity_rating = 300
    errors = model.validate_for_analysis("optimal_dispatch")
    assert not any("trafo.1" in e for e in errors)


def test_interconnector_requires_directional_flow_limits_not_thermal_capacity_rating():
    """Interconnector expresses capacity directionally
    (maximum_power_flow_from_to/to_from), not as thermal_capacity_rating
    -- confirmed the profile checks the field that actually exists on
    this class, not the TransmissionLine/Transformer one."""
    model = _model()
    ntc = model.add_entity("Interconnector", "ntc.1")
    ntc.fromNode = "bus.1"
    ntc.toNode = "bus.2"

    errors = model.validate_for_analysis("optimal_dispatch")
    assert any("ntc.1" in e and "maximum_power_flow_from_to" in e for e in errors)
    assert any("ntc.1" in e and "maximum_power_flow_to_from" in e for e in errors)
    assert not any("ntc.1" in e and "thermal_capacity_rating" in e for e in errors)

    ntc.power_flow.maximum_power_flow_from_to = 500
    ntc.power_flow.maximum_power_flow_to_from = 500
    errors = model.validate_for_analysis("optimal_dispatch")
    assert not any("ntc.1" in e for e in errors)


def test_hvdclink_requires_max_flow():
    model = _model()
    hvdc = model.add_entity("HVDCLink", "hvdc.1")
    hvdc.fromNode = "bus.1"
    hvdc.toNode = "bus.2"

    errors = model.validate_for_analysis("optimal_dispatch")
    assert any("hvdc.1" in e and "max_flow" in e for e in errors)

    hvdc.dispatch.max_flow = 1000
    errors = model.validate_for_analysis("optimal_dispatch")
    assert not any("hvdc.1" in e for e in errors)
