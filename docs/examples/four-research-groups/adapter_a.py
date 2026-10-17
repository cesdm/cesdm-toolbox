"""Group A: semicolon CSV, German headers, numeric technology codes.

    regions.csv   ID;Bezeichnung
    load.csv      Region;E_Jahr                      GWh/year
    plants.csv    ID;Region;Pmax;Typ;Eta;VarKosten   MW, code, percent, EUR/MWh
    storage.csv   ID;Region;E_speicher;Zufluss       MWh, MWh/year

The functions that touch CESDM live in this file. A reservoir and a
run-of-river plant are both a HydroGenerationUnit drawing from a
HydraulicStorageUnit.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


def _repository() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        if (candidate / "schemas" / "cesdm").is_dir():
            return candidate
    raise FileNotFoundError("Run this from inside the cesdm-toolbox repository.")


_REPO = _repository()
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cesdm_toolbox import build_model_from_yaml  # noqa: E402
from ear import get_attr_value  # noqa: E402

SOURCE = "group-a"


def leeres_modell():
    """Schema, technologies and regions. Group A opens this itself."""
    model = build_model_from_yaml(str(_REPO / "schemas" / "cesdm"))
    for library in ("default_library", "regions_library"):
        model.import_library(str(_REPO / "library" / library))
    return model


def yaml_einlesen(path) -> object:
    """A CESDM file another group sent, opened with Group A's schema and libraries."""
    model = leeres_modell()
    model.import_yaml(str(path))
    return model


def zahl(x: float):
    x = round(float(x), 9)
    return int(x) if x.is_integer() else x

# --- The mapping tables: one row per code, used in both directions --------
REGIONS = {"CH": ("region.country.CH", "Schweiz")}

# The code names the group's own technology. It is not a library GeneratorType:
# efficiency and variable cost come from the row.
TYP = {
    1: "ccgt",
    2: "nuclear",
    3: "wind",
    4: "solar",
    6: "reservoir_hydro",
    7: "run_of_river",
}
RESERVOIR, RUN_OF_RIVER = 6, 7
TECH_TO_TYP = {tech: typ for typ, tech in TYP.items()}
REGION_TO_CODE = {cesdm: code for code, (cesdm, _) in REGIONS.items()}

_KLASSE = {
    "wind": "WindGenerationUnit",
    "solar": "SolarGenerationUnit",
}
_GENERATOR_CLASSES = (
    "GenerationUnit", "WindGenerationUnit", "SolarGenerationUnit", "HydroGenerationUnit",
)


def _read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def _write(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def to_cesdm(folder: Path, model) -> None:
    for row in _read(folder / "load.csv"):
        region = REGIONS[row["Region"]][0]
        eid = f"demand.{row['Region']}"
        model.add_entity("DemandUnit", eid)
        model.add_relation(eid, "belongsToGeographicalRegion", region)
        model.add_attribute(eid, "annual_energy_demand", float(row["E_Jahr"]) * 1000,
                            unit="MWh/year", provenance_ref=SOURCE)  # GWh -> MWh

    # Group A links hydro plants to storage rows only by convention:
    # in the same region, the row with E_speicher > 0 belongs to the Typ 6 plant,
    # the row with E_speicher = 0 to the Typ 7 plant. CESDM makes the link explicit.
    storage = {}
    for row in _read(folder / "storage.csv"):
        kind = RESERVOIR if float(row["E_speicher"]) > 0 else RUN_OF_RIVER
        storage[(row["Region"], kind)] = row

    for row in _read(folder / "plants.csv"):
        typ = int(row["Typ"])
        region = REGIONS[row["Region"]][0]
        art = TYP[typ]
        eid = f"gen.{row['ID']}"
        if typ in (RESERVOIR, RUN_OF_RIVER):
            model.add_entity("HydroGenerationUnit", eid)
        else:
            model.add_entity(_KLASSE.get(art, "GenerationUnit"), eid)
        model.add_relation(eid, "belongsToGeographicalRegion", region)
        model.add_attribute(eid, "nominal_power_capacity", float(row["Pmax"]),
                            unit="MW", provenance_ref=SOURCE)
        model.add_attribute(eid, "generator_technology_type", art)
        # Wind and PV have no fuel conversion, so Eta is left empty.
        if str(row["Eta"]).strip():
            model.add_attribute(eid, "energy_conversion_efficiency", float(row["Eta"]) / 100,
                                unit="fraction", provenance_ref=SOURCE)   # percent -> fraction
        model.add_attribute(eid, "variable_operating_cost", float(row["VarKosten"]),
                            unit="MU/MWh", provenance_ref=SOURCE)         # EUR/MWh, stored as MU/MWh
        if typ in (RESERVOIR, RUN_OF_RIVER):
            s = storage[(row["Region"], typ)]
            basin = f"storage.{s['ID']}"
            model.add_entity("HydraulicStorageUnit", basin)
            model.add_attribute(basin, "energy_storage_capacity", float(s["E_speicher"]),
                                unit="MWh", provenance_ref=SOURCE)
            model.add_attribute(basin, "annual_natural_inflow_energy", float(s["Zufluss"]),
                                unit="MWh/year", provenance_ref=SOURCE)
            model.add_relation(eid, "drawsFromHydraulicStorage", basin)


def from_cesdm(model, folder: Path) -> None:
    folder.mkdir(parents=True, exist_ok=True)
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
        {"region": unit.get_relation("belongsToGeographicalRegion"),
         "annual_mwh": get_attr_value(unit, "annual_energy_demand")}
        for unit in model.get_entities("DemandUnit").values()
    ]

    codes = sorted({REGION_TO_CODE[p["region"]] for p in plants})
    _write(folder / "regions.csv", ["ID", "Bezeichnung"],
           [[c, REGIONS[c][1]] for c in codes])
    _write(folder / "load.csv", ["Region", "E_Jahr"],
           [[REGION_TO_CODE[d["region"]], zahl(d["annual_mwh"] / 1000)] for d in demand])
    _write(folder / "plants.csv", ["ID", "Region", "Pmax", "Typ", "Eta", "VarKosten"],
           [[p["id"], REGION_TO_CODE[p["region"]], zahl(p["capacity_mw"]), TECH_TO_TYP[p["technology"]],
             "" if p["efficiency"] is None else zahl(p["efficiency"] * 100), zahl(p["variable_cost"])]
            for p in plants])
    _write(folder / "storage.csv", ["ID", "Region", "E_speicher", "Zufluss"],
           [[p["storage_id"], REGION_TO_CODE[p["region"]], zahl(p["storage_mwh"]),
             zahl(p["inflow_mwh_per_year"])]
            for p in plants if "storage_id" in p])
