# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

"""
Kundur Two-Area System — CESDM dynamic and power flow representation
====================================================================

Reproduces the classic four-machine, two-area benchmark from:

  P. Kundur, *Power System Stability and Control*,
  McGraw-Hill, 1994, Chapter 12, pp. 813–816.

Network summary
---------------
  Area 1: Generators G1 (bus 1) and G2 (bus 2)
  Area 2: Generators G3 (bus 3) and G4 (bus 4)
  Load buses: bus 7 (area 1, 967 MW + 100 MVAr) and bus 9 (area 2, 1767 MW + 100 MVAr)
  Shunt capacitors: 200 MVAr at bus 7, 350 MVAr at bus 9
  Tie: buses 7–8 and 8–9, each two parallel 110 km, 230 kV circuits
  Step-up transformers: buses 1–5, 2–6, 3–11, 4–10
  Area intermediate buses: 5, 6, 7, 8, 9, 10, 11 at 230 kV

Unit convention
---------------
  All four generators are identical:
    Sn = 900 MVA,  Vn = 20 kV,  fn = 60 Hz

  CESDM stores all reactances in ohm referred to the machine's own base:
    Z_base = Vn² / Sn = 20² / 900 = 0.4444 Ω

  Per-unit source values (Kundur Table 12.6) are converted on input:
    X_ohm = X_pu × Z_base

  Transformer short-circuit voltage is stored in percent (attributes.yaml:
  short_circuit_voltage_in_percentage, unit = percent).

  Line impedances are stored per km (ohm/km, S/km) with line_length [km],
  converted from Kundur's total pu on the system base (100 MVA, 230 kV):
    Z_base_sys = 230² / 100 = 529 Ω
    X_ohm_per_km = (x_pu × Z_base_sys) / length_km
    B_S_per_km   = (b_pu / Z_base_sys) / length_km

  Power flow quantities (MW, MVAr) are absolute — no conversion needed.

Usage
-----
  python examples/example_kundur_two_area.py
  python examples/example_kundur_two_area.py --export-dir /tmp/kundur_out
  python examples/example_kundur_two_area.py --export-yaml /tmp/kundur.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]

_REPO_ROOT = _repo_root()
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from cesdm_toolbox import build_model_from_yaml  # noqa: E402

SCHEMA_DIRS = [
    _REPO_ROOT / "cesdm/schemas/powerflow",
    _REPO_ROOT / "cesdm/schemas/dynamics",
]

# ═════════════════════════════════════════════════════════════════════════════
# Impedance bases
# ═════════════════════════════════════════════════════════════════════════════

# Machine base (all four generators identical)
Sn_mva = 900.0   # MVA
Vn_kv  = 20.0    # kV (generator terminal)
Z_base_machine = Vn_kv**2 / Sn_mva   # = 0.4444 Ω

# System base (for network branches)
S_sys_mva = 100.0    # MVA system base
V_sys_kv  = 230.0    # kV network base
Z_base_sys = V_sys_kv**2 / S_sys_mva  # = 529 Ω


def pu_to_ohm(x_pu: float, z_base: float) -> float:
    """Convert a per-unit reactance/resistance to ohm (used for network branches)."""
    return round(x_pu * z_base, 6)


def pu_to_mw(p_pu: float, s_base_mva: float) -> float:
    """Convert a per-unit power to MW (used for governor limits only)."""
    return round(p_pu * s_base_mva, 4)


def pu_to_siemens(b_pu: float, z_base: float) -> float:
    """Convert a per-unit susceptance to siemens (B_S = b_pu / Z_base)."""
    return round(b_pu / z_base, 8)


# ═════════════════════════════════════════════════════════════════════════════
# Source data in per unit (Kundur 1994, Tables 12.6, 12.7, 12.8)
# ═════════════════════════════════════════════════════════════════════════════

# Machine — subtransient model, all values in pu on machine base (Sn=900 MVA, Vn=20 kV).
# Attribute ids match DynamicMachineModelType.Synchronous's attributes exactly.
# Reference: Kundur (1994) Example 12.6. Inertia differs by area, so the
# reactances are shared and H is stored on two machine types.
_MACHINE_PU = {
    "machine_model_order":      "subtransient_6th",
    "damping_coefficient":          0.0,    # pu
    "d_axis_synchronous_reactance":         1.8,    "q_axis_synchronous_reactance":        1.7,
    "d_axis_transient_reactance":   0.3,    "q_axis_transient_reactance":  0.55,
    "d_axis_transient_open_circuit_time_constant":  8.0,    "q_axis_transient_open_circuit_time_constant": 0.4,
    "d_axis_subtransient_reactance":  0.25,   "q_axis_subtransient_reactance": 0.25,
    "d_axis_subtransient_open_circuit_time_constant": 0.03,   "q_axis_subtransient_open_circuit_time_constant": 0.05,
    "armature_resistance":         0.0025, "stator_leakage_reactance":        0.2,
}

# AVR — SEXS simplified exciter (all four machines identical)
_AVR = {
    "AVR_SEXS_Ka":  200.0,  # pu
    "AVR_SEXS_Ta":  0.01,   # s
    "AVR_Efd_min": -3.0,    # pu
    "AVR_Efd_max":  6.0,    # pu
}

# PSS — STAB1 dual lead-lag (all four machines identical)
_PSS = {
    "PSS_STAB1_Kstab": 20.0,  # pu
    "PSS_STAB1_Tw":    10.0,  # s
    "PSS_STAB1_T1":     0.05, # s
    "PSS_STAB1_T2":     0.02, # s
    "PSS_STAB1_T3":     3.0,  # s
    "PSS_STAB1_T4":     5.4,  # s
    "PSS_Vs_max":       0.1,  # pu
    "PSS_Vs_min":      -0.1,  # pu
}

# Governor — IEEEG1 simplified steam (all four machines identical)
# Pmax/Pmin in pu on machine base → converted to MW below
_GOV_PU = {
    "GOV_IEEEG1_R":  0.05,  # pu droop
    "GOV_IEEEG1_T1": 0.1,   # s
    "GOV_IEEEG1_T2": 0.0,   # s
    "GOV_IEEEG1_T3": 0.3,   # s
    "Pmax_pu":       1.0,   # pu → MW (converted below)
    "Pmin_pu":       0.0,   # pu → MW
}


# Power flow bus type assignment (Kundur two-area, standard convention)
#   bus.1  — slack (G1 reference bus, area 1 angular reference)
#   bus.2  — PV    (G2, voltage-controlled generator bus)
#   bus.3  — PV    (G3, voltage-controlled generator bus)
#   bus.4  — PV    (G4, voltage-controlled generator bus)
#   all others — PQ (passive transmission and load buses)
_GEN_PF = {
    "gen.g1": {"active_power_setpoint": 700.0, "reactive_power_setpoint": 185.0, "voltage_magnitude_setpoint": 1.03, "voltage_angle_setpoint":  20.2},
    "gen.g2": {"active_power_setpoint": 700.0, "reactive_power_setpoint": 235.0, "voltage_magnitude_setpoint": 1.01, "voltage_angle_setpoint":  10.5},
    "gen.g3": {"active_power_setpoint": 719.0, "reactive_power_setpoint": 176.0, "voltage_magnitude_setpoint": 1.03, "voltage_angle_setpoint":  -6.8},
    "gen.g4": {"active_power_setpoint": 700.0, "reactive_power_setpoint": 202.0, "voltage_magnitude_setpoint": 1.01, "voltage_angle_setpoint": -17.0},
}
# Bus classification lives on ElectricalBus (not on GenerationUnit).
_BUS_PF_TYPE = {
    "bus.1": "slack",
    "bus.2": "PV",
    "bus.3": "PV",
    "bus.4": "PV",
}

# Bus topology: (bus_id, nominal_voltage_kv, area_label)
_BUSES = [
    ("bus.1",  20.0, "Area 1"),
    ("bus.2",  20.0, "Area 1"),
    ("bus.3",  20.0, "Area 2"),
    ("bus.4",  20.0, "Area 2"),
    ("bus.5", 230.0, "Area 1"),
    ("bus.6", 230.0, "Area 1"),
    ("bus.7", 230.0, "Area 1"),
    ("bus.8", 230.0, "Tie"),
    ("bus.9", 230.0, "Area 2"),
    ("bus.10",230.0, "Area 2"),
    ("bus.11",230.0, "Area 2"),
]

# Transformers: (id, from_bus, to_bus, short_circuit_voltage_%, rated_mva)
# Leakage reactance is 0.15 pu on the 900 MVA transformer rating.
# On the 100 MVA system base that is 0.15 × 100/900 = 0.0167 pu.
# short_circuit_voltage_in_percentage is stored on the rating, so the value is 15 %.
_TRANSFORMERS = [
    ("tfr.t1", "bus.1", "bus.5",  15.0, 900.0),
    ("tfr.t2", "bus.2", "bus.6",  15.0, 900.0),
    ("tfr.t3", "bus.3", "bus.11", 15.0, 900.0),
    ("tfr.t4", "bus.4", "bus.10", 15.0, 900.0),
]

# Lines, Example 12.6, on the 100 MVA / 230 kV base:
#   r = 0.0001 pu/km,  x = 0.001 pu/km,  b = 0.00175 pu/km
# The 110 km corridors 7–8 and 8–9 each have two circuits.
_R_PU_PER_KM = 0.0001
_X_PU_PER_KM = 0.001
_B_PU_PER_KM = 0.00175


def _line(line_id: str, from_bus: str, to_bus: str, length_km: float):
    return (
        line_id, from_bus, to_bus,
        _R_PU_PER_KM * length_km,
        _X_PU_PER_KM * length_km,
        _B_PU_PER_KM * length_km,
        length_km,
    )


# (id, from_bus, to_bus, r_pu, x_pu, b_pu, length_km) — pu totals on the system base.
_LINES = [
    _line("line.l1",  "bus.5",  "bus.6",   25.0),
    _line("line.l2",  "bus.6",  "bus.7",   10.0),
    _line("line.l3a", "bus.7",  "bus.8",  110.0),
    _line("line.l3b", "bus.7",  "bus.8",  110.0),
    _line("line.l4a", "bus.8",  "bus.9",  110.0),
    _line("line.l4b", "bus.8",  "bus.9",  110.0),
    _line("line.l5",  "bus.9",  "bus.10",  10.0),
    _line("line.l6",  "bus.10", "bus.11",  25.0),
]

# Loads: (id, bus, P [MW], Q [MVAr])
_LOADS = [
    ("load.d7", "bus.7",  967.0, 100.0),
    ("load.d9", "bus.9", 1767.0, 100.0),
]

# Shunt capacitors: (id, bus, Q injection at nominal voltage [MVAr])
_SHUNTS = [
    ("shunt.c7", "bus.7", 200.0),
    ("shunt.c9", "bus.9", 350.0),
]

# H = 6.5 s in area 1, H = 6.175 s in area 2. One type per value.
_MACHINE_TYPE = {
    "gen.g1": "dynamic_model_type.kundur.area1",
    "gen.g2": "dynamic_model_type.kundur.area1",
    "gen.g3": "dynamic_model_type.kundur.area2",
    "gen.g4": "dynamic_model_type.kundur.area2",
}
_INERTIA_S = {
    "dynamic_model_type.kundur.area1": 6.5,
    "dynamic_model_type.kundur.area2": 6.175,
}

_GEN_BUSES = {
    "gen.g1": "bus.1", "gen.g2": "bus.2",
    "gen.g3": "bus.3", "gen.g4": "bus.4",
}
_GEN_NAMES = {
    "gen.g1": "G1 (Area 1)", "gen.g2": "G2 (Area 1)",
    "gen.g3": "G3 (Area 2)", "gen.g4": "G4 (Area 2)",
}


# ═════════════════════════════════════════════════════════════════════════════
# Derived machine parameters in physical units
# ═════════════════════════════════════════════════════════════════════════════

def machine_params() -> dict:
    """Return the reusable synchronous-machine model parameters."""
    return dict(_MACHINE_PU)


def gov_params_physical() -> dict:
    """Return governor parameters converted to MW for power limits."""
    g = _GOV_PU
    gov = {k: v for k, v in _GOV_PU.items() if not k.startswith("P")}
    gov["GOV_Pmax"] = pu_to_mw(_GOV_PU["Pmax_pu"], Sn_mva)
    gov["GOV_Pmin"] = pu_to_mw(_GOV_PU["Pmin_pu"], Sn_mva)
    return gov


# ═════════════════════════════════════════════════════════════════════════════
# Model builder
# ═════════════════════════════════════════════════════════════════════════════

def build_kundur(model):
    """Populate a CesdmModel with the full Kundur two-area dataset.

    Built entirely with core add_entity/add_attribute/add_relation calls
    and typed proxy properties, including the reusable dynamic-model-type
    and controller entities (DynamicMachineModelType.Synchronous,
    Controller.AVR/.GOV/.PSS).
    """

    mach = machine_params()
    gov  = gov_params_physical()

    # ── Energy carrier + electricity CarrierDomain ────────────────────────────
    model.ensure_carrier(
        "carrier.electricity", name="Electricity", carrier_group="electricity",
    )
    model.add_entity(entity_class="CarrierDomain", entity_id="domain.electricity")
    model.add_relation("domain.electricity", "hasCarrier", "carrier.electricity")

    # ── Network nodes ────────────────────────────────────────────────────────
    for bus_id, kv, area in _BUSES:
        model.add_entity(entity_class="ElectricalBus", entity_id=bus_id)
        model.add_attribute(bus_id, "nominal_voltage", kv)
        model.add_attribute(bus_id, "name", f"{bus_id.upper()} ({area})")
        model.add_attribute(bus_id, "powerflow_bus_type", _BUS_PF_TYPE.get(bus_id, "PQ"))
        model.add_relation(bus_id, "belongsToCarrierDomain", "domain.electricity")

    # ── Reusable dynamic-machine model types ────────────────────────────────
    # Reactances are the same. Inertia is 6.5 s for G1/G2 and 6.175 s for G3/G4.
    for type_id, inertia in _INERTIA_S.items():
        model.add_entity(
            entity_class="DynamicMachineModelType.Synchronous",
            entity_id=type_id,
        )
        for attr, val in mach.items():
            model.add_attribute(type_id, attr, val)
        model.add_attribute(type_id, "inertia_constant", inertia)

    # ── Generators ────────────────────────────────────────────────────────────
    for gen_id, bus_id in _GEN_BUSES.items():
        model.add_entity(entity_class="GenerationUnit", entity_id=gen_id)
        model.add_relation(gen_id, "atNode", bus_id)
        gen = model.get_entity(entity_id=gen_id)
        gen.name = _GEN_NAMES[gen_id]

        # Power flow — all in MW / MVAr / pu / deg
        pf = gen.power_flow
        for attr, val in _GEN_PF[gen_id].items():
            setattr(pf, attr, val)

        # Generator-specific rated quantities define the per-unit base.
        gen.rated_apparent_power = Sn_mva
        gen.rated_voltage = Vn_kv

        gen.usesDynamicModelType = _MACHINE_TYPE[gen_id]

        # AVR/GOV/PSS controllers remain separate entities
        # (Controller.AVR.*/GOV.*/PSS.*), linked via controlsGenerationUnit,
        # for the same reason: every one of their attributes has a real
        # default too, and a generator can only ever have one of each, so
        # there's nothing gained from flattening them onto the generator.

        avr_id = f"dyn.avr.{gen_id}"
        model.add_entity(entity_class="Controller.AVR.SEXS", entity_id=avr_id)
        model.add_relation(avr_id, "controlsGenerationUnit", gen_id)
        for attr, val in _AVR.items():
            model.add_attribute(avr_id, attr, val)
        gen.hasAutomaticVoltageRegulator = avr_id

        pss_id = f"dyn.pss.{gen_id}"
        model.add_entity(entity_class="Controller.PSS.STAB1", entity_id=pss_id)
        model.add_relation(pss_id, "controlsGenerationUnit", gen_id)
        for attr, val in _PSS.items():
            model.add_attribute(pss_id, attr, val)
        gen.hasPowerSystemStabilizer = pss_id

        gov_id = f"dyn.gov.{gen_id}"
        model.add_entity(entity_class="Controller.GOV.IEEEG1", entity_id=gov_id)
        model.add_relation(gov_id, "controlsGenerationUnit", gen_id)
        for attr, val in gov.items():
            model.add_attribute(gov_id, attr, val)
        gen.hasTurbineGovernor = gov_id

    # ── Transformers ────────────────────────────────────────────────────────
    for tfr_id, from_bus, to_bus, scc_pct, rated_mva in _TRANSFORMERS:
        model.add_entity(entity_class="Transformer", entity_id=tfr_id)
        model.add_attribute(tfr_id, "name", tfr_id.upper())
        tfr = model.get_entity(entity_id=tfr_id)
        tfr.connect(from_bus, to_bus)

        pf = tfr.power_flow
        pf.short_circuit_voltage_in_percentage = scc_pct  # %
        pf.rated_primary_voltage = 230.0    # kV HV
        pf.rated_secondary_voltage = 20.0    # kV LV
        pf.thermal_capacity_rating = rated_mva  # MVA

    # ── Transmission lines ────────────────────────────────────────────────────
    for line_id, from_bus, to_bus, r_pu, x_pu, b_pu, length_km in _LINES:
        model.add_entity(entity_class="TransmissionLine", entity_id=line_id)
        model.add_relation(line_id, "fromNode", from_bus)
        model.add_relation(line_id, "toNode", to_bus)
        line = model.get_entity(entity_id=line_id)
        line.name = line_id.upper()

        # Convert total pu → Ω/km / S/km on system base
        pf = line.power_flow
        pf.line_length = length_km
        pf.series_resistance_per_km = pu_to_ohm(r_pu, Z_base_sys) / length_km
        pf.series_reactance_per_km = pu_to_ohm(x_pu, Z_base_sys) / length_km
        pf.shunt_susceptance_per_km = pu_to_siemens(b_pu, Z_base_sys) / length_km

    # ── Loads ─────────────────────────────────────────────────────────────────
    for load_id, bus_id, p_mw, q_mvar in _LOADS:
        model.add_entity(entity_class="DemandUnit", entity_id=load_id)
        model.add_relation(load_id, "atNode", bus_id)
        load = model.get_entity(entity_id=load_id)
        load.name = f"Load @ {bus_id.upper()}"

        pf = load.power_flow
        pf.active_power_demand = p_mw     # MW
        pf.reactive_power_demand = q_mvar  # MVAr

    # ── Shunt capacitors ────────────────────────────────────────────────────
    for shunt_id, bus_id, q_mvar in _SHUNTS:
        model.add_entity(entity_class="ShuntUnit", entity_id=shunt_id)
        model.add_relation(shunt_id, "atNode", bus_id)
        model.add_attribute(shunt_id, "name", f"Capacitor @ {bus_id.upper()}")
        model.add_attribute(shunt_id, "reactive_power_injection", q_mvar)

    return model


# ═════════════════════════════════════════════════════════════════════════════
# Summary
# ═════════════════════════════════════════════════════════════════════════════

def _val(model, eid, attr, default=None):
    """Read a scalar attribute value from any entity, class-agnostic."""
    # Model.get_attr_value needs (class, entity_id, attr); look up class first.
    for cname, ents in model.entities.items():
        if eid in ents:
            try:
                raw = model.get_attr_value(cname, eid, attr)
                return raw["value"] if isinstance(raw, dict) else raw
            except Exception:
                return default
    return default


def print_summary(model):
    print("\n" + "=" * 72)
    print("  KUNDUR TWO-AREA SYSTEM — CESDM SUMMARY")
    print("=" * 72)
    print(f"  System impedance base  : {V_sys_kv}² / {S_sys_mva} = {Z_base_sys:.1f} Ω"
          f"  (used for line/cable conversion only)")

    print(f"\n  CarrierDomain  : {list((model.entities.get('CarrierDomain') or {}).keys())}")
    print(f"  Network nodes  : {len(model.entities.get('ElectricalBus', {}))} buses"
          f" (all → domain.electricity)")
    print(f"  Generators     : {len(model.entities.get('GenerationUnit', {}))} units")
    print(f"  Transformers   : {len(model.entities.get('Transformer', {}))} units")
    print(f"  Lines          : {len(model.entities.get('TransmissionLine', {}))} circuits")
    print(f"  Loads          : {len(model.entities.get('DemandUnit', {}))} units")
    print(f"  Shunts         : {len(model.entities.get('ShuntUnit', {}))} capacitors")

    print("\n  Dynamic machine models")
    n = sum(1 for gid in model.entities.get("GenerationUnit", {})
            if model.get_entity(entity_id=gid).usesDynamicModelType)
    print(f"    {'GenerationUnit with a dynamic machine model':44s}: {n}")

    print("\n  Generator machine parameters (pu on machine base, via usesDynamicModelType)")
    xd_h, xdp_h, xdpp_h = "Xd [pu]", "X'd [pu]", "X''d [pu]"
    print(f"  {'':8s} {xd_h:>10} {xdp_h:>10} {xdpp_h:>10} {'H [s]':>7} {'Pset [MW]':>10}")
    for gen_id in _GEN_BUSES:
        gen = model.get_entity(entity_id=gen_id)
        # Shared DynamicMachineModelType — not a per-generator dyn.machine.* id.
        dyn_ids = model.get_relation_targets(gen_id, "usesDynamicModelType") or []
        dyn_id = dyn_ids[0] if dyn_ids else None
        xd = xdp = xdpp = H = "n/a"
        if dyn_id:
            xd   = _val(model, dyn_id, "d_axis_synchronous_reactance", "n/a")
            xdp  = _val(model, dyn_id, "d_axis_transient_reactance", "n/a")
            xdpp = _val(model, dyn_id, "d_axis_subtransient_reactance", "n/a")
            H    = _val(model, dyn_id, "inertia_constant", "n/a")
        pm = gen.power_flow.active_power_setpoint
        pm = pm if pm is not None else "n/a"
        fmt = lambda v, w, d: f"{v:{w}.{d}f}" if isinstance(v, (int, float)) else f"{'n/a':>{w}}"
        print(f"  {gen_id:8s}"
              f" {fmt(xd,10,4)} {fmt(xdp,10,4)} {fmt(xdpp,10,4)}"
              f" {fmt(H,7,3)} {fmt(pm,10,1)}")

    print(f"\n  (Sn={Sn_mva} MVA, Vn={Vn_kv} kV; "
          f"area 1 H={_INERTIA_S['dynamic_model_type.kundur.area1']} s, "
          f"area 2 H={_INERTIA_S['dynamic_model_type.kundur.area2']} s)")
    print("\n  Line data (total pu on 100 MVA, 230 kV)")
    for line_id, fb, tb, r_pu, x_pu, b_pu, length_km in _LINES:
        print(f"  {line_id:12s} {fb}→{tb}  L={length_km:5.0f} km  "
              f"r={r_pu:.4f} pu  x={x_pu:.4f} pu  b={b_pu:.4f} pu")
    print("\n  Shunt capacitors (MVAr injected at nominal voltage)")
    for shunt_id, bus_id, q_mvar in _SHUNTS:
        print(f"  {shunt_id:12s} {bus_id}  Q={q_mvar:.0f} MVAr")

    print("\n  Role classification")
    for cls in ("Controller.AVR", "Controller.AVR.SEXS", "Controller.AVR.IEEET1", "Controller.AVR.AC1A",
                "Controller.GOV", "Controller.GOV.IEEEG1", "Controller.GOV.GGOV1", "Controller.GOV.HYGOV",
                "Controller.PSS", "Controller.PSS.STAB1", "Controller.PSS.PSS2A",
                "GenerationUnit", "ElectricalBus"):
        role = model._derive_role_from_parents(cls)
        print(f"    {cls:44s} → {role}")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# Power flow — Example 12.6 operating point
# ═════════════════════════════════════════════════════════════════════════════

def solve_power_flow(model, *, tol: float = 1e-8, max_iter: int = 25) -> dict:
    """Solve the AC power flow stored on the model.

    Lines and transformers are read back from the entity attributes, so the
    result is the network CESDM holds, not a second copy of the textbook table.
    Shunt capacitors are constant susceptance. Loads are constant power.
    Bus 1 is the slack bus.
    """
    bus_ids = [bus_id for bus_id, _kv, _area in _BUSES]
    index = {bus_id: i for i, bus_id in enumerate(bus_ids)}
    n = len(bus_ids)
    Y = np.zeros((n, n), dtype=complex)

    def stamp(i: int, j: int, r: float, x: float, b: float) -> None:
        y = 1.0 / (r + 1j * x)
        y_sh = 1j * b / 2.0
        Y[i, i] += y + y_sh
        Y[j, j] += y + y_sh
        Y[i, j] -= y
        Y[j, i] -= y

    for line_id, fb, tb, _r, _x, _b, _length in _LINES:
        pf = model.get_entity(entity_id=line_id).power_flow
        length = pf.line_length
        r_pu = pf.series_resistance_per_km * length / Z_base_sys
        x_pu = pf.series_reactance_per_km * length / Z_base_sys
        b_pu = pf.shunt_susceptance_per_km * length * Z_base_sys
        stamp(index[fb], index[tb], r_pu, x_pu, b_pu)
    for tfr_id, fb, tb, _scc, _rated in _TRANSFORMERS:
        pf = model.get_entity(entity_id=tfr_id).power_flow
        x_pu = (pf.short_circuit_voltage_in_percentage / 100.0) * (
            S_sys_mva / pf.thermal_capacity_rating
        )
        stamp(index[fb], index[tb], 0.0, x_pu, 0.0)
    for shunt_id, bus_id, _q in _SHUNTS:
        q_mvar = model.get_entity(entity_id=shunt_id).power_flow.reactive_power_injection
        Y[index[bus_id], index[bus_id]] += 1j * (q_mvar / S_sys_mva)

    p_spec = np.zeros(n)
    q_spec = np.zeros(n)
    vm = np.ones(n)
    kind = {bus_id: "PQ" for bus_id in bus_ids}
    gen_for_bus = {bus_id: gen_id for gen_id, bus_id in _GEN_BUSES.items()}
    for bus_id, bus_kind in _BUS_PF_TYPE.items():
        kind[bus_id] = bus_kind
        vm[index[bus_id]] = _GEN_PF[gen_for_bus[bus_id]]["voltage_magnitude_setpoint"]
    for gen_id, bus_id in _GEN_BUSES.items():
        if kind[bus_id] == "slack":
            continue
        p_spec[index[bus_id]] += _GEN_PF[gen_id]["active_power_setpoint"] / S_sys_mva
    for _load_id, bus_id, p_mw, q_mvar in _LOADS:
        p_spec[index[bus_id]] -= p_mw / S_sys_mva
        q_spec[index[bus_id]] -= q_mvar / S_sys_mva

    slack = [i for bus_id, i in index.items() if kind[bus_id] == "slack"]
    pv = [i for bus_id, i in index.items() if kind[bus_id] == "PV"]
    pq = [i for bus_id, i in index.items() if kind[bus_id] == "PQ"]
    ang_buses = pv + pq
    ang = np.zeros(n)
    G = Y.real
    B = Y.imag

    def injections(vm_now, ang_now):
        P = np.zeros(n)
        Q = np.zeros(n)
        for i in range(n):
            for j in range(n):
                theta = ang_now[i] - ang_now[j]
                P[i] += vm_now[i] * vm_now[j] * (G[i, j] * np.cos(theta) + B[i, j] * np.sin(theta))
                Q[i] += vm_now[i] * vm_now[j] * (G[i, j] * np.sin(theta) - B[i, j] * np.cos(theta))
        return P, Q

    for _ in range(max_iter):
        P, Q = injections(vm, ang)
        mismatch = np.concatenate([
            np.array([p_spec[i] - P[i] for i in ang_buses]),
            np.array([q_spec[i] - Q[i] for i in pq]),
        ])
        if np.max(np.abs(mismatch)) < tol:
            break
        n_ang = len(ang_buses)
        J = np.zeros((len(mismatch), len(mismatch)))
        for a, i in enumerate(ang_buses):
            for b, j in enumerate(ang_buses):
                if i == j:
                    J[a, b] = -Q[i] - B[i, i] * vm[i] ** 2
                else:
                    theta = ang[i] - ang[j]
                    J[a, b] = vm[i] * vm[j] * (G[i, j] * np.sin(theta) - B[i, j] * np.cos(theta))
            for b, j in enumerate(pq):
                col = n_ang + b
                if i == j:
                    J[a, col] = P[i] / vm[i] + G[i, i] * vm[i]
                else:
                    theta = ang[i] - ang[j]
                    J[a, col] = vm[i] * (G[i, j] * np.cos(theta) + B[i, j] * np.sin(theta))
        for a, i in enumerate(pq):
            row = n_ang + a
            for b, j in enumerate(ang_buses):
                if i == j:
                    J[row, b] = P[i] - G[i, i] * vm[i] ** 2
                else:
                    theta = ang[i] - ang[j]
                    J[row, b] = -vm[i] * vm[j] * (G[i, j] * np.cos(theta) + B[i, j] * np.sin(theta))
            for b, j in enumerate(pq):
                col = n_ang + b
                if i == j:
                    J[row, col] = Q[i] / vm[i] - B[i, i] * vm[i]
                else:
                    theta = ang[i] - ang[j]
                    J[row, col] = vm[i] * (G[i, j] * np.sin(theta) - B[i, j] * np.cos(theta))
        step = np.linalg.solve(J, mismatch)
        for b, i in enumerate(ang_buses):
            ang[i] += step[b]
        for b, i in enumerate(pq):
            vm[i] += step[n_ang + b]
    else:
        raise RuntimeError(f"Kundur power flow did not converge in {max_iter} iterations")

    P, Q = injections(vm, ang)

    def branch_flow(fb, tb, r, x, b):
        i, j = index[fb], index[tb]
        Vi = vm[i] * np.exp(1j * ang[i])
        Vj = vm[j] * np.exp(1j * ang[j])
        current = (Vi - Vj) / (r + 1j * x) + Vi * (1j * b / 2.0)
        power = Vi * np.conj(current) * S_sys_mva
        return float(power.real), float(power.imag)

    flows = []
    for line_id, fb, tb, _r, _x, _b, _length in _LINES:
        pf = model.get_entity(entity_id=line_id).power_flow
        length = pf.line_length
        p_mw, q_mvar = branch_flow(
            fb, tb,
            pf.series_resistance_per_km * length / Z_base_sys,
            pf.series_reactance_per_km * length / Z_base_sys,
            pf.shunt_susceptance_per_km * length * Z_base_sys,
        )
        flows.append({"id": line_id, "from": fb, "to": tb, "p_mw": p_mw, "q_mvar": q_mvar})
    tie_mw = sum(item["p_mw"] for item in flows if item["from"] == "bus.7" and item["to"] == "bus.8")
    return {
        "bus_id": bus_ids,
        "vm": vm,
        "angle_deg": np.degrees(ang),
        "p_mw": P * S_sys_mva,
        "q_mvar": Q * S_sys_mva,
        "flows": flows,
        "tie_7_8_mw": tie_mw,
    }


def print_power_flow(result: dict) -> None:
    print("  Power flow (bus 1 is the angle reference)")
    print(f"  {'bus':8s} {'|V| [pu]':>10} {'angle [deg]':>12} {'P [MW]':>10} {'Q [MVAr]':>10}")
    for i, bus_id in enumerate(result["bus_id"]):
        print(f"  {bus_id:8s} {result['vm'][i]:10.4f} {result['angle_deg'][i]:12.2f}"
              f" {result['p_mw'][i]:10.1f} {result['q_mvar'][i]:10.1f}")
    print("\n  Tie circuits, flow out of the from-bus")
    for item in result["flows"]:
        if item["from"] not in ("bus.7", "bus.8"):
            continue
        print(f"  {item['id']:12s} {item['from']}→{item['to']}"
              f"  P={item['p_mw']:7.1f} MW  Q={item['q_mvar']:7.1f} MVAr")
    print(f"  area 1 export on buses 7–8: {result['tie_7_8_mw']:.1f} MW")
    print()


# ═════════════════════════════════════════════════════════════════════════════
# Entry point
# ═════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Build the Kundur two-area CESDM model."
    )
    parser.add_argument("--export-dir",  metavar="DIR",  default=None,
                        help="Export as Frictionless Data Package.")
    parser.add_argument("--export-yaml", metavar="FILE", default=None,
                        help="Export as flat YAML.")
    args = parser.parse_args()

    print("Loading CESDM schema …")
    model = build_model_from_yaml([str(path) for path in SCHEMA_DIRS])

    print("Building Kundur two-area model …")
    build_kundur(model)
    print_summary(model)
    print_power_flow(solve_power_flow(model))

    errors = model.validate()
    if errors:
        print("Model has validation issues:")
        for e in errors:
            print("  -", e)
    else:
        print("Model validated successfully.")

    # Analysis-specific checks (schema-optional fields needed by each study).
    for profile in ("power_flow", "dynamics"):
        analysis_errors = model.validate_for_analysis(profile)
        if analysis_errors:
            print(f"\nvalidate_for_analysis('{profile}'): {len(analysis_errors)} error(s)")
            for e in analysis_errors:
                print("  -", e)
        else:
            print(f"validate_for_analysis('{profile}'): OK")

    if args.export_dir:
        out = Path(args.export_dir)
        out.mkdir(parents=True, exist_ok=True)
        dp = model.export_frictionless(
            out,
            name        = "kundur-two-area",
            title       = "Kundur Two-Area System",
            description = (
                "Four-machine two-area benchmark (Kundur 1994, Ch. 12). "
                "Subtransient machine models, SEXS AVRs, STAB1 PSSs, IEEEG1 governors. "
                "Reactances stored in ohm (machine base), line impedances in ohm/S (system base)."
            ),
            version = "1.0.0",
        )
        print(f"  Exported Frictionless package → {dp}")

    if args.export_yaml:
        model.export_yaml(args.export_yaml)
        print(f"  Exported YAML → {args.export_yaml}")


if __name__ == "__main__":
    main()
