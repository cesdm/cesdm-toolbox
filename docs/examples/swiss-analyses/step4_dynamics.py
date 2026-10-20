#!/usr/bin/env python3
# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

"""Part 2, step 4: the dynamics layer.

    python docs/examples/swiss-analyses/step4_dynamics.py

Reads the power-flow file and appends a 6th-order subtransient model
for each synchronous class. The numbers are typical for that class of
machine, not nameplate data for these plants. The dispatch year and
the network stay on the same objects.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from step1_complete import load_layer, save_layer, summarise  # noqa: E402

# 6th-order subtransient model. Per-unit on the machine base.
# Round rotor: Xd ≈ Xq. Salient pole (hydro): Xq clearly below Xd.
# H rises from hydro to gas turbine to large steam. Not nameplate data.
ORDER = "subtransient_6th"

def machine(h, xd, xq, xd_tr, xq_tr, xd_sub, xq_sub, td0, tq0, td0_sub, tq0_sub):
    return {
        "machine_model_order": ORDER,
        "inertia_constant": h,
        "damping_coefficient": 0.0,
        "d_axis_synchronous_reactance": xd,
        "q_axis_synchronous_reactance": xq,
        "d_axis_transient_reactance": xd_tr,
        "q_axis_transient_reactance": xq_tr,
        "d_axis_subtransient_reactance": xd_sub,
        "q_axis_subtransient_reactance": xq_sub,
        "d_axis_transient_open_circuit_time_constant": td0,
        "q_axis_transient_open_circuit_time_constant": tq0,
        "d_axis_subtransient_open_circuit_time_constant": td0_sub,
        "q_axis_subtransient_open_circuit_time_constant": tq0_sub,
    }

# Large steam turbo-generator. Xd sits on the schema default, which is the
# round-rotor band cited from IEEE Std 1110 (about 1.0–2.0 pu).
NUCLEAR_MACHINE = machine(6.5, 1.8, 1.7, 0.30, 0.55, 0.25, 0.25, 8.0, 0.4, 0.03, 0.05)
# Heavy-duty gas turbine: same construction, less inertia, slightly lower reactance.
GAS_MACHINE = machine(4.5, 1.6, 1.5, 0.25, 0.45, 0.18, 0.18, 5.0, 0.5, 0.03, 0.04)
# Salient-pole hydro. Xq' stays near Xq: there is no field winding on the q axis.
HYDRO_MACHINE = machine(3.0, 1.0, 0.65, 0.30, 0.65, 0.22, 0.22, 5.0, 0.1, 0.05, 0.05)

# Same simplified exciter. The type dependence is in the machine and the governor.
AVR = {"AVR_SEXS_Ka": 200.0, "AVR_SEXS_Ta": 0.01, "AVR_Efd_min": -3.0, "AVR_Efd_max": 6.0}

# power_factor used only to turn plant MW into a rated MVA base.
POWER_FACTOR = 0.9
TERMINAL_KV = {"nuclear": 24.0, "gas": 15.0, "hydro": 15.0}

NUCLEAR = "gen.CH_NUC"


def report(model, title: str, profile) -> None:
    gaps = model.validate_for_analysis(profile)
    print(title)
    print(f"    {len(gaps)} gaps")
    for (cls, attribute), n in sorted(summarise(gaps).items()):
        print(f"      {cls:42s} {attribute:48s} ×{n}")


def fill(model, entity_id: str, values: dict) -> None:
    for name, value in values.items():
        model.add_attribute(entity_id, name, value)


def plant_mw(model, entity_id: str) -> float:
    for cls in ("GenerationUnit", "HydroGenerationUnit"):
        value = model.get_attr_value(cls, entity_id, "nominal_power_capacity")
        if value is not None:
            return float(value)
    raise KeyError(entity_id)


def link_type(model, entity_id: str, type_id: str, params: dict, terminal_kv: float) -> None:
    if not model.has_entity(type_id):
        model.add_entity("DynamicMachineModelType.Synchronous", type_id)
    fill(model, type_id, params)
    model.add_relation(entity_id, "usesDynamicModelType", type_id)
    model.add_attribute(entity_id, "rated_apparent_power",
                        round(plant_mw(model, entity_id) / POWER_FACTOR, 1), unit="MVA")
    model.add_attribute(entity_id, "rated_voltage", terminal_kv, unit="kV")


def link_controller(model, entity_id: str, cls: str, role: str, values: dict) -> None:
    cid = f"dyn.{role}.{entity_id.removeprefix('gen.')}"
    back = {"avr": "hasAutomaticVoltageRegulator", "gov": "hasTurbineGovernor"}[role]
    model.add_entity(cls, cid)
    model.add_relation(cid, "controlsGenerationUnit", entity_id)
    model.add_relation(entity_id, back, cid)
    pmax = plant_mw(model, entity_id)
    fill(model, cid, {**values, "GOV_Pmax": pmax, "GOV_Pmin": 0.0} if role == "gov" else values)


def attach_synchronous(model) -> None:
    link_type(model, "gen.CH_NUC", "dynamic_model_type.nuclear.steam",
              NUCLEAR_MACHINE, TERMINAL_KV["nuclear"])
    link_type(model, "gen.CH_GAS", "dynamic_model_type.gas.round_rotor",
              GAS_MACHINE, TERMINAL_KV["gas"])
    link_type(model, "gen.CH_HYD_RES", "dynamic_model_type.hydro.salient",
              HYDRO_MACHINE, TERMINAL_KV["hydro"])
    link_type(model, "gen.CH_HYD_ROR", "dynamic_model_type.hydro.salient",
              HYDRO_MACHINE, TERMINAL_KV["hydro"])

    for eid in ("gen.CH_NUC", "gen.CH_GAS", "gen.CH_HYD_RES", "gen.CH_HYD_ROR"):
        link_controller(model, eid, "Controller.AVR.SEXS", "avr", AVR)

    link_controller(model, "gen.CH_NUC", "Controller.GOV.IEEEG1", "gov",
                    {"GOV_IEEEG1_R": 0.05, "GOV_IEEEG1_T1": 0.2, "GOV_IEEEG1_T3": 0.3})
    link_controller(model, "gen.CH_GAS", "Controller.GOV.GGOV1", "gov",
                    {"GOV_GGOV1_R": 0.04, "GOV_GGOV1_Kpgov": 10.0, "GOV_GGOV1_Kigov": 2.0,
                     "GOV_GGOV1_Tact": 0.5, "GOV_GGOV1_T3": 0.85})
    for eid in ("gen.CH_HYD_RES", "gen.CH_HYD_ROR"):
        link_controller(model, eid, "Controller.GOV.HYGOV", "gov",
                        {"GOV_HYGOV_R": 0.05, "GOV_HYGOV_r": 0.3, "GOV_HYGOV_Tr": 5.0,
                         "GOV_HYGOV_Tf": 0.05, "GOV_HYGOV_Tg": 0.5, "GOV_HYGOV_Tw": 0.5,
                         "GOV_HYGOV_At": 1.2})


def print_machines(model) -> None:
    rows = [
        ("gen.CH_NUC", "round-rotor steam", "Controller.GOV.IEEEG1", None),
        ("gen.CH_GAS", "round-rotor gas", "Controller.GOV.GGOV1", None),
        ("gen.CH_HYD_RES", "salient-pole hydro", "Controller.GOV.HYGOV", "GOV_HYGOV_Tw"),
        ("gen.CH_HYD_ROR", "salient-pole hydro", "Controller.GOV.HYGOV", "GOV_HYGOV_Tw"),
    ]
    print(f"    {'plant':16} {'construction':22} {'H [s]':>6} {'Xd':>6} {'Xq':>6}  governor")
    for eid, kind, gov_cls, extra_attr in rows:
        type_id = model.get_relation_targets(eid, "usesDynamicModelType")[0]
        def param(name: str):
            return model.get_attr_value("DynamicMachineModelType.Synchronous", type_id, name)
        gov_id = model.get_relation_targets(eid, "hasTurbineGovernor")[0]
        gov = gov_cls.rsplit(".", 1)[-1]
        note = ""
        if extra_attr:
            tw = model.get_attr_value(gov_cls, gov_id, extra_attr)
            note = f"  Tw={tw:g} s"
        print(f"    {eid:16} {kind:22} {param('inertia_constant'):6.1f}"
              f" {param('d_axis_synchronous_reactance'):6.2f}"
              f" {param('q_axis_synchronous_reactance'):6.2f}  {gov}{note}")
    print(f"    model order: {ORDER}")


def main() -> None:
    model = load_layer("power_flow", ("powerflow", "dynamics"))

    report(model, "Shipped dynamics profile, before any machine model", "dynamics")
    report(model, "A profile that requires a machine model on every hydro unit",
           str(HERE / "synchronous_hydro.yaml"))

    print("Link an empty machine type to the nuclear unit")
    model.add_entity("DynamicMachineModelType.Synchronous", "dynamic_model_type.nuclear.steam")
    model.add_relation(NUCLEAR, "usesDynamicModelType", "dynamic_model_type.nuclear.steam")
    stored = model.get_attr_value(
        "DynamicMachineModelType.Synchronous", "dynamic_model_type.nuclear.steam", "inertia_constant")
    effective = model.get_effective_attribute_value(
        "dynamic_model_type.nuclear.steam", "inertia_constant")
    print(f"    inertia_constant stored={stored!r}  effective={effective!r}  (schema default)")
    report(model, "Shipped dynamics profile, empty machine type", "dynamics")

    print("Set the one attribute that has no default")
    model.add_attribute("dynamic_model_type.nuclear.steam", "machine_model_order", ORDER)
    report(model, "Shipped dynamics profile, only machine_model_order set", "dynamics")

    print("Subtransient model, one type per construction class")
    attach_synchronous(model)
    print_machines(model)
    report(model, "Shipped dynamics profile, class-typical parameters set", "dynamics")
    report(model, "Hydro units now have a machine model and a rated base",
           str(HERE / "synchronous_hydro.yaml"))

    skipped = [
        eid for cls in ("WindGenerationUnit", "SolarGenerationUnit")
        for eid in model.get_entities(cls)
    ]
    print("No synchronous model: " + ", ".join(skipped))
    save_layer(model, "dynamics")


if __name__ == "__main__":
    main()
