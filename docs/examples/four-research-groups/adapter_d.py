"""Group D: JSON with flat lists, capacities in kW.

    {"regions":    [{"code": "CHE", "label": "Switzerland"}],
     "demand":     [{"region": "CHE", "annual_mwh": 58000000}],
     "generators": [{"id": "che-hydro", "region": "CHE", "technology": "reservoir_hydro",
                     "capacity_kw": 8500000, "reservoir_id": "CHE_RES",
                     "reservoir_mwh": 8800000, "inflow_mwh": 20000000}, ...]}

A hydro generator in this file carries its basin on the same object. The
CESDM objects this adapter creates are still two: the machine and the reservoir.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _repo_with_schema() -> Path:
    for folder in Path(__file__).resolve().parents:
        if (folder / "schemas" / "cesdm").is_dir():
            return folder
    raise FileNotFoundError("schemas/cesdm is not above this file")


_REPO = _repo_with_schema()
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cesdm_toolbox import build_model_from_yaml  # noqa: E402
from ear import get_attr_value  # noqa: E402

SOURCE = "group-d"


def _attach_libraries(model):
    model.import_library(str(_REPO / "library" / "default_library"))
    model.import_library(str(_REPO / "library" / "regions_library"))
    return model


def empty_document():
    return _attach_libraries(build_model_from_yaml(str(_REPO / "schemas" / "cesdm")))


def document_from_yaml(path):
    model = empty_document()
    model.import_yaml(str(path))
    return model


def json_number(x: float):
    x = round(float(x), 9)
    return int(x) if x.is_integer() else x

REGIONS = {"CHE": ("region.country.CH", "Switzerland")}

# Group D's technology name becomes a category. Efficiency is a percent;
# variable cost is EUR/kWh and is stored as MU/MWh.
TECH = {
    "gas_ccgt": "ccgt",
    "nuclear": "nuclear",
    "wind_onshore": "wind",
    "solar_pv": "solar",
    "reservoir_hydro": "reservoir_hydro",
    "run_of_river": "run_of_river",
}
CESDM_TO_TECH = {cesdm: t for t, cesdm in TECH.items()}
REGION_TO_CODE = {cesdm: code for code, (cesdm, _) in REGIONS.items()}


_CLASS = {
    "wind_onshore": "WindGenerationUnit",
    "solar_pv": "SolarGenerationUnit",
}


def to_cesdm(path: Path, model) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    for item in data["demand"]:
        eid = f"demand.{item['region']}"
        model.add_entity("DemandUnit", eid)
        model.add_relation(eid, "belongsToGeographicalRegion", REGIONS[item["region"]][0])
        model.add_attribute(eid, "annual_energy_demand", item["annual_mwh"],
                            unit="MWh/year", provenance_ref=SOURCE)
    for item in data["generators"]:
        eid = f"gen.{item['id']}"
        hydro = "inflow_mwh" in item
        model.add_entity("HydroGenerationUnit" if hydro else _CLASS.get(item["technology"], "GenerationUnit"), eid)
        model.add_relation(eid, "belongsToGeographicalRegion", REGIONS[item["region"]][0])
        model.add_attribute(eid, "nominal_power_capacity", item["capacity_kw"] / 1000,
                            unit="MW", provenance_ref=SOURCE)  # kW -> MW
        model.add_attribute(eid, "generator_technology_type", TECH[item["technology"]])
        if item.get("efficiency_pc") not in (None, ""):
            model.add_attribute(eid, "energy_conversion_efficiency", item["efficiency_pc"] / 100,
                                unit="fraction", provenance_ref=SOURCE)
        model.add_attribute(eid, "variable_operating_cost", item["variable_cost_eur_per_kwh"] * 1000,
                            unit="MU/MWh", provenance_ref=SOURCE)  # EUR/kWh -> MU/MWh
        if hydro:
            basin = f"storage.{item.get('reservoir_id', item['id'] + '-inflow')}"
            model.add_entity("HydraulicStorageUnit", basin)
            model.add_attribute(basin, "energy_storage_capacity", item.get("reservoir_mwh", 0),
                                unit="MWh", provenance_ref=SOURCE)
            model.add_attribute(basin, "annual_natural_inflow_energy", item["inflow_mwh"],
                                unit="MWh/year", provenance_ref=SOURCE)
            model.add_relation(eid, "drawsFromHydraulicStorage", basin)


def from_cesdm(model, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    basins = model.get_entities("HydraulicStorageUnit")
    generators = []
    for cls in ("GenerationUnit", "WindGenerationUnit", "SolarGenerationUnit", "HydroGenerationUnit"):
        for eid, gen in model.get_entities(cls).items():
            item = {
                "id": eid.removeprefix("gen."),
                "region": REGION_TO_CODE[gen.get_relation("belongsToGeographicalRegion")],
                "technology": CESDM_TO_TECH[get_attr_value(gen, "generator_technology_type")],
                "capacity_kw": json_number(get_attr_value(gen, "nominal_power_capacity") * 1000),
                "variable_cost_eur_per_kwh": json_number(
                    get_attr_value(gen, "variable_operating_cost") / 1000),
            }
            efficiency = get_attr_value(gen, "energy_conversion_efficiency")
            if efficiency is not None:
                item["efficiency_pc"] = json_number(efficiency * 100)
            sid = gen.get_relation("drawsFromHydraulicStorage")
            if sid:
                basin = basins[sid]
                stored = get_attr_value(basin, "energy_storage_capacity")
                if stored > 0:
                    item["reservoir_id"] = sid.removeprefix("storage.")
                    item["reservoir_mwh"] = json_number(stored)
                item["inflow_mwh"] = json_number(get_attr_value(basin, "annual_natural_inflow_energy"))
            generators.append(item)
    codes = sorted({item["region"] for item in generators})
    document = {
        "problem": "economic_dispatch",
        "units": {"capacity": "kW", "demand": "MWh/year"},
        "regions": [{"code": code, "label": REGIONS[code][1]} for code in codes],
        "demand": [
            {"region": REGION_TO_CODE[d.get_relation("belongsToGeographicalRegion")],
             "annual_mwh": json_number(get_attr_value(d, "annual_energy_demand"))}
            for d in model.get_entities("DemandUnit").values()
        ],
        "generators": generators,
    }
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")
