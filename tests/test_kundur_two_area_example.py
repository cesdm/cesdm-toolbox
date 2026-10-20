# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

"""Kundur two-area example is analysis-ready for power flow and dynamics."""

from __future__ import annotations

from pathlib import Path

from cesdm_toolbox import build_model_from_yaml

REPO_ROOT = Path(__file__).resolve().parents[1]


def _build_kundur():
    from examples.example_kundur_two_area import SCHEMA_DIRS, build_kundur

    model = build_model_from_yaml([str(path) for path in SCHEMA_DIRS])
    build_kundur(model)
    return model


def test_kundur_schema_validation_is_clean():
    assert _build_kundur().validate() == []


def test_kundur_passes_power_flow_analysis_profile():
    assert _build_kundur().validate_for_analysis("power_flow") == []


def test_kundur_passes_dynamics_analysis_profile():
    assert _build_kundur().validate_for_analysis("dynamics") == []


def test_kundur_network_matches_example_12_6():
    """Line, shunt and inertia data are Example 12.6 on a 100 MVA, 230 kV base."""
    from examples.example_kundur_two_area import solve_power_flow

    model = _build_kundur()
    pairs = []
    for line_id, ends in (
        ("line.l3a", ("bus.7", "bus.8")),
        ("line.l3b", ("bus.7", "bus.8")),
        ("line.l4a", ("bus.8", "bus.9")),
        ("line.l4b", ("bus.8", "bus.9")),
    ):
        line = model.get_entity(entity_id=line_id)
        length = line.power_flow.line_length
        pairs.append((
            line.power_flow.series_resistance_per_km * length,
            line.power_flow.series_reactance_per_km * length,
            line.power_flow.shunt_susceptance_per_km * length,
        ))
        assert set(model.get_relation_targets(line_id, "fromNode")
                   + model.get_relation_targets(line_id, "toNode")) == set(ends)
    # 110 km: r = 0.011 pu, x = 0.11 pu, b = 0.1925 pu, Zbase = 529 ohm.
    for r_ohm, x_ohm, b_s in pairs:
        assert abs(r_ohm - 0.011 * 529) < 1e-3
        assert abs(x_ohm - 0.11 * 529) < 1e-3
        assert abs(b_s - 0.1925 / 529) < 1e-6

    short = model.get_entity(entity_id="line.l1").power_flow
    assert abs(short.series_reactance_per_km * short.line_length - 0.025 * 529) < 1e-3

    assert model.get_entity(entity_id="shunt.c7").power_flow.reactive_power_injection == 200
    assert model.get_entity(entity_id="shunt.c9").power_flow.reactive_power_injection == 350

    area1 = model.get_entity(entity_id="dynamic_model_type.kundur.area1")
    area2 = model.get_entity(entity_id="dynamic_model_type.kundur.area2")
    assert area1.inertia_constant == 6.5
    assert area2.inertia_constant == 6.175

    solved = solve_power_flow(model)
    assert abs(solved["tie_7_8_mw"] - 400) < 5
