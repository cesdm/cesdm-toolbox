#!/usr/bin/env python3
"""Part 2, step 2: the dispatch layer.

    python docs/examples/swiss-analyses/step2_dispatch.py

Reads output/swiss-analyses/system.yaml and appends the hourly dispatch.
The annual balance in that file is already complete. The hourly profile
is not, until this step adds stylised demand, wind, PV and inflow shapes
and writes output/swiss-analyses/dispatch.yaml. The plants stay the same
objects.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from step1_complete import load_layer, save_layer, summarise  # noqa: E402
from step1_complete import MODELS  # noqa: E402

HOURS = 8760
MONTH_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
# Full-load hours of the stylised availability, so the annual resource
# is capacity times this number. Not a measured Swiss weather year.
WIND_FULL_LOAD_HOURS = 2000.0
PV_FULL_LOAD_HOURS = 1000.0
TS_ID = "ts.hourly.2030"


def _month_starts() -> list[int]:
    starts = []
    hour = 0
    for days in MONTH_DAYS:
        starts.append(hour)
        hour += days * 24
    return starts


MONTH_STARTS = _month_starts()


def _scale(raw: list[float], total: float) -> list[float]:
    factor = total / sum(raw)
    return [value * factor for value in raw]


def demand_share() -> list[float]:
    """Share of annual energy in each hour. Sums to 1. Winter evenings are higher."""
    raw = []
    for hour in range(HOURS):
        day = hour / 24.0
        clock = hour % 24
        season = 1.0 + 0.35 * math.cos(2.0 * math.pi * (day - 15.0) / 365.0)
        morning = math.exp(-((clock - 8.0) ** 2) / 10.0)
        evening = math.exp(-((clock - 19.0) ** 2) / 8.0)
        raw.append(season * (0.72 + 0.16 * morning + 0.28 * evening))
    return _scale(raw, 1.0)


def wind_capacity_factor() -> list[float]:
    """Higher in winter. Mean is WIND_FULL_LOAD_HOURS / 8760."""
    raw = []
    for hour in range(HOURS):
        day = hour / 24.0
        season = 1.0 + 0.35 * math.cos(2.0 * math.pi * (day - 15.0) / 365.0)
        weather = 0.12 * math.sin(2.0 * math.pi * hour / (24.0 * 5.0))
        raw.append(season + weather)
    return _scale(raw, WIND_FULL_LOAD_HOURS)


def pv_capacity_factor() -> list[float]:
    """Zero at night, higher in summer. Sums to PV_FULL_LOAD_HOURS."""
    raw = []
    for hour in range(HOURS):
        day = hour / 24.0
        clock = hour % 24
        elevation = math.sin((clock - 6.0) * math.pi / 13.0)
        if elevation < 0.0:
            raw.append(0.0)
            continue
        # 0.35 in midwinter to 1.0 near the summer solstice. Never negative.
        season = 0.675 + 0.325 * math.cos(2.0 * math.pi * (day - 172.0) / 365.0)
        raw.append(elevation * season)
    return _scale(raw, PV_FULL_LOAD_HOURS)


def inflow_share(peak_day: float, width_days: float, base: float) -> list[float]:
    """Share of annual inflow in each hour. Sums to 1."""
    raw = []
    for hour in range(HOURS):
        day = hour / 24.0
        pulse = math.exp(-((day - peak_day) ** 2) / (2.0 * width_days ** 2))
        raw.append(base + pulse)
    return _scale(raw, 1.0)


def _span(series: list[float], first_month: int, last_month: int) -> float:
    """Share of a normalised series between two months, inclusive, 0-based."""
    start = MONTH_STARTS[first_month]
    end = HOURS if last_month == 11 else MONTH_STARTS[last_month + 1]
    return sum(series[start:end])


def report(model, title: str) -> None:
    gaps = model.validate_for_analysis("optimal_dispatch")
    print(title)
    print(f"    {len(gaps)} gaps")
    for (cls, attribute), n in sorted(summarise(gaps).items()):
        print(f"      {cls:22s} {attribute:30s} ×{n}")


def plant_mw(model, entity_id: str) -> float:
    for cls in ("WindGenerationUnit", "SolarGenerationUnit", "HydroGenerationUnit", "GenerationUnit"):
        value = model.get_attr_value(cls, entity_id, "nominal_power_capacity")
        if value is not None:
            return float(value)
    raise KeyError(entity_id)


def hour_index(month: int, day: int, clock: int) -> int:
    """1-based month and day, hour 0–23. 2030 is not a leap year."""
    return MONTH_STARTS[month - 1] + (day - 1) * 24 + clock


def _attr(model, entity_id: str, name: str) -> float:
    for cls in (
        "DemandUnit", "HydraulicStorageUnit", "HydroGenerationUnit",
        "WindGenerationUnit", "SolarGenerationUnit", "GenerationUnit",
    ):
        value = model.get_attr_value(cls, entity_id, name)
        if value is not None:
            return float(value)
    raise KeyError(entity_id)


def winter_evening(model) -> dict:
    """15 January, 19:00, taken from the same series this step writes.

    Must-run resources first (wind, PV, run-of-river inflow), then nuclear
    up to its capacity, then the reservoir turbine, then gas. Nuclear's
    variable cost sits below gas, so gas stays off when the reservoir can
    cover the rest. This is that stacking, not a solved dispatch.
    """
    hour = hour_index(1, 15, 19)
    demand = demand_share()[hour] * _attr(model, "demand.CH", "annual_energy_demand")
    wind = wind_capacity_factor()[hour] * plant_mw(model, "gen.CH_WIND")
    pv = pv_capacity_factor()[hour] * plant_mw(model, "gen.CH_PV")
    ror = min(
        plant_mw(model, "gen.CH_HYD_ROR"),
        inflow_share(peak_day=135.0, width_days=55.0, base=0.35)[hour]
        * _attr(model, "storage.CH_ROR", "annual_natural_inflow_energy"),
    )
    remaining = demand - wind - pv - ror
    nuclear = min(plant_mw(model, "gen.CH_NUC"), max(0.0, remaining))
    remaining -= nuclear
    reservoir = min(plant_mw(model, "gen.CH_HYD_RES"), max(0.0, remaining))
    remaining -= reservoir
    gas = min(plant_mw(model, "gen.CH_GAS"), max(0.0, remaining))
    plants = {
        "gen.CH_NUC": nuclear,
        "gen.CH_HYD_RES": reservoir,
        "gen.CH_HYD_ROR": ror,
        "gen.CH_GAS": gas,
        "gen.CH_WIND": wind,
        "gen.CH_PV": pv,
    }
    return {"hour": hour, "demand_mw": demand, "plants_mw": plants}


def add_profile(model, profile_id: str, profile_type: str, values: list[float], values_map: dict) -> None:
    model.add_entity("Profile", profile_id)
    model.add_attribute(profile_id, "profile_type", profile_type)
    model.add_attribute(profile_id, "profile_unit", "pu")
    model.add_attribute(profile_id, "data_reference", f"profiles.h5:/profiles/{profile_id}")
    model.add_relation(profile_id, "hasTimestampSeries", TS_ID)
    values_map[profile_id] = values


def add_dispatch(model) -> dict:
    """Hourly shapes and the wind and PV annual resource. Returns the series."""
    model.add_entity("TimestampSeries", TS_ID)
    model.add_attribute(TS_ID, "start_datetime", "2030-01-01T00:00:00")
    model.add_attribute(TS_ID, "resolution", "PT1H")
    model.add_attribute(TS_ID, "length", HOURS)
    model.add_attribute(TS_ID, "timezone", "Europe/Zurich")

    series = {
        "demand": demand_share(),
        "wind": wind_capacity_factor(),
        "pv": pv_capacity_factor(),
        "inflow_res": inflow_share(peak_day=196.0, width_days=40.0, base=0.08),
        "inflow_ror": inflow_share(peak_day=135.0, width_days=55.0, base=0.35),
    }
    values_map: dict[str, list[float]] = {}
    add_profile(model, "profile.demand.CH", "as_normalized_annual_energy", series["demand"], values_map)
    add_profile(model, "profile.wind.CH", "as_capacity_factor", series["wind"], values_map)
    add_profile(model, "profile.pv.CH", "as_capacity_factor", series["pv"], values_map)
    add_profile(model, "profile.inflow.CH_RES", "as_normalized_annual_energy", series["inflow_res"], values_map)
    add_profile(model, "profile.inflow.CH_ROR", "as_normalized_annual_energy", series["inflow_ror"], values_map)

    model.add_relation("demand.CH", "hasDemandProfile", "profile.demand.CH")
    model.add_relation("gen.CH_WIND", "hasAvailabilityProfile", "profile.wind.CH")
    model.add_relation("gen.CH_PV", "hasAvailabilityProfile", "profile.pv.CH")
    model.add_relation("storage.CH_RES", "hasNaturalInflowProfile", "profile.inflow.CH_RES")
    model.add_relation("storage.CH_ROR", "hasNaturalInflowProfile", "profile.inflow.CH_ROR")

    wind_mw = plant_mw(model, "gen.CH_WIND")
    pv_mw = plant_mw(model, "gen.CH_PV")
    model.add_attribute("gen.CH_WIND", "annual_resource_potential", wind_mw * WIND_FULL_LOAD_HOURS, unit="MWh/year")
    model.add_attribute("gen.CH_PV", "annual_resource_potential", pv_mw * PV_FULL_LOAD_HOURS, unit="MWh/year")
    series["values_map"] = values_map
    series["wind_mw"] = wind_mw
    series["pv_mw"] = pv_mw
    return series


def print_shapes(series: dict) -> None:
    demand = series["demand"]
    annual_mwh = 58_000_000.0
    peak_mw = max(demand) * annual_mwh
    print("Hourly shapes, stylised, year 2030")
    print(f"    demand peak {peak_mw:.0f} MW"
          f"   winter(DJF) {100 * (_span(demand, 11, 11) + _span(demand, 0, 1)):.0f}%"
          f"   summer(JJA) {100 * _span(demand, 5, 7):.0f}%")
    print(f"    wind  {series['wind_mw']:.0f} MW × {WIND_FULL_LOAD_HOURS:.0f} h"
          f" = {series['wind_mw'] * WIND_FULL_LOAD_HOURS / 1e6:.1f} TWh/year"
          f"   cf {min(series['wind']):.2f}–{max(series['wind']):.2f}")
    print(f"    pv    {series['pv_mw']:.0f} MW × {PV_FULL_LOAD_HOURS:.0f} h"
          f" = {series['pv_mw'] * PV_FULL_LOAD_HOURS / 1e6:.1f} TWh/year"
          f"   cf {min(series['pv']):.2f}–{max(series['pv']):.2f}")
    print(f"    reservoir inflow  Jun–Aug {100 * _span(series['inflow_res'], 5, 7):.0f}%"
          f"   Dec–Feb {100 * (_span(series['inflow_res'], 11, 11) + _span(series['inflow_res'], 0, 1)):.0f}%")
    print(f"    run-of-river inflow  Apr–Jun {100 * _span(series['inflow_ror'], 3, 5):.0f}%"
          f"   Dec–Feb {100 * (_span(series['inflow_ror'], 11, 11) + _span(series['inflow_ror'], 0, 1)):.0f}%")
    for name in ("wind", "pv"):
        lo, hi = min(series[name]), max(series[name])
        if lo < -1e-9 or hi > 1.0 + 1e-9:
            raise SystemExit(f"{name} capacity factor outside 0–1: {lo:.3f}–{hi:.3f}")


def write_hdf5(model, values_map: dict) -> None:
    try:
        import numpy as np
    except ImportError:
        print("numpy is not installed; profile metadata is in the model, values were not written")
        return
    path = MODELS / "profiles.h5"
    arrays = {key: np.asarray(values, dtype=np.float64) for key, values in values_map.items()}
    model.export_hdf5(path, values_map=arrays)
    print(f"profiles.h5  {len(arrays)} series × {HOURS} h")


def main() -> None:
    model = load_layer("system")

    print("Is it complete for the four groups' annual dispatch?")
    annual = model.validate_for_analysis(str(HERE / "annual_dispatch.yaml"))
    print(f"    annual_dispatch: {len(annual)} gaps")

    report(model, "Before the hourly shapes")
    series = add_dispatch(model)
    print_shapes(series)
    report(model, "After the hourly shapes")
    print(f"Schema check: {len(model.validate())} errors")
    save_layer(model, "dispatch")
    write_hdf5(model, series["values_map"])


if __name__ == "__main__":
    main()
