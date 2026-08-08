#!/usr/bin/env python3
"""
minimal_electricity_model.py

Smallest useful CESDM study model for documentation and first-time modellers:
one electricity carrier domain, one bus, one wind generator, one demand unit.

Uses Core EAR API for the system container and carrier domain, then Proxy API
for network assets. Run from the cesdm-toolbox repository root:

    python docs/examples/minimal_electricity_model.py
"""

from __future__ import annotations

from pathlib import Path
import sys


def repository_root() -> Path:
    here = Path(__file__).resolve()
    candidates = list(here.parents) + [Path.cwd(), *Path.cwd().parents]
    for candidate in candidates:
        if (candidate / "schemas" / "cesdm").exists():
            return candidate
    raise FileNotFoundError(
        "Could not locate cesdm-toolbox. Run this script from the repository root "
        "or from docs/examples/."
    )


_REPO_ROOT = repository_root()
sys.path.insert(0, str(_REPO_ROOT))

from cesdm_toolbox import build_model_from_yaml
from cesdm.default_library import Carriers, GeneratorTypes


def main() -> None:
    repo = _REPO_ROOT
    output_dir = repo / "output" / "minimal_electricity_model"

    model = build_model_from_yaml(str(repo / "schemas" / "cesdm"))
    model.import_library(str(repo / "library" / "default_library"))

    # --- Core EAR API: system boundary and electricity domain ---
    model.add_entity(entity_class="EnergySystemModel", entity_id="DEMO_2030")
    model.add_attribute(
        entity_id="DEMO_2030",
        attribute_id="long_name",
        value="Minimal electricity demo",
        unit=None,
        provenance_ref=None,
    )

    model.add_entity(entity_class="CarrierDomain", entity_id="domain.electricity")
    model.add_attribute(
        entity_id="domain.electricity",
        attribute_id="name",
        value="Electricity",
        unit=None,
        provenance_ref=None,
    )
    model.add_relation(
        entity_id="domain.electricity",
        relation_id="hasCarrier",
        target_entity_id=Carriers.CARRIER_ELECTRICITY,
    )

    electricity = model.get_entity("domain.electricity")

    # --- Proxy API: network and assets ---
    bus = model.add_entity("ElectricalBus", "bus.demo")
    bus.name = "Demo bus 380 kV"
    bus.nominal_voltage = (380, "kV")
    bus.belongsToCarrierDomain = electricity

    gen = model.add_entity("GenerationUnit", "gen.demo.wind")
    gen.name = "Demo wind farm"
    gen.nominal_power_capacity = (500, "MW")
    gen.hasTechnology = GeneratorTypes.GENERATION_RENEWABLE_WIND_ONSHORE
    gen.atNode = bus

    demand = model.add_entity("DemandUnit", "dem.demo")
    demand.name = "Demo electricity demand"
    demand.annual_energy_demand = (2_000_000, "MWh/year")  # 2 TWh/year
    demand.atNode = bus

    errors = model.validate()
    if errors:
        print(f"{len(errors)} validation issue(s):")
        for error in errors[:20]:
            print(" -", error)
        raise SystemExit(1)

    output_dir.mkdir(parents=True, exist_ok=True)
    model.export_yaml_hierarchical(output_dir / "demo_2030.yaml")
    model.export_frictionless(
        output_dir / "frictionless",
        name="minimal-electricity-demo",
        title="Minimal electricity demo model",
    )

    print(f"Validated {len(model.entities)} entities and exported to {output_dir}")


if __name__ == "__main__":
    main()
