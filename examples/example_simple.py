#!/usr/bin/env python3
"""example_simple.py

A tiny CESDM demo model using each core energy-domain entity type,
built with the object-oriented proxy layer throughout: `add_entity()`/
`ensure_entity()`/`ensure_carrier()` already hand back a live,
correctly-typed proxy object directly, so it's captured and used
straight away (`entity.add_attribute(...)`, `entity.add_relation(...)`,
`entity.dispatch.x = y`, `entity.connect(bus)`, ...) rather than
re-fetching the id with `get_entity()` afterward -- see
docs/getting_started.md for the same style, and
docs/architecture/proxy_api.md for the full proxy design.

Goal
----
Keep the system very small (3 electricity nodes) but demonstrate every
core entity class at least once:

  EnergySystemModel, Carrier, CarrierDomain,
  GeographicalRegion, ElectricalBus, GasBus, HeatBus,
  DemandUnit, GenerationUnit, StorageUnit, TransmissionElement,
  ConversionUnit + ConversionPort ×3 (Tier 2 MIMO)

Design rules applied throughout
--------------------------------
- Every attribute/relation lives directly on the asset it belongs to,
  tagged `belongsToGroup` (dispatch/topology/power_flow/...) -- see
  docs/guide/05_attribute_groups.md.
- Profile references use ``hasDemandProfile`` / ``hasAvailabilityProfile``
  relations pointing to ``Profile`` entities (not plain string attributes)
- ``CarrierDomain`` groups energy carriers by domain
- ``ElectricalBus`` / ``GasBus`` / ``HeatBus`` / ``HydrogenBus`` are the
  typed, carrier-specific ``NetworkNode`` subclasses
- ``belongsToCarrierDomain`` links a node to its ``CarrierDomain``
- ``locatedIn`` links an entity to its ``GeographicalRegion``
- ``atNode`` (single-port assets) / ``fromNode``+``toNode`` (two-port
  assets) declare topological connections directly on the asset
- ``hasTechnology`` links an asset instance to its ``EnergyTechnologyType``
- ``ConversionPort.hasCarrier`` declares each conversion port's carrier;
  ``hasInputCarrier``/``hasOutputCarrier`` do the same for simple assets
"""

from __future__ import annotations

from pathlib import Path
import sys

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]

sys.path.insert(0, str(_repo_root()))

from cesdm_toolbox import build_model_from_yaml, CesdmModel  # noqa: E402

