#!/usr/bin/env python3
"""
reference_energy_system_model.py
==========================

A self-contained, self-explanatory walkthrough of the CESDM toolbox,
told through one running example: a simplified 2030 electricity
system for Switzerland and its four neighbours (Germany, France,
Italy, Austria).

No external data files are needed -- every number in this tutorial is
a made-up but plausible 2030 planning assumption, chosen to be
*interesting* (a real generation mix, a real hydro portfolio, real
cross-border trade) rather than realistic down to the last MW.

Run it:

    python examples/reference_energy_system_model.py


THE CESDM API: CORE EAR CALLS + THE PROXY LAYER
-------------------------------------------------
This tutorial builds everything with two things, side by side:

1. **Core EAR calls** -- `add_entity`, `add_attribute`, `add_relation`,
   the same three primitives for *any* schema-defined class. This is
   the recommended way to build a model: it needs no matching builder
   function to exist for whatever you're modelling, and the schema
   documents exactly what's valid to call it with. `add_entity`/
   `ensure_entity` already hand back a live, correctly-typed proxy
   object directly, so it's captured and used right away rather than
   re-fetched with `get_entity` afterward:

       region = model.add_entity("GeographicalRegion", "region.ch")
       region.add_attribute(attribute_id="name", value="Switzerland")

2. **Direct proxy attribute/relation assignment** -- that returned
   object is a live, typed handle back into the model, not a
   disconnected copy:

       gen.name = "Beznau II"                        # asset-level identity attribute
       gen.dispatch.nominal_power_capacity = 1600     # dispatch attribute -- unit auto-attached
       gen.connect(bus)                               # topology relation

   Typos are caught immediately, with a suggestion, instead of
   silently doing nothing (`gen.dispach.x = 1` -> AttributeError:
   "not an attribute or relation of GenerationUnit. Did you mean:
   dispatch?"). This tutorial deliberately triggers one on purpose,
   in Step 4, so you can see it happen.

A third thing worth knowing about even though it's not a function you
call: **unset dispatch attributes fall back to the technology
template.** If a GenerationUnit references a GeneratorType (via
``hasTechnology``) and doesn't set its own
``energy_conversion_efficiency``, reading it resolves the technology's
value automatically. Step 5 shows this directly.
"""

from __future__ import annotations

from pathlib import Path
from collections import defaultdict
import sys

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]

_REPO_ROOT = _repo_root()
sys.path.insert(0, str(_REPO_ROOT))

from cesdm_toolbox import build_model_from_yaml, CesdmModel
from cesdm.default_library import GeneratorTypes, Carriers
from cesdm.generated_proxies import (
    CarrierProxy, GenerationUnitProxy, ReservoirStorageUnitProxy, InterconnectorProxy,
)


# ══════════════════════════════════════════════════════════════════════
# STEP 0 — Load the schema, then the technology library
#
# The *schema* (schemas/cesdm/) defines what entity classes, attributes, and
# relations exist at all, and validates every value against it as you
# build. The *library* (library/default_library/) is optional reference
# data built on top of that schema: pre-defined GeneratorType/
# StorageType/Carrier entities with realistic default efficiency,
# cost, and dispatch-type values drawn from ENTSO-E/TYNDP technology
# classes, so you don't have to invent your own efficiency numbers for
# "a 2030 CCGT" from scratch.
# ══════════════════════════════════════════════════════════════════════

