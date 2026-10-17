"""Compare two CESDM models by meaning, not by identifiers.

Each group names its plants differently (CH_NUC, nuc, che-nuc). What they agree
on is the region and the technology category. Efficiency and variable cost are
the group's own numbers, not a library technology.

    python compare.py output/four-research-groups/group_a.yaml output/four-research-groups/group_d.yaml
"""

from __future__ import annotations

import math
import sys

from cesdm_common import load
from ear import get_attr_value  # noqa: E402  (cesdm_common puts this repo on sys.path)

_GENERATOR_CLASSES = (
    "GenerationUnit", "WindGenerationUnit", "SolarGenerationUnit", "HydroGenerationUnit",
)


def read_system(model) -> dict:
    """Plain records in CESDM units, for comparison across groups.

    Hydro, reservoir and run-of-river, is a HydroGenerationUnit drawing from
    a HydraulicStorageUnit. The plant id and the basin id stay separate.
    """
    basins = model.get_entities("HydraulicStorageUnit")
    plants = []
    for cls in _GENERATOR_CLASSES:
        for eid, gen in model.get_entities(cls).items():
            record = {
                "id": eid.removeprefix("gen."),
                "region": gen.get_relation("belongsToGeographicalRegion"),
                "technology": get_attr_value(gen, "generator_technology_type"),
                "capacity_mw": get_attr_value(gen, "nominal_power_capacity"),
                "efficiency": get_attr_value(gen, "energy_conversion_efficiency"),
                "variable_cost": get_attr_value(gen, "variable_operating_cost"),
            }
            sid = gen.get_relation("drawsFromHydraulicStorage")
            if sid:
                basin = basins[sid]
                record.update(
                    storage_id=sid.removeprefix("storage."),
                    storage_mwh=get_attr_value(basin, "energy_storage_capacity"),
                    inflow_mwh_per_year=get_attr_value(basin, "annual_natural_inflow_energy"),
                )
            plants.append(record)
    demand = [
        {"region": d.get_relation("belongsToGeographicalRegion"),
         "annual_mwh": get_attr_value(d, "annual_energy_demand")}
        for d in model.get_entities("DemandUnit").values()
    ]
    return {"plants": plants, "demand": demand}

FIELDS = [("capacity_mw", "capacity", "MW"),
          ("efficiency", "efficiency", "fraction"),
          ("variable_cost", "variable cost", "MU/MWh"),
          ("storage_mwh", "reservoir energy", "MWh"),
          ("inflow_mwh_per_year", "annual inflow", "MWh/year")]


def _fmt(v) -> str:
    return "missing" if v is None else f"{v:,.12g}"


def _short(cesdm_id: str) -> str:
    return cesdm_id.split(".")[-1]


def compare(model_x, model_y, x="first", y="second") -> list[str]:
    sx, sy = read_system(model_x), read_system(model_y)
    plants_x = {(p["region"], p["technology"]): p for p in sx["plants"]}
    plants_y = {(p["region"], p["technology"]): p for p in sy["plants"]}
    diffs = []

    for key in sorted(plants_x.keys() | plants_y.keys()):
        region, tech = key
        label = f"{tech} in {_short(region)}"
        if key not in plants_y:
            diffs.append(f"{label}: only in {x}")
            continue
        if key not in plants_x:
            diffs.append(f"{label}: only in {y}")
            continue
        for field, name, unit in FIELDS:
            a, b = plants_x[key].get(field), plants_y[key].get(field)
            if a is None and b is None:
                continue
            if a is None or b is None or not math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9):
                diffs.append(f"{label}: {name} {_fmt(a)} {unit} ({x}) vs {_fmt(b)} {unit} ({y})")

    demand_x = {d["region"]: d["annual_mwh"] for d in sx["demand"]}
    demand_y = {d["region"]: d["annual_mwh"] for d in sy["demand"]}
    for region in sorted(demand_x.keys() | demand_y.keys()):
        a, b = demand_x.get(region), demand_y.get(region)
        if a is None or b is None or not math.isclose(a, b, rel_tol=1e-9):
            diffs.append(f"demand in {_short(region)}: {_fmt(a)} MWh/year ({x}) vs {_fmt(b)} MWh/year ({y})")
    return diffs


if __name__ == "__main__":
    from pathlib import Path
    first, second = sys.argv[1], sys.argv[2]
    differences = compare(load(first), load(second), Path(first).stem, Path(second).stem)
    print(f"{len(differences)} differences")
    for d in differences:
        print(" -", d)