def build_simple_model(schema_dir: Path) -> CesdmModel:
    m = build_model_from_yaml(str(schema_dir))

    # ------------------------------------------------------------------
    # 1) Root container
    # ------------------------------------------------------------------
    energy_system = m.add_entity(entity_class="EnergySystemModel", entity_id="SIMPLE_DEMO")
    energy_system.add_attribute(attribute_id="long_name", value="Simple 3-node electricity + CHP + storage demo")
    energy_system.add_attribute(attribute_id="co2_price", value=100.0)

    # ------------------------------------------------------------------
    # 2) Carrier entities, via ensure_carrier() (proxy-returning)
    # ------------------------------------------------------------------
    carriers = {}
    for eid, name, co2, cost in [
        ("Electricity", "Electricity", 0.0,  0.0),
        ("Gas",         "Gas",         0.20, 60.0),
        ("Heat",        "Heat",        0.0,  0.0),
        ("Water",       "Water",       0.0,  5.0),
        ("Uranium",     "Uranium",     0.0,  10.0),
    ]:
        carrier = m.ensure_carrier(eid, name=name)
        carrier.co2_emission_intensity = co2
        carrier.energy_carrier_cost = cost
        carriers[eid] = carrier

    # ------------------------------------------------------------------
    # 3) CarrierDomain entities
    # ------------------------------------------------------------------
    for did, name, carrier_id in [
        ("ELEC", "Electricity", "Electricity"),
        ("HEAT", "Heat",        "Heat"),
        ("GAS",  "Gas",         "Gas"),
    ]:
        domain = m.add_entity(entity_class="CarrierDomain", entity_id=did)
        domain.add_attribute(attribute_id="name", value=name)
        domain.add_relation(relation_id="hasCarrier", target_entity_id=carrier_id)

    # ------------------------------------------------------------------
    # 4) GeographicalRegion
    # ------------------------------------------------------------------
    for rid, name in [("R_A", "Region A"), ("R_B", "Region B")]:
        region = m.add_entity(entity_class="GeographicalRegion", entity_id=rid)
        region.add_attribute(attribute_id="name", value=name)

    # ------------------------------------------------------------------
    # 5) Buses
    # ------------------------------------------------------------------
    # Three ElectricalBus nodes (small 3-node electricity network).
    buses = {}
    for bid, region, name in [
        ("N_E1", "R_A", "Electricity node E1"),
        ("N_E2", "R_A", "Electricity node E2"),
        ("N_E3", "R_B", "Electricity node E3"),
    ]:
        bus = m.add_entity(entity_class="ElectricalBus", entity_id=bid)
        bus.add_attribute(attribute_id="nominal_voltage", value=220.0)
        bus.add_relation(relation_id="locatedIn", target_entity_id=region)
        bus.add_relation(relation_id="belongsToCarrierDomain", target_entity_id="ELEC")
        bus.add_attribute(attribute_id="name", value=name)
        buses[bid] = bus
    n_e1, n_e2, n_e3 = buses["N_E1"], buses["N_E2"], buses["N_E3"]

    n_g1 = m.add_entity(entity_class="GasBus", entity_id="N_G1")
    n_g1.add_attribute(attribute_id="name", value="Gas node G1")
    n_g1.add_relation(relation_id="belongsToCarrierDomain", target_entity_id="GAS")
    n_g1.add_relation(relation_id="locatedIn", target_entity_id="R_A")

    n_h1 = m.add_entity(entity_class="HeatBus", entity_id="N_H1")
    n_h1.add_attribute(attribute_id="name", value="Heat node H1")
    n_h1.add_relation(relation_id="belongsToCarrierDomain", target_entity_id="HEAT")
    n_h1.add_relation(relation_id="locatedIn", target_entity_id="R_A")

    # ------------------------------------------------------------------
    # 6) DemandUnit
    # ------------------------------------------------------------------
    demand_elec = m.add_entity(entity_class="DemandUnit", entity_id="L_ELEC_A")
    demand_elec.add_relation(relation_id="atNode", target_entity_id="N_E2")
    demand_elec.add_attribute(attribute_id="name", value="Electricity demand in Region A")
    demand_elec.dispatch.annual_energy_demand = 5_000_000.0

    demand_heat = m.add_entity(entity_class="DemandUnit", entity_id="L_HEAT_A")
    demand_heat.add_relation(relation_id="atNode", target_entity_id="N_H1")
    demand_heat.add_attribute(attribute_id="name", value="Heat demand in Region A")
    demand_heat.dispatch.annual_energy_demand = 3_000_000.0

    # ------------------------------------------------------------------
    # 7) GenerationUnit -- no specific technology template is being used
    #    here (the original demo assigns carriers directly, not a
    #    technology).
    # ------------------------------------------------------------------
    # Gas turbine: Gas -> Electricity at N_E1
    gt_a = m.add_entity(entity_class="GenerationUnit", entity_id="GT_A")
    gt_a.add_relation(relation_id="atNode", target_entity_id="N_E1")
    gt_a.add_relation(relation_id="hasInputCarrier", target_entity_id="Gas")
    gt_a.add_relation(relation_id="hasOutputCarrier", target_entity_id="Electricity")
    gt_a.name = "Gas turbine A"
    gt_a.dispatch.generator_technology_type = "gas"
    gt_a.dispatch.energy_conversion_efficiency = 0.50
    gt_a.dispatch.nominal_power_capacity = 200.0

    # Run-of-river hydro: Water -> Electricity at N_E3. Nondispatchable,
    # so this uses HydroGenerationUnit with dispatch_type set explicitly
    # (reservoir-coupled dispatchable units would use drawsFromReservoir
    # to a ReservoirStorageUnit instead -- see example_hydro_reservoir_plant.py).
    hyd_b = m.add_entity(entity_class="HydroGenerationUnit", entity_id="HYD_B")
    hyd_b.add_relation(relation_id="atNode", target_entity_id="N_E3")
    hyd_b.add_relation(relation_id="hasInputCarrier", target_entity_id="Water")
    hyd_b.add_relation(relation_id="hasOutputCarrier", target_entity_id="Electricity")
    hyd_b.name = "Hydro B (run-of-river)"
    hyd_b.dispatch.dispatch_type = "nondispatchable"
    hyd_b.dispatch.turbine_efficiency = 0.90
    hyd_b.dispatch.nominal_power_capacity = 150.0
    hyd_b.dispatch.annual_resource_potential = 1_500_000.0

    # ------------------------------------------------------------------
    # 8) StorageUnit
    # ------------------------------------------------------------------
    bat_e2 = m.add_entity(entity_class="StorageUnit", entity_id="BAT_E2")
    bat_e2.add_relation(relation_id="atNode", target_entity_id="N_E2")
    bat_e2.add_relation(relation_id="storesCarrier", target_entity_id="Electricity")
    bat_e2.add_attribute(attribute_id="name", value="Battery at E2")
    bat_e2.dispatch.energy_storage_capacity = 500.0
    bat_e2.dispatch.nominal_power_capacity = 100.0
    bat_e2.dispatch.maximum_charging_power = 100.0
    bat_e2.dispatch.charging_efficiency = 0.95
    bat_e2.dispatch.discharging_efficiency = 0.95
    bat_e2.dispatch.initial_state_of_charge = 0.50

    # ------------------------------------------------------------------
    # 9) Interconnectors
    # ------------------------------------------------------------------
    for ntc_id, name, frm, to, p12, p21 in [
        ("NTC_E1_E2", "NTC E1-E2", n_e1, n_e2, 300.0, 300.0),
        ("NTC_E2_E3", "NTC E2-E3", n_e2, n_e3, 200.0, 200.0),
    ]:
        ntc = m.add_entity(entity_class="Interconnector", entity_id=ntc_id)
        ntc.add_attribute(attribute_id="name", value=name)
        ntc.connect(frm, to)  # fromNode+toNode
        pv = ntc.power_flow
        pv.maximum_power_flow_from_to = p12
        pv.maximum_power_flow_to_from = p21

    # ------------------------------------------------------------------
    # 10) ConversionUnit — Tier 2 MIMO: PEM Fuel Cell (H2 + Air → Elec + Heat)
    #
    #   Ports:
    #     port.FC_A.h2_in    input   H2 bus     flow_coeff = -1.00  (reference)
    #     port.FC_A.elec_out output  elec bus   flow_coeff = +0.55
    #     port.FC_A.heat_out output  heat bus   flow_coeff = +0.30
    #
    #   ConversionUnit's own dispatch attributes/relations (declared
    #   directly on the asset) only declare dispatch participation.
    #   Port-level coefficients and the is_reference_port flag define the
    #   conversion ratios and reference scale.
    # ------------------------------------------------------------------

    # We reuse the existing carriers and add H2 for this demo
    h2 = m.ensure_carrier("H2", name="Hydrogen")
    h2.co2_emission_intensity = 0.0

    # H2 bus (new for the fuel cell)
    n_h2 = m.add_entity(entity_class="HydrogenBus", entity_id="N_H2")
    n_h2.add_attribute(attribute_id="name", value="H2 bus")

    # Asset identity
    fuel_cell = m.add_entity(entity_class="ConversionUnit", entity_id="FC_A")
    fuel_cell.add_attribute(attribute_id="name", value="PEM Fuel Cell A")

    # ── Tier 2: ConversionPort entities ───────────────────────────────────
    # Reference port: H2 input (flow_coefficient = -1.0, negative = withdrawal)
    h2_in = m.add_entity(entity_class="ConversionPort", entity_id="port.FC_A.h2_in")
    h2_in.add_attribute(attribute_id="port_direction", value="input")
    h2_in.add_attribute(attribute_id="flow_coefficient", value=-1.0)
    h2_in.add_attribute(attribute_id="is_reference_port", value=True)
    h2_in.add_relation(relation_id="belongsToUnit", target_entity_id=fuel_cell)
    h2_in.add_relation(relation_id="atNode", target_entity_id=n_h2)
    h2_in.add_relation(relation_id="hasCarrier", target_entity_id=h2)

    # Electricity output port
    elec_out = m.add_entity(entity_class="ConversionPort", entity_id="port.FC_A.elec_out")
    elec_out.add_attribute(attribute_id="port_direction", value="output")
    elec_out.add_attribute(attribute_id="flow_coefficient", value=0.55)
    elec_out.add_attribute(attribute_id="maximum_output_power", value=55.0)
    elec_out.add_attribute(attribute_id="is_reference_port", value=False)
    elec_out.add_relation(relation_id="belongsToUnit", target_entity_id=fuel_cell)
    elec_out.add_relation(relation_id="atNode", target_entity_id=n_e1)
    elec_out.add_relation(relation_id="hasCarrier", target_entity_id=carriers["Electricity"])

    # Heat output port
    heat_out = m.add_entity(entity_class="ConversionPort", entity_id="port.FC_A.heat_out")
    heat_out.add_attribute(attribute_id="port_direction", value="output")
    heat_out.add_attribute(attribute_id="flow_coefficient", value=0.30)
    heat_out.add_attribute(attribute_id="maximum_output_power", value=30.0)
    heat_out.add_attribute(attribute_id="is_reference_port", value=False)
    heat_out.add_relation(relation_id="belongsToUnit", target_entity_id=fuel_cell)
    heat_out.add_relation(relation_id="atNode", target_entity_id=n_h1)
    heat_out.add_relation(relation_id="hasCarrier", target_entity_id=carriers["Heat"])

    # ── Operational parameters, held directly on the unit itself ─────────
    fuel_cell.add_relation(relation_id="referencePort", target_entity_id=h2_in)

    return m

