"""Team B: engineering. Smart-meter and asset data of the same households.

One JSON file per year. The team's conventions, written down once, here:

- household ids as "ll01"; the living lab's register writes "hh.ll01";
- consumption in kWh per year, PV in kWp, battery in kWh — CESDM wants
  MWh/year, MW and MWh, so the adapter converts;
- a value of 0 means "has none": no PV system, no battery is created;
- "ev" is a yes/no flag, stored on the household (has_ev).
"""

from __future__ import annotations

import json
from pathlib import Path

SOURCE = "meter-team-b"


def to_cesdm(path: Path, model) -> None:
    """Read the meter file and write each household's energy assets."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))

    for h in data["households"]:
        hh = "hh." + h["meter"]
        key = h["meter"]

        model.add_entity("DemandUnit", f"demand.{key}")
        model.add_attribute(f"demand.{key}", "annual_energy_demand", h["consumption"] / 1000,
                            unit="MWh/year", provenance_ref=SOURCE)
        model.add_relation(f"demand.{key}", "ownedBy", hh)

        if h["pv"] > 0:
            model.add_entity("SolarGenerationUnit", f"pv.{key}")
            model.add_attribute(f"pv.{key}", "nominal_power_capacity", h["pv"] / 1000,
                                unit="MW", provenance_ref=SOURCE)
            model.add_relation(f"pv.{key}", "ownedBy", hh)

        if h["battery"] > 0:
            model.add_entity("StorageUnit", f"battery.{key}")
            model.add_attribute(f"battery.{key}", "energy_storage_capacity", h["battery"] / 1000,
                                unit="MWh", provenance_ref=SOURCE)
            model.add_relation(f"battery.{key}", "ownedBy", hh)

        model.add_attribute(hh, "has_ev", h["ev"], provenance_ref=SOURCE)
