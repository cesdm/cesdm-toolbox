#!/usr/bin/env python3
"""Part 2, step 3: the power-flow layer.

    python docs/examples/swiss-analyses/step3_power_flow.py

Reads the dispatch file and appends one operating point — a winter
evening — and the 380 kV network that point needs. The plants, and the
hourly year already stored on them, stay.

The plants are fleet totals, so each branch is an equivalent corridor:
the impedance of one 380 kV overhead circuit, divided by a handful of
parallel circuits. It is not a model of the Swiss transmission grid.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from step1_complete import load_layer, save_layer, summarise  # noqa: E402
from step2_dispatch import winter_evening  # noqa: E402

# One 380 kV overhead circuit. Corridor equivalents divide r and x by the
# parallel count and multiply susceptance and rating by it.
CIRCUIT_R_OHM_PER_KM = 0.028
CIRCUIT_X_OHM_PER_KM = 0.260
CIRCUIT_B_MICROS_PER_KM = 4.4
CIRCUIT_MVA = 2000.0
KV = 380.0

# 15 January 19:00 of the dispatch year. Setpoints come from winter_evening().
DEMAND_POWER_FACTOR = 0.98

# bus, plants on it, powerflow_bus_type, voltage setpoint (pu) or None.
# The alpine bus is the slack: the reservoir turbine has headroom, and
# storage hydro is what balances this system. The export builds one
# ext_grid per generator on a slack bus, so run-of-river stays on its
# own PV bus and only the reservoir is the angular reference.
BUSES = [
    ("bus.ch_nuclear", ["gen.CH_NUC"], "PV", 1.02),
    ("bus.ch_gas", ["gen.CH_GAS"], "PV", 1.01),
    ("bus.ch_alpine", ["gen.CH_HYD_RES"], "slack", 1.01),
    ("bus.ch_ror", ["gen.CH_HYD_ROR"], "PV", 1.01),
    ("bus.ch_plateau", ["gen.CH_WIND", "gen.CH_PV"], "PV", 1.00),
    ("bus.ch_load", ["demand.CH"], "PQ", None),
]

# id, from, to, length km, parallel 380 kV circuits.
# One circuit is about 2000 MVA. The plateau corridor is sized for the
# wind and PV fleet (6.6 GW), not for this dark evening.
LINES = [
    ("line.nuclear_load", "bus.ch_nuclear", "bus.ch_load", 120.0, 3),
    ("line.gas_nuclear", "bus.ch_gas", "bus.ch_nuclear", 20.0, 1),
    # Reservoir 8.5 GW, plus one extra circuit so the load stays at or above 0.95 pu.
    ("line.alpine_load", "bus.ch_alpine", "bus.ch_load", 100.0, 8),
    ("line.ror_alpine", "bus.ch_ror", "bus.ch_alpine", 15.0, 3),
    ("line.plateau_load", "bus.ch_plateau", "bus.ch_load", 140.0, 4),
    ("line.nuclear_alpine", "bus.ch_nuclear", "bus.ch_alpine", 160.0, 2),
]


def report(model, title: str) -> None:
    gaps = model.validate_for_analysis("power_flow")
    print(title)
    print(f"    {len(gaps)} gaps")
    for (cls, attribute), n in sorted(summarise(gaps).items()):
        print(f"      {cls:22s} {attribute:30s} ×{n}")


def add_network(model, snapshot_mw: dict, demand_mw: float) -> list[tuple]:
    for bus_id, _plants, kind, _vm in BUSES:
        model.add_entity("ElectricalBus", bus_id)
        model.add_attribute(bus_id, "nominal_voltage", KV, unit="kV")
        model.add_attribute(bus_id, "powerflow_bus_type", kind)
        model.add_relation(bus_id, "belongsToCarrierDomain", "domain.electricity")
        model.add_relation(bus_id, "belongsToGeographicalRegion", "region.country.CH")

    for bus_id, plants, _kind, vm in BUSES:
        for eid in plants:
            model.add_relation(eid, "atNode", bus_id)
            if vm is None:
                continue
            model.add_attribute(eid, "voltage_magnitude_setpoint", vm, unit="pu")

    for eid, p_mw in snapshot_mw.items():
        model.add_attribute(eid, "active_power_setpoint", p_mw, unit="MW")
        cap = None
        for cls in ("GenerationUnit", "HydroGenerationUnit", "WindGenerationUnit", "SolarGenerationUnit"):
            cap = model.get_attr_value(cls, eid, "nominal_power_capacity")
            if cap is not None:
                break
        q_limit = 0.4 * float(cap)
        model.add_attribute(eid, "maximum_reactive_power_output", q_limit, unit="MVAr")
        model.add_attribute(eid, "minimum_reactive_power_output", -q_limit, unit="MVAr")

    q_mvar = demand_mw * math.tan(math.acos(DEMAND_POWER_FACTOR))
    model.add_attribute("demand.CH", "active_power_demand", demand_mw, unit="MW")
    model.add_attribute("demand.CH", "reactive_power_demand", round(q_mvar, 1), unit="MVAr")

    built = []
    for line_id, fb, tb, length_km, n in LINES:
        model.add_entity("TransmissionLine", line_id)
        model.add_relation(line_id, "fromNode", fb)
        model.add_relation(line_id, "toNode", tb)
        model.add_attribute(line_id, "line_length", length_km, unit="km")
        model.add_attribute(line_id, "series_resistance_per_km", CIRCUIT_R_OHM_PER_KM / n, unit="Ohm/km")
        model.add_attribute(line_id, "series_reactance_per_km", CIRCUIT_X_OHM_PER_KM / n, unit="Ohm/km")
        model.add_attribute(line_id, "shunt_susceptance_per_km", CIRCUIT_B_MICROS_PER_KM * n, unit="microS/km")
        model.add_attribute(line_id, "thermal_capacity_rating", CIRCUIT_MVA * n, unit="MVA")
        model.add_attribute(line_id, "parallel_circuit_count", n)
        built.append((line_id, fb, tb, length_km, n, CIRCUIT_MVA * n))
    return built


def print_snapshot(lines: list[tuple], snapshot_mw: dict, demand_mw: float) -> None:
    print("Winter evening, 15 January 19:00, from the dispatch profiles")
    print(f"    demand {demand_mw:.0f} MW at power factor {DEMAND_POWER_FACTOR}")
    print(f"    generation {sum(snapshot_mw.values()):.0f} MW")
    for eid, p_mw in snapshot_mw.items():
        print(f"      {eid:16} {p_mw:7.0f} MW")
    print("Corridors (equivalent of parallel 380 kV circuits)")
    for line_id, fb, tb, length_km, n, rating in lines:
        print(f"    {line_id:22} {fb} → {tb}  {length_km:.0f} km  ×{n}  {rating:.0f} MVA")


def try_pandapower(model) -> None:
    try:
        import pandapower as pp
        from tools.export_pandapower import export_pandapower_net
    except ImportError:
        print("pandapower is not installed; the CESDM power-flow data is ready without it")
        return
    net = export_pandapower_net(model, name="Swiss system, winter evening")
    pp.runpp(net)
    print("pandapower AC power flow converged")
    for _, row in net.res_bus.iterrows():
        name = net.bus.at[row.name, "name"]
        print(f"    {name:16}  {row.vm_pu:.3f} pu  {row.va_degree:7.2f} deg")
    reservoir = net.res_gen.loc[net.gen.name == "gen.CH_HYD_RES", "p_mw"]
    reservoir_p = float(reservoir.iloc[0]) if len(reservoir) else float("nan")
    losses_mw = float(net.res_ext_grid.p_mw.sum())
    slack_name = ", ".join(net.ext_grid.name.astype(str))
    print(
        f"    reservoir keeps its setpoint {reservoir_p:.0f} MW; "
        f"slack {slack_name} covers {losses_mw:.1f} MW of losses"
    )
    load_vm = float(net.res_bus.loc[net.bus.name == "bus.ch_load", "vm_pu"].iloc[0])
    cap = float(net.gen.loc[net.gen.name == "gen.CH_HYD_RES", "max_p_mw"].iloc[0])
    if load_vm < 0.95:
        raise SystemExit(f"load voltage {load_vm:.3f} pu is below 0.95")
    if reservoir_p + losses_mw > cap + 1.0:
        raise SystemExit(
            f"alpine slack injects {reservoir_p + losses_mw:.0f} MW, above the reservoir capacity {cap:.0f} MW"
        )


def main() -> None:
    model = load_layer("dispatch", "cesdm_power_flow")
    point = winter_evening(model)
    snapshot_mw = {eid: round(mw, 1) for eid, mw in point["plants_mw"].items()}
    demand_mw = round(point["demand_mw"], 1)
    if abs(sum(snapshot_mw.values()) - demand_mw) > 1.0:
        raise SystemExit(
            f"setpoints {sum(snapshot_mw.values()):.1f} MW do not meet demand {demand_mw:.1f} MW"
        )
    report(model, "Before the network")
    lines = add_network(model, snapshot_mw, demand_mw)
    report(model, "After the network")
    print(f"Schema check: {len(model.validate())} errors")
    save_layer(model, "power_flow")
    print_snapshot(lines, snapshot_mw, demand_mw)
    try_pandapower(model)


if __name__ == "__main__":
    main()