def build_model(schema_dir: Path, library_path: Path) -> CesdmModel:
    print("\n── Step 0: Load schema + technology library ─────────────")
    m = build_model_from_yaml(str(schema_dir))
    m.import_library(str(library_path))
    n_types = len(m.entities.get("GeneratorType", {})) + len(m.entities.get("StorageType", {}))
    print(f"   Schema:  {len(m.classes)} entity classes available")
    print(f"   Library: {len(m.entities.get('Carrier', {}))} carriers, "
          f"{n_types} technology types pre-loaded")

    # ────────────────────────────────────────────────────────────────
    # STEP 1 — The system container, carriers, and the carrier domain
    #
    # add_energy_system_model() is a *generated* constructor (layer 1)
    # -- EnergySystemModel has no bus/topology of its own, so there's
    # nothing a hand-written composite could usefully add on top.
    #
    # The library already created every Carrier entity we need
    # (with realistic default cost/CO2 values); we only update the fuel
    # costs to this scenario's 2030 assumptions, using direct proxy
    # attribute assignment (layer 3) -- no separate "update" method
    # needed, the same assignment that creates a value also updates it.
    # ────────────────────────────────────────────────────────────────

    # ────────────────────────────────────────────────────────────────
    # STEP 1 — The system container, carriers, and the carrier domain
    #
    # EnergySystemModel has no bus/topology of its own -- pure identity
    # attributes.
    #
    # The library already created every Carrier entity we need
    # (with realistic default cost/CO2 values); we only update the fuel
    # costs to this scenario's 2030 assumptions, using direct proxy
    # attribute assignment -- no separate "update" method needed, the
    # same assignment that creates a value also updates it.
    # ────────────────────────────────────────────────────────────────

    print("\n── Step 1: System container, carriers, carrier domain ────")

    system = m.add_entity(entity_class="EnergySystemModel", entity_id="CH_NEIGHBOURS_2030")
    system.add_attribute(attribute_id="long_name", value="CH + neighbours electricity system, 2030")
    system.add_attribute(attribute_id="co2_price", value=80.0)  # MU/t -- stored directly on the system container

    fuel_costs_2030 = {  # MU/MWh_fuel, 2030 planning assumptions
        Carriers.CARRIER_FUEL_FOSSIL_GAS_NATURAL_GAS: 30.0,
        Carriers.CARRIER_FUEL_NUCLEAR_URANIUM: 3.0,
        Carriers.CARRIER_FUEL_FOSSIL_COAL_HARD_COAL: 12.0,
    }
    for carrier_id, cost in fuel_costs_2030.items():
        m.asset_as(carrier_id, CarrierProxy).energy_carrier_cost = cost

    elec_domain = m.add_entity(entity_class="CarrierDomain", entity_id="domain.electricity")
    elec_domain.add_attribute(attribute_id="name", value="Electricity")
    elec_domain.add_relation(relation_id="hasCarrier", target_entity_id=Carriers.CARRIER_ELECTRICITY)
    print(f"   CO2 price: 80 MU/t.  Fuel costs updated for "
          f"{len(fuel_costs_2030)} carriers.")

    # ────────────────────────────────────────────────────────────────
    # STEP 2 — Geographic regions
    #
    # GeographicalRegion is pure identity + an optional isSubRegionOf
    # relation.
    # ────────────────────────────────────────────────────────────────

    print("\n── Step 2: Geographic regions ────────────────────────────")

    countries = [
        ("region.ch", "Switzerland"), ("region.de", "Germany"),
        ("region.fr", "France"),      ("region.it", "Italy"),
        ("region.at", "Austria"),
    ]
    for region_id, name in countries:
        region = m.add_entity(entity_class="GeographicalRegion", entity_id=region_id)
        region.add_attribute(attribute_id="name", value=name)
    print(f"   Created {len(countries)} regions.")

    # ────────────────────────────────────────────────────────────────
    # STEP 3 — Electricity buses
    #
    # ElectricalBus holds its power-flow and spatial data directly --
    # no separate view entity needed at all.
    # ────────────────────────────────────────────────────────────────

    print("\n── Step 3: Electricity buses ─────────────────────────────")

    buses = [
        # id        region        name                  kV     lat   lon
        ("bus.ch",  "region.ch",  "Switzerland 380kV",  380.0, 47.0,  8.0),
        ("bus.de",  "region.de",  "Germany 380kV",       380.0, 51.0, 10.0),
        ("bus.fr",  "region.fr",  "France 400kV",        400.0, 46.0,  2.0),
        ("bus.it",  "region.it",  "Italy 380kV",         380.0, 42.0, 12.0),
        ("bus.at",  "region.at",  "Austria 380kV",       380.0, 47.5, 14.0),
    ]
    for bus_id, region_id, name, kv, lat, lon in buses:
        bus = m.add_entity(entity_class="ElectricalBus", entity_id=bus_id)
        bus.add_attribute(attribute_id="nominal_voltage", value=kv)
        bus.add_relation(relation_id="locatedIn", target_entity_id=region_id)
        bus.add_relation(relation_id="belongsToCarrierDomain", target_entity_id=elec_domain)
        bus.add_attribute(attribute_id="latitude", value=lat)
        bus.add_attribute(attribute_id="longitude", value=lon)
        bus.name = name
    print(f"   Created {len(buses)} buses, each with a spatial (lat/lon) view.")

    # ────────────────────────────────────────────────────────────────
    # STEP 4 — Demand
    #
    # DemandUnit + carrier relation + bus connection + dispatch
    # attributes, all directly on the asset. annual_energy_demand is
    # then set via `.dispatch`, still a namespace alias over the same
    # storage -- CESDM keeps identity (name, description) and
    # operational data (how much, how flexible, what it costs) both on
    # the asset now, just tagged by which former view they came from.
    #
    # One deliberate typo below shows what happens when you get an
    # attribute name wrong: not a silent no-op, an immediate
    # AttributeError naming the actual class and suggesting the fix.
    # ────────────────────────────────────────────────────────────────

    print("\n── Step 4: Demand units ───────────────────────────────────")

    demands = [
        # id       name                    annual GWh     bus
        ("dem.ch", "CH electricity demand",   60_000, "bus.ch"),
        ("dem.de", "DE electricity demand",  500_000, "bus.de"),
        ("dem.fr", "FR electricity demand",  450_000, "bus.fr"),
        ("dem.it", "IT electricity demand",  300_000, "bus.it"),
        ("dem.at", "AT electricity demand",   70_000, "bus.at"),
    ]
    for dem_id, name, annual_gwh, bus_id in demands:
        load = m.add_entity(entity_class="DemandUnit", entity_id=dem_id)
        load.add_relation(relation_id="atNode", target_entity_id=bus_id)
        load.name = name
        load.dispatch.annual_energy_demand = annual_gwh * 1000  # GWh -> MWh
    print(f"   Created {len(demands)} demand units.")

    print("   (Demonstration: a deliberate typo on a view attribute...)")
    try:
        # m.get_entity(...) already returns the correctly-typed DemandUnitProxy
        # at runtime -- but a type checker can't know that just from a
        # plain string argument, so it still sees the generic EntityProxy
        # statically (and EntityProxy itself has no .dispatch declared,
        # only its subclasses do). asset_as(entity_id, cls) closes that
        # gap: statically typed to return exactly `cls`, and checked at
        # runtime too (raises TypeError if the entity turns out to be
        # something else), so .dispatch below type-checks correctly in
        # your editor *and* the typo is still caught immediately at
        # runtime either way.
        from cesdm.generated_proxies import DemandUnitProxy
        demands_asset = m.asset_as("dem.ch", DemandUnitProxy)
        demands_asset.dispatch.anual_energy_demand = 1.0  # <- missing 'n'
    except AttributeError as exc:
        print(f"   -> caught immediately: {exc}")

    # ────────────────────────────────────────────────────────────────
    # STEP 5 — The generation fleet
    #
    # Each technology family wires a different input relation: thermal
    # and nuclear generators use hasInputCarrier (nuclear has none set
    # at all by convention -- fuel isn't modelled as a flow for it
    # here), wind/solar use hasInputResource. Every family sets
    # hasTechnology, atNode, and nominal_power_capacity the same way.
    #
    # Using GeneratorTypes.* / Carriers.* constants instead of raw strings means your editor autocompletes
    # every valid technology id and flags an unknown one immediately --
    # no more finding out about a typo only once validate() runs.
    #
    # Every generator below sets nominal_power_capacity explicitly, but
    # deliberately *never* sets energy_conversion_efficiency --
    # watch what it reads back as anyway.
    # ────────────────────────────────────────────────────────────────

    print("\n── Step 5: Generation fleet ───────────────────────────────")

    generators = [
        # id           name              technology                                          MW      bus       family    annual_MWh
        ("gen.ch.gas", "CH Gas CCGT",   GeneratorTypes.GENERATION_THERMAL_GAS_CCGT_NEW,       3_000, "bus.ch", "thermal", None),
        ("gen.ch.nuc", "CH Nuclear",    GeneratorTypes.GENERATION_THERMAL_NUCLEAR_STANDARD,   2_000, "bus.ch", "nuclear", None),
        ("gen.ch.win", "CH Wind",       GeneratorTypes.GENERATION_RENEWABLE_WIND_ONSHORE,        500, "bus.ch", "wind",    900_000),
        ("gen.ch.sol", "CH Solar PV",   GeneratorTypes.GENERATION_RENEWABLE_SOLAR_PV_UTILITY,  2_000, "bus.ch", "solar", 2_000_000),
        ("gen.de.gas", "DE Gas CCGT",   GeneratorTypes.GENERATION_THERMAL_GAS_CCGT_NEW,       6_000, "bus.de", "thermal", None),
        ("gen.de.win", "DE Wind",       GeneratorTypes.GENERATION_RENEWABLE_WIND_ONSHORE,     30_000, "bus.de", "wind",    65_000_000),
        ("gen.de.sol", "DE Solar PV",   GeneratorTypes.GENERATION_RENEWABLE_SOLAR_PV_UTILITY, 60_000, "bus.de", "solar",   60_000_000),
        ("gen.fr.nuc", "FR Nuclear",    GeneratorTypes.GENERATION_THERMAL_NUCLEAR_STANDARD,   56_000, "bus.fr", "nuclear", None),
        ("gen.fr.gas", "FR Gas CCGT",   GeneratorTypes.GENERATION_THERMAL_GAS_CCGT_NEW,       4_000, "bus.fr", "thermal", None),
        ("gen.it.gas", "IT Gas CCGT",   GeneratorTypes.GENERATION_THERMAL_GAS_CCGT_NEW,       5_000, "bus.it", "thermal", None),
        ("gen.it.sol", "IT Solar PV",   GeneratorTypes.GENERATION_RENEWABLE_SOLAR_PV_UTILITY, 20_000, "bus.it", "solar",   25_000_000),
    ]

    m.ensure_entity(
        class_name="TimestampSeries", entity_id="ts.hourly.2030", name="Hourly, 2030",
        start_datetime="2030-01-01T00:00:00", resolution="PT1H",
        length=8760, timezone="Europe/Zurich",
    )
    ts_hourly = "ts.hourly.2030"

    m.ensure_resource("resource.renewable.wind", name="Wind", resource_type="wind", resource_group="renewable")
    m.ensure_resource("resource.renewable.solar", name="Solar irradiance", resource_type="solar", resource_group="renewable")


    for gen_id, name, technology, cap_mw, bus_id, family, annual_mwh in generators:
        gen = m.add_entity(entity_class="GenerationUnit", entity_id=gen_id)
        gen.add_relation(relation_id="hasTechnology", target_entity_id=technology)
        gen.add_relation(relation_id="atNode", target_entity_id=bus_id)
        if family == "thermal":
            gen.add_relation(relation_id="hasInputCarrier", target_entity_id=Carriers.CARRIER_FUEL_FOSSIL_GAS_NATURAL_GAS)
        elif family == "wind":
            gen.add_relation(relation_id="hasInputResource", target_entity_id="resource.renewable.wind")
        elif family == "solar":
            gen.add_relation(relation_id="hasInputResource", target_entity_id="resource.renewable.solar")
        # nuclear: no input relation set, by convention (fuel isn't
        # modelled as a flow for it in this tutorial).
        gen.name = name
        gen.dispatch.nominal_power_capacity = cap_mw
        if annual_mwh:  # renewables: attach a capacity-factor availability profile
            gen.dispatch.annual_resource_potential = annual_mwh
            profile_id = f"profile.{gen_id}.capacity_factor"
            m.attach_availability_profile(
                gen,
                profile_id,
                create=True,
                timestamp_series_id=ts_hourly,
                profile_type="as_capacity_factor",
                data_reference=f"/profiles/{profile_id}",
            )
    print(f"   Created {len(generators)} generators.")

    gas_gen = m.asset_as("gen.ch.gas", GenerationUnitProxy)
    print(f"   energy_conversion_efficiency was never set on {gas_gen.name!r} -- "
          f"reads back as {gas_gen.dispatch.energy_conversion_efficiency} anyway, "
          f"resolved from its GeneratorType technology template.")

    # ────────────────────────────────────────────────────────────────
    # STEP 6 — The hydro portfolio: four different plant types
    #
    # Real hydro fleets aren't one asset type: a run-of-river plant has
    # no meaningful storage, a reservoir/pondage plant stores energy
    # for later, and pumped-hydro storage (PHS) can additionally pump
    # water back uphill. Each pattern below wires the same relations a
    # dedicated builder used to wire for you: hasTechnology, atNode,
    # hasInputResource="resource.water", machine_role, and -- for the
    # reservoir-coupled ones -- the drawsFromReservoir/
    # dischargesToReservoir/suppliesResourceTo relation pair linking
    # each HydroGenerationUnit to its ReservoirStorageUnit(s).
    # ────────────────────────────────────────────────────────────────

    print("\n── Step 6: Hydro portfolio ────────────────────────────────")

    m.ensure_resource("resource.water", name="Water", resource_type="water")

    # Run-of-river: CH and AT, availability tracks river flow throughout the year.
    for gen_id, name, cap_mw, bus_id, annual_mwh in [
        ("gen.ch.hydro.ror", "CH Hydro run-of-river", 4_000, "bus.ch", 16_000_000),
        ("gen.at.hydro.ror", "AT Hydro run-of-river", 1_500, "bus.at",  8_000_000),
    ]:
        gen = m.add_entity(entity_class="HydroGenerationUnit", entity_id=gen_id)
        gen.add_relation(relation_id="hasTechnology", target_entity_id="Generation.Renewable.Hydro.RunOfRiver")
        gen.add_relation(relation_id="hasInputResource", target_entity_id="resource.water")
        gen.add_relation(relation_id="atNode", target_entity_id=bus_id)
        gen.name = name
        gen.dispatch.machine_role = "turbine"
        gen.dispatch.nominal_power_capacity = cap_mw
        gen.dispatch.annual_resource_potential = annual_mwh
        profile_id = f"profile.{gen_id}.inflow"
        m.attach_run_of_river_profile(
            gen,
            profile_id,
            create=True,
            timestamp_series_id=ts_hourly,
            profile_type="as_capacity_factor",
            data_reference=f"/profiles/{profile_id}",
        )

    # Reservoir hydro: CH and AT, seasonal storage with natural inflow.
    for res_id, res_name, gen_id, gen_name, cap_mw, bus_id, energy_mwh, inflow_mwh in [
        ("storage.ch.hydro.reservoir", "CH Alpine seasonal reservoir",
         "gen.ch.hydro.reservoir", "CH Reservoir hydro turbines", 8_000, "bus.ch", 8_800_000, 20_000_000),
        ("storage.at.hydro.reservoir", "AT Alpine reservoir",
         "gen.at.hydro.reservoir", "AT Reservoir hydro turbines", 3_000, "bus.at", 3_000_000,  7_000_000),
    ]:
        reservoir = m.add_entity(entity_class="ReservoirStorageUnit", entity_id=res_id)
        reservoir.add_relation(relation_id="storesResource", target_entity_id="resource.water")
        gen = m.add_entity(entity_class="HydroGenerationUnit", entity_id=gen_id)
        gen.add_relation(relation_id="hasTechnology", target_entity_id="Generation.Renewable.Hydro.Reservoir")
        gen.add_relation(relation_id="hasInputResource", target_entity_id="resource.water")
        gen.add_relation(relation_id="atNode", target_entity_id=bus_id)
        gen.add_relation(relation_id="drawsFromReservoir", target_entity_id=res_id)
        reservoir.add_relation(relation_id="suppliesResourceTo", target_entity_id=gen_id)

        reservoir.name = res_name
        reservoir.dispatch.energy_storage_capacity = energy_mwh
        reservoir.dispatch.annual_natural_inflow_energy = inflow_mwh
        gen.name = gen_name
        gen.dispatch.machine_role = "turbine"
        gen.dispatch.nominal_power_capacity = cap_mw
        gen.dispatch.annual_resource_potential = inflow_mwh
        profile_id = f"profile.{res_id}.inflow"
        m.attach_natural_inflow_profile(
            reservoir,
            profile_id,
            create=True,
            timestamp_series_id=ts_hourly,
            profile_type="as_normalized_annual_energy",
            data_reference=f"/profiles/{profile_id}",
        )

    # Open-loop PHS: CH and AT, reversible, with some natural inflow into
    # the upper reservoir as well as pumped storage.
    for res_id, res_name, gen_id, gen_name, cap_mw, bus_id, energy_mwh, inflow_mwh, pump_mw in [
        ("storage.ch.phs.open", "CH open-loop PHS reservoir",
         "gen.ch.phs.open", "CH open-loop PHS pump-turbine", 1_500, "bus.ch", 1_200_000, 1_200_000, 1_300),
        ("storage.at.phs.open", "AT open-loop PHS reservoir",
         "gen.at.phs.open", "AT open-loop PHS pump-turbine", 1_500, "bus.at",  450_000,   500_000, 1_300),
    ]:
        reservoir = m.add_entity(entity_class="ReservoirStorageUnit", entity_id=res_id)
        reservoir.add_relation(relation_id="storesResource", target_entity_id="resource.water")
        gen = m.add_entity(entity_class="HydroGenerationUnit", entity_id=gen_id)
        gen.add_relation(relation_id="hasTechnology", target_entity_id="Generation.Renewable.Hydro.PHS.OpenLoop")
        gen.add_relation(relation_id="hasInputResource", target_entity_id="resource.water")
        gen.add_relation(relation_id="atNode", target_entity_id=bus_id)
        gen.add_relation(relation_id="drawsFromReservoir", target_entity_id=res_id)

        reservoir.name = res_name
        reservoir.dispatch.energy_storage_capacity = energy_mwh
        reservoir.dispatch.annual_natural_inflow_energy = inflow_mwh
        gen.name = gen_name
        gen.dispatch.machine_role = "reversible"
        gen.dispatch.nominal_power_capacity = cap_mw
        gen.dispatch.maximum_pumping_power = pump_mw
        gen.dispatch.pumping_efficiency = 0.82
        gen.dispatch.turbine_efficiency = 0.90

    # Closed-loop PHS: CH only, purely reversible storage, no natural
    # inflow at all -- both reservoirs created explicitly, linked via
    # drawsFromReservoir (upper) and dischargesToReservoir (lower).
    upper = m.add_entity(entity_class="ReservoirStorageUnit", entity_id="storage.ch.phs.closed.upper")
    upper.add_relation(relation_id="storesResource", target_entity_id="resource.water")
    lower = m.add_entity(entity_class="ReservoirStorageUnit", entity_id="storage.ch.phs.closed.lower")
    lower.add_relation(relation_id="storesResource", target_entity_id="resource.water")

    gen = m.add_entity(entity_class="HydroGenerationUnit", entity_id="gen.ch.phs.closed")
    gen.add_relation(relation_id="hasTechnology", target_entity_id="Generation.Renewable.Hydro.PHS.ClosedLoop")
    gen.add_relation(relation_id="hasInputResource", target_entity_id="resource.water")
    gen.add_relation(relation_id="atNode", target_entity_id="bus.ch")
    gen.add_relation(relation_id="drawsFromReservoir", target_entity_id="storage.ch.phs.closed.upper")
    gen.add_relation(relation_id="dischargesToReservoir", target_entity_id="storage.ch.phs.closed.lower")

    gen.dispatch.machine_role = "reversible"
    gen.dispatch.nominal_power_capacity = 2_000
    gen.dispatch.maximum_pumping_power = 1_900
    gen.dispatch.pumping_efficiency = 0.81
    gen.dispatch.turbine_efficiency = 0.89
    upper.name = "CH closed-loop PHS upper reservoir"
    upper.dispatch.energy_storage_capacity = 250_000
    lower.name = "CH closed-loop PHS lower reservoir"
    lower.dispatch.energy_storage_capacity = 250_000
    gen.name = "CH closed-loop PHS pump-turbine"

    n_hydro = len(m.entities.get("HydroGenerationUnit", {}))
    n_reservoirs = len(m.entities.get("ReservoirStorageUnit", {}))
    print(f"   Created {n_hydro} hydro generation units and {n_reservoirs} reservoirs "
          f"(run-of-river, reservoir, open-loop PHS, closed-loop PHS).")

    # ────────────────────────────────────────────────────────────────
    # STEP 7 — Cross-border interconnectors (NTC)
    #
    # Interconnector itself is pure identity, so there's nothing beyond
    # what .connect() and .power_flow already give every asset for free.
    # ────────────────────────────────────────────────────────────────

    print("\n── Step 7: Cross-border interconnectors ──────────────────")

    interconnectors = [
        # id            name          bus A     bus B     MW A->B  MW B->A
        ("ntc.ch.de", "CH-DE NTC", "bus.ch", "bus.de", 6_000, 5_500),
        ("ntc.ch.fr", "CH-FR NTC", "bus.ch", "bus.fr", 4_000, 3_500),
        ("ntc.ch.it", "CH-IT NTC", "bus.ch", "bus.it", 5_000, 4_500),
        ("ntc.ch.at", "CH-AT NTC", "bus.ch", "bus.at", 2_000, 2_000),
        ("ntc.de.fr", "DE-FR NTC", "bus.de", "bus.fr", 3_500, 3_500),
        ("ntc.de.at", "DE-AT NTC", "bus.de", "bus.at", 4_000, 4_000),
        ("ntc.fr.it", "FR-IT NTC", "bus.fr", "bus.it", 3_000, 3_000),
        ("ntc.at.it", "AT-IT NTC", "bus.at", "bus.it", 2_500, 2_500),
    ]
    for ntc_id, name, bus_a, bus_b, mw_ab, mw_ba in interconnectors:
        ntc = m.add_entity(entity_class="Interconnector", entity_id=ntc_id)
        ntc.add_attribute(attribute_id="name", value=name)
        ntc.connect(bus_a, bus_b)
        ntc.power_flow.maximum_power_flow_from_to = mw_ab
        ntc.power_flow.maximum_power_flow_to_from = mw_ba
    print(f"   Created {len(interconnectors)} interconnectors.")


    # ────────────────────────────────────────────────────────────────
    # STEP 8 — Multi-energy extension for Switzerland
    #
    # The electricity-only cross-border model is extended with gas and
    # heat domains. A CHP plant couples all three domains through explicit
    # ConversionPort entities. This demonstrates that CESDM represents
    # several physical infrastructures in one consistent model rather
    # than creating a separate data model for each sector.
    # ────────────────────────────────────────────────────────────────

    print("\n── Step 8: Multi-energy extension ───────────────────────")

    heat_carrier = m.ensure_carrier("carrier.heat", name="Heat")
    gas_carrier = Carriers.CARRIER_FUEL_FOSSIL_GAS_NATURAL_GAS

    gas_domain = m.add_entity(entity_class="CarrierDomain", entity_id="domain.gas.ch")
    gas_domain.add_attribute(attribute_id="name", value="Swiss gas domain")
    gas_domain.add_relation(relation_id="hasCarrier", target_entity_id=gas_carrier)

    heat_domain = m.add_entity(entity_class="CarrierDomain", entity_id="domain.heat.ch")
    heat_domain.add_attribute(attribute_id="name", value="Swiss heat domain")
    heat_domain.add_relation(relation_id="hasCarrier", target_entity_id=heat_carrier)

    gas_bus = m.add_entity(entity_class="GasBus", entity_id="bus.ch.gas")
    gas_bus.add_attribute(attribute_id="name", value="Swiss gas bus")
    gas_bus.add_relation(relation_id="locatedIn", target_entity_id="region.ch")
    gas_bus.add_relation(relation_id="belongsToCarrierDomain", target_entity_id="domain.gas.ch")

    heat_bus = m.add_entity(entity_class="HeatBus", entity_id="bus.ch.heat")
    heat_bus.add_attribute(attribute_id="name", value="Swiss heat bus")
    heat_bus.add_relation(relation_id="locatedIn", target_entity_id="region.ch")
    heat_bus.add_relation(relation_id="belongsToCarrierDomain", target_entity_id="domain.heat.ch")

    gas_supply = m.add_entity(entity_class="ExternalSupply", entity_id="supply.ch.gas")
    gas_supply.add_attribute(attribute_id="name", value="Swiss gas import")
    gas_supply.add_relation(relation_id="hasOutputCarrier", target_entity_id=gas_carrier)
    gas_supply.add_relation(relation_id="atNode", target_entity_id="bus.ch.gas")
    gas_supply.add_attribute(attribute_id="supply_capacity", value=10_000.0)
    gas_supply.add_attribute(attribute_id="is_slack", value=True)

    chp = m.add_entity(entity_class="CHPUnit", entity_id="chp.ch")
    chp.add_attribute(attribute_id="name", value="Swiss CHP plant")
    chp.add_attribute(attribute_id="nominal_electrical_power_capacity", value=350.0, unit="MW")
    chp.add_attribute(attribute_id="nominal_thermal_power_capacity", value=450.0, unit="MW")
    chp.add_attribute(attribute_id="electrical_efficiency", value=0.35, unit="fraction")
    chp.add_attribute(attribute_id="thermal_efficiency", value=0.45, unit="fraction")
    chp.add_attribute(attribute_id="total_efficiency", value=0.80, unit="fraction")
    chp.add_attribute(attribute_id="power_to_heat_ratio", value=350.0 / 450.0, unit="fraction")
    chp.add_relation(relation_id="hasInputCarrier", target_entity_id=gas_carrier)
    chp.add_relation(
        relation_id="hasElectricityOutputCarrier",
        target_entity_id=Carriers.CARRIER_ELECTRICITY,
    )
    chp.add_relation(relation_id="hasHeatOutputCarrier", target_entity_id="carrier.heat")
    chp.add_relation(relation_id="atFuelNode", target_entity_id="bus.ch.gas")
    chp.add_relation(relation_id="atElectricityNode", target_entity_id="bus.ch")
    chp.add_relation(relation_id="atHeatNode", target_entity_id="bus.ch.heat")

    heat_demand = m.add_entity(entity_class="DemandUnit", entity_id="dem.ch.heat")
    heat_demand.add_attribute(attribute_id="name", value="Swiss heat demand")
    heat_demand.add_relation(relation_id="atNode", target_entity_id="bus.ch.heat")
    heat_demand.add_attribute(attribute_id="annual_energy_demand", value=20_000_000.0)

    print("   Added gas and heat domains, one compact CHPUnit, and heat demand.")

    return m


