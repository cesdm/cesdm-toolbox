#!/usr/bin/env python3
"""
Example: reservoir hydro modelled with direct reservoir/generator assets,
built with core EAR calls (`add_entity`/`add_attribute`/`add_relation`)
plus the object-oriented proxy layer for convenient reading/writing
afterward -- see docs/getting_started.md and
docs/architecture/proxy_api.md.

HydroGenerationUnit assets link directly to ReservoirStorageUnit assets:
  - drawsFromReservoir: upper/source reservoir used for generation
  - dischargesToReservoir: lower/downstream reservoir where modelled
  - suppliesResourceTo: inverse link from reservoir to generator

No HydroPowerPlant wrapper is required -- both entities plus this
composite relation pairing are created directly below.
"""
from pathlib import Path
import sys

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]

_REPO_ROOT = _repo_root()
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
HERE = Path(__file__).resolve().parent

from cesdm_toolbox import build_model_from_yaml


def build_example(schema_dir: Path, library_path: Path):
    m = build_model_from_yaml(str(schema_dir))
    m.import_library(str(library_path))

    ELEC  = "carrier.electricity"
    WATER = "resource.water"

    domain = m.ensure_entity(class_name="CarrierDomain", entity_id="domain.electricity")
    m.add_relation_if_allowed(domain, "hasCarrier", ELEC)

    m.ensure_entity(class_name="GeographicalRegion", entity_id="region.ch", name="Switzerland")

    m.add_entity(entity_class="ElectricalBus", entity_id="bus.ch")
    m.add_attribute("bus.ch", "nominal_voltage", 380.0)
    m.add_relation("bus.ch", "locatedIn", "region.ch")
    m.add_relation("bus.ch", "belongsToCarrierDomain", "domain.electricity")
    m.add_attribute("bus.ch", "name", "Swiss 380kV bus")
    bus = m.get_entity(entity_id="bus.ch")

    # ── Direct reservoir ↔ generator linkage (no HydroPowerPlant wrapper) ──
    # ReservoirStorageUnit + the paired HydroGenerationUnit + the
    # drawsFromReservoir/suppliesResourceTo relation pairing, created
    # directly.
    m.add_entity(entity_class="ReservoirStorageUnit", entity_id="reservoir.alpine")
    m.add_entity(entity_class="HydroGenerationUnit", entity_id="gen.hydro.alpine")
    m.add_relation("gen.hydro.alpine", "drawsFromReservoir", "reservoir.alpine")
    m.add_relation("reservoir.alpine", "suppliesResourceTo", "gen.hydro.alpine")
    reservoir = m.get_entity(entity_id="reservoir.alpine")
    gen = m.get_entity(entity_id="gen.hydro.alpine")
    gen.dispatch.nominal_power_capacity = 500.0
    reservoir.dispatch.energy_storage_capacity = 2500.0

    m.set_attribute_if_allowed(reservoir, "name", "Alpine reservoir")
    m.add_relation_if_allowed(reservoir, "storesResource", WATER)
    reservoir.dispatch.annual_natural_inflow_energy = 900_000.0

    m.set_attribute_if_allowed(gen, "name", "Alpine hydro turbine")
    m.set_attribute_if_allowed(gen, "is_reversible", False)
    m.add_relation_if_allowed(gen, "hasInputResource", WATER)
    m.add_relation_if_allowed(gen, "hasOutputCarrier", ELEC)
    gen.connect(bus)

    # dischargesToReservoir: where the turbine outflow goes (cascade
    # stage) -- for this example the outflow reaches the river directly,
    # no downstream reservoir modelled, so this is left unset.
    gen.dispatch.dispatch_type = "dispatchable"
    gen.dispatch.machine_role = "turbine"
    gen.dispatch.turbine_efficiency = 0.90
    gen.dispatch.annual_resource_potential = 900_000.0

    return m


def build_phs_example(schema_dir: Path, library_path: Path):
    """PHS closed-loop: same structure as reservoir-hydro, is_reversible=True."""
    m = build_model_from_yaml(str(schema_dir))
    m.import_library(str(library_path))

    ELEC  = "carrier.electricity"
    WATER = "resource.water"

    domain = m.ensure_entity(class_name="CarrierDomain", entity_id="domain.electricity")
    m.add_relation_if_allowed(domain, "hasCarrier", ELEC)
    m.ensure_entity(class_name="GeographicalRegion", entity_id="region.ch")

    m.add_entity(entity_class="ElectricalBus", entity_id="bus.ch")
    m.add_relation("bus.ch", "locatedIn", "region.ch")
    m.add_relation("bus.ch", "belongsToCarrierDomain", "domain.electricity")
    bus = m.get_entity(entity_id="bus.ch")

    # Upper + lower ReservoirStorageUnit, paired reversible
    # HydroGenerationUnit, and the drawsFromReservoir/suppliesResourceTo/
    # dischargesToReservoir relations, created directly.
    m.add_entity(entity_class="ReservoirStorageUnit", entity_id="reservoir.grimsel.upper")
    m.add_entity(entity_class="ReservoirStorageUnit", entity_id="reservoir.grimsel.lower")
    m.add_entity(entity_class="HydroGenerationUnit", entity_id="gen.phs.grimsel")
    m.add_relation("gen.phs.grimsel", "drawsFromReservoir", "reservoir.grimsel.upper")
    m.add_relation("gen.phs.grimsel", "dischargesToReservoir", "reservoir.grimsel.lower")
    m.add_relation("reservoir.grimsel.upper", "suppliesResourceTo", "gen.phs.grimsel")
    upper = m.get_entity(entity_id="reservoir.grimsel.upper")
    lower = m.get_entity(entity_id="reservoir.grimsel.lower")
    gen = m.get_entity(entity_id="gen.phs.grimsel")
    gen.dispatch.nominal_power_capacity = 420.0
    gen.dispatch.maximum_pumping_power = 420.0
    gen.dispatch.pumping_efficiency = 0.82
    gen.dispatch.turbine_efficiency = 0.87
    gen.dispatch.machine_role = "reversible"

    m.add_relation_if_allowed(lower, "storesResource", WATER)
    m.add_relation_if_allowed(upper, "storesResource", WATER)
    upper.dispatch.energy_storage_capacity = 1200.0

    m.set_attribute_if_allowed(gen, "name", "Grimsel reversible pump-turbine")
    m.set_attribute_if_allowed(gen, "is_reversible", True)
    m.set_attribute_if_allowed(gen, "turbine_type", "reversible_francis")
    m.add_relation_if_allowed(gen, "hasInputResource", WATER)
    m.add_relation_if_allowed(gen, "hasOutputCarrier", ELEC)
    gen.connect(bus)
    gen.dispatch.dispatch_type = "dispatchable"

    return m


if __name__ == "__main__":
    schema_dir   = HERE.parent / "schemas/cesdm"
    library_path = HERE.parent / "library" / "default_library"

    print("=== Reservoir-Hydro example ===")
    model = build_example(schema_dir, library_path)
    print(model.summary())
    errors = model.validate()
    print(f"Validation errors: {len(errors)}")
    for error in errors[:20]:
        print(" -", error)
    print("Hydro reservoir composite example built.")

    print("\n=== PHS closed-loop example ===")
    phs_model = build_phs_example(schema_dir, library_path)
    print(phs_model.summary())
    phs_errors = phs_model.validate()
    print(f"Validation errors: {len(phs_errors)}")
    for error in phs_errors[:20]:
        print(" -", error)
    print("PHS closed-loop composite example built.")
