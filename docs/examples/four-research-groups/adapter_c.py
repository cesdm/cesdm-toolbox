"""Group C: one YAML file, nested by region, GW and TWh.

    regions:
      CHE:
        demand_twh: 58
        plants:
          - {id: hydro, tech: reservoir_hydro, cap_gw: 8.5,
             reservoir_id: CHE_RES, reservoir_twh: 8.8, inflow_twh: 20}
          - {id: ror, tech: run_of_river, cap_gw: 4.0, inflow_twh: 16}

Hydro storage sits on the plant in this file. In CESDM it is still a
HydroGenerationUnit linked to a HydraulicStorageUnit.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


def _find_repo() -> Path:
    cursor = Path(__file__).resolve().parent
    while True:
        if (cursor / "schemas" / "cesdm").is_dir():
            return cursor
        if cursor.parent == cursor:
            raise FileNotFoundError("cesdm-toolbox repository not found")
        cursor = cursor.parent


_REPO = _find_repo()
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cesdm_toolbox import build_model_from_yaml  # noqa: E402
from ear import get_attr_value  # noqa: E402

SOURCE = "group-c"


def start_case():
    """Group C's empty case: schema plus the two shared libraries."""
    model = build_model_from_yaml(str(_REPO / "schemas/cesdm"))
    libraries = [
        _REPO / "library" / "default_library",
        _REPO / "library" / "regions_library",
    ]
    for path in libraries:
        model.import_library(str(path))
    return model


def case_from_file(path):
    model = start_case()
    model.import_yaml(str(path))
    return model


def scalar(x: float):
    rounded = round(float(x), 9)
    return int(rounded) if rounded.is_integer() else rounded

REGIONS = {"CHE": ("region.country.CH", "Switzerland")}

# Group C's tech name becomes a category. eta and var_cost are on the plant.
TECH = {
    "ccgt": "ccgt",
    "nuclear": "nuclear",
    "onshore_wind": "wind",
    "solar_pv": "solar",
    "reservoir_hydro": "reservoir_hydro",
    "run_of_river": "run_of_river",
}
CESDM_TO_TECH = {cesdm: t for t, cesdm in TECH.items()}
REGION_TO_CODE = {cesdm: code for code, (cesdm, _) in REGIONS.items()}


_ASSET = {
    "onshore_wind": "WindGenerationUnit",
    "solar_pv": "SolarGenerationUnit",
}


def to_cesdm(path: Path, model) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for code, region_block in data["regions"].items():
        region = REGIONS[code][0]
        demand = f"demand.{code}"
        model.add_entity("DemandUnit", demand)
        model.add_relation(demand, "belongsToGeographicalRegion", region)
        model.add_attribute(demand, "annual_energy_demand", region_block["demand_twh"] * 1e6,
                            unit="MWh/year", provenance_ref=SOURCE)  # TWh -> MWh
        for plant in region_block["plants"]:
            eid = f"gen.{plant['id']}"
            hydro = "inflow_twh" in plant
            model.add_entity("HydroGenerationUnit" if hydro else _ASSET.get(plant["tech"], "GenerationUnit"), eid)
            model.add_relation(eid, "belongsToGeographicalRegion", region)
            model.add_attribute(eid, "nominal_power_capacity", plant["cap_gw"] * 1000,
                                unit="MW", provenance_ref=SOURCE)  # GW -> MW
            model.add_attribute(eid, "generator_technology_type", TECH[plant["tech"]])
            if plant.get("eta") not in (None, ""):
                model.add_attribute(eid, "energy_conversion_efficiency", plant["eta"],
                                    unit="fraction", provenance_ref=SOURCE)
            model.add_attribute(eid, "variable_operating_cost", plant["var_cost"],
                                unit="MU/MWh", provenance_ref=SOURCE)
            if hydro:
                basin_id = plant.get("reservoir_id", f"{plant['id']}_inflow")
                basin = f"storage.{basin_id}"
                model.add_entity("HydraulicStorageUnit", basin)
                model.add_attribute(basin, "energy_storage_capacity", plant.get("reservoir_twh", 0) * 1e6,
                                    unit="MWh", provenance_ref=SOURCE)
                model.add_attribute(basin, "annual_natural_inflow_energy", plant["inflow_twh"] * 1e6,
                                    unit="MWh/year", provenance_ref=SOURCE)
                model.add_relation(eid, "drawsFromHydraulicStorage", basin)


def from_cesdm(model, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    basins = model.get_entities("HydraulicStorageUnit")
    regions: dict = {}
    for demand in model.get_entities("DemandUnit").values():
        code = REGION_TO_CODE[demand.get_relation("belongsToGeographicalRegion")]
        regions[code] = {
            "name": REGIONS[code][1],
            "demand_twh": scalar(get_attr_value(demand, "annual_energy_demand") / 1e6),
            "plants": [],
        }
    for cls in ("GenerationUnit", "WindGenerationUnit", "SolarGenerationUnit", "HydroGenerationUnit"):
        for eid, gen in model.get_entities(cls).items():
            code = REGION_TO_CODE[gen.get_relation("belongsToGeographicalRegion")]
            plant = {
                "id": eid.removeprefix("gen."),
                "tech": CESDM_TO_TECH[get_attr_value(gen, "generator_technology_type")],
                "cap_gw": scalar(get_attr_value(gen, "nominal_power_capacity") / 1000),
                "var_cost": scalar(get_attr_value(gen, "variable_operating_cost")),
            }
            eta = get_attr_value(gen, "energy_conversion_efficiency")
            if eta is not None:
                plant["eta"] = scalar(eta)
            sid = gen.get_relation("drawsFromHydraulicStorage")
            if sid:
                basin = basins[sid]
                stored = get_attr_value(basin, "energy_storage_capacity")
                if stored > 0:
                    plant["reservoir_id"] = sid.removeprefix("storage.")
                    plant["reservoir_twh"] = scalar(stored / 1e6)
                plant["inflow_twh"] = scalar(get_attr_value(basin, "annual_natural_inflow_energy") / 1e6)
            regions[code]["plants"].append(plant)
    data = {
        "problem": "economic_dispatch",
        "units": {"capacity": "GW", "energy": "TWh"},
        "regions": regions,
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