# ══════════════════════════════════════════════════════════════════════
# Exploring the finished model
# ══════════════════════════════════════════════════════════════════════

def print_statistics(m: CesdmModel) -> None:
    print("\n" + "═" * 70)
    print("MODEL OVERVIEW")
    print("═" * 70)

    # model.summary() -- the one-liner "what's in this model" answer.
    # Subclasses are rolled up under their top-level asset family by
    # default (HydroGenerationUnit counts under GenerationUnit); pass
    # detailed=True for the fine-grained breakdown instead.
    print("\n  model.summary():")
    for line in m.summary().splitlines():
        print("   ", line)
    print("\n  model.summary(detailed=True):")
    for line in m.summary(detailed=True).splitlines():
        print("   ", line)

    # Beyond the one-liner overview, the low-level entity/relation API
    # is the right tool for custom analysis that summary() doesn't try
    # to cover -- reading arbitrary, not-statically-known fields across
    # a whole model is exactly what it's for.
    print("\n  Generation capacity by country and fuel:")
    by_country_fuel: dict[tuple[str, str], float] = defaultdict(float)
    node_to_country = {b: c for c, b in [("CH", "bus.ch"), ("DE", "bus.de"),
                                          ("FR", "bus.fr"), ("IT", "bus.it"), ("AT", "bus.at")]}
    for cls in ("GenerationUnit", "HydroGenerationUnit"):
        for gen_id in m.entities.get(cls, {}):
            # asset() rather than asset_as() here: this loop genuinely
            # covers two different classes, so there's no single correct
            # cls argument to give asset_as() -- exactly the case where
            # the low-level API (generic EntityProxy, resolved dynamically
            # at runtime) is the right tool, not a static-typing gap to
            # close.
            gen = m.get_entity(entity_id=gen_id)
            bus_targets = m.get_relation_targets(gen_id, "atNode")
            country = node_to_country.get(bus_targets[0], "?") if bus_targets else "?"
            tech_targets = m.get_relation_targets(gen_id, "hasTechnology")
            fuel = tech_targets[0].split(".")[-2] if tech_targets and "." in tech_targets[0] else "other"
            cap = gen.dispatch.nominal_power_capacity or 0.0
            by_country_fuel[(country, fuel)] += cap
    for (country, fuel), cap in sorted(by_country_fuel.items()):
        print(f"    {country:3s} {fuel:12s} {cap:>9,.0f} MW")

    print("\n  Cross-border interconnector NTC [MW]:")
    for ntc_id in m.entities.get("Interconnector", {}):
        ntc = m.asset_as(ntc_id, InterconnectorProxy)
        pf = ntc.power_flow
        topo_id = ntc.topology.id
        frm = m.get_relation_targets(topo_id, "fromNode")
        to = m.get_relation_targets(topo_id, "toNode")
        if frm and to:
            print(f"    {ntc.name:12s} {frm[0]:8s} -> {to[0]:8s}  "
                  f"{pf.maximum_power_flow_from_to:>6,.0f} MW  <-  {pf.maximum_power_flow_to_from:>6,.0f} MW")

    print("\n  Total system capacity [MW]:", f"{m.total_capacity():,.0f}")


