#!/usr/bin/env python3
"""One adapter mistake at a time, starting from Group A's correct model.

    python docs/examples/four-research-groups/mistakes.py

Some mistakes stop at the write. Others are stored and reported by
model.validate(). One is a valid number in the wrong unit: validate()
accepts it, and compare shows the difference.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import adapter_a                     # noqa: E402
from compare import compare          # noqa: E402


def correct_model():
    """Group A's CSV, already translated. validate() is empty."""
    model = adapter_a.leeres_modell()
    adapter_a.to_cesdm(HERE / "group-a-csv", model)
    return model


def _short(error: BaseException) -> str:
    text = str(error).strip('"')
    known = text.find(". Known")
    if known != -1:
        text = text[:known]
    return f"{type(error).__name__}: {text}"


print("0. Group A's model, before any mistake")
model = correct_model()
print(f"   model.validate() → {model.validate()}")

print("\n1. Demand left in GWh, with unit GWh/year")
model = correct_model()
try:
    model.add_attribute("demand.CH", "annual_energy_demand", 58000, unit="GWh/year")
except ValueError as error:
    print("   stopped on write:", _short(error))

print("\n2. The column name Pmax, instead of nominal_power_capacity")
model = correct_model()
try:
    model.add_attribute("gen.CH_NUC", "Pmax", 3000, unit="MW")
except KeyError as error:
    print("   stopped on write:", _short(error))

print("\n3. A plain GenerationUnit drawing from a reservoir")
model = correct_model()
try:
    model.add_entity("GenerationUnit", "gen.dam")
    model.add_relation("gen.dam", "drawsFromHydraulicStorage", "storage.CH_ROR")
except KeyError as error:
    print("   stopped on write:", _short(error))

print("\n4. Capacity written as the text '3 GW'")
model = correct_model()
try:
    model.add_attribute("gen.CH_NUC", "nominal_power_capacity", "3 GW", unit="MW")
except ValueError as error:
    print("   stopped on write:", _short(error))

print("\n5. Region code CHE, which is not a region in the library")
model = correct_model()
model.add_relation("gen.CH_NUC", "belongsToGeographicalRegion", "region.country.CHE")
print("   the write is accepted; model.validate() reports:")
for error in model.validate():
    print("  ", error)

print("\n6. Efficiency 1.5, above the maximum of 1")
print("   the value is stored; model.validate() still reports it:")
model = correct_model()
model.add_attribute("gen.CH_NUC", "energy_conversion_efficiency", 1.5, unit="fraction")
for error in model.validate():
    print("  ", error)

print("\n7. A hydro plant drawing from a demand, not from a basin")
model = correct_model()
model.add_relation("gen.CH_HYD_ROR", "drawsFromHydraulicStorage", "demand.CH")
print("   the write is accepted; model.validate() reports:")
for error in model.validate():
    print("  ", error)

print("\n8. Reservoir energy stored as a negative number")
print("   the value is stored; model.validate() still reports it:")
model = correct_model()
model.add_attribute("storage.CH_RES", "energy_storage_capacity", -8_800_000, unit="MWh")
for error in model.validate():
    print("  ", error)

print("\n9. Nuclear capacity 3.0 with no unit — meant as GW, stored as MW")
correct = correct_model()
mistaken = correct_model()
mistaken.add_attribute("gen.CH_NUC", "nominal_power_capacity", 3.0)
print(f"   model.validate() → {mistaken.validate()}")
for diff in compare(correct, mistaken, "Group A", "with mistake"):
    print("  ", diff)