def main():
    root       = _repo_root()
    schema_dir = root / "schemas/cesdm"
    out_dir    = root / "output" / "simple" / "cesdm"
    out_dir.mkdir(parents=True, exist_ok=True)

    model  = build_simple_model(schema_dir)

    print(model.summary())
    print()

    errors = model.validate()
    if errors:
        print("Model has validation issues:")
        for e in errors:
            print("  -", e)
    else:
        print("Model validated successfully.")

    # Hierarchical YAML — representations nested under each asset
    model.export_yaml_hierarchical(out_dir / "yaml" / "simple_hierarchical.yaml")

    # Flat YAML — one section per class
    model.export_yaml(out_dir / "yaml" / "simple_flat.yaml")

    # Frictionless Data Package — self-describing, one CSV per class
    model.export_frictionless(
        out_dir / "frictionless",
        name  = "cesdm-simple-demo",
        title = "Simple CESDM Demo Model",
    )

    print(f"Wrote outputs to: {out_dir}")
    print(f"  {out_dir / 'yaml' / 'simple_hierarchical.yaml'}")
    print(f"  {out_dir / 'yaml' / 'simple_flat.yaml'}")
    print(f"  {out_dir / 'frictionless' / 'datapackage.json'}")

if __name__ == "__main__":
    main()