def export_model(m: CesdmModel, output_dir: Path) -> None:
    print("\n" + "═" * 70)
    print("EXPORT")
    print("═" * 70)
    output_dir.mkdir(parents=True, exist_ok=True)

    yaml_path = output_dir / "ch_neighbours_2030.yaml"
    m.export_yaml_hierarchical(yaml_path)
    print(f"\n  Hierarchical YAML -> {yaml_path}")

    fp_dir = output_dir / "frictionless"
    dp_path = m.export_frictionless(
        fp_dir, name="ch-neighbours-2030",
        title="CH + Neighbours 2030 -- CESDM tutorial model",
    )
    print(f"  Frictionless Data Package -> {dp_path}")


if __name__ == "__main__":
    schema_dir = _REPO_ROOT / "schemas/cesdm"
    library_path = _REPO_ROOT / "library" / "default_library"
    output_dir = _REPO_ROOT / "output" / "reference_energy_system_model"

    model = build_model(schema_dir, library_path)

    print("\n" + "═" * 70)
    print("VALIDATION")
    print("═" * 70)
    errors = model.validate()
    if errors:
        print(f"\n  {len(errors)} validation issue(s):")
        for e in errors[:20]:
            print("   -", e)
    else:
        print("\n  Model validated successfully -- every relation and attribute")
        print("  satisfies the schema's own rules.")

    print_statistics(model)
    export_model(model, output_dir)

    print("\n" + "═" * 70)
    print("That's the whole tutorial. What you just saw:")
    print("  - core add_entity/add_attribute/add_relation calls for every class")
    print("  - direct proxy attribute/relation assignment, typo-safe, unit-aware")
    print("  - the technology-default cascade (efficiency resolved, never set)")
    print("  - gas, electricity, and heat domains coupled by a compact CHPUnit")
    print("  - model.summary() for the one-line overview of a whole model")
    print("═" * 70)
