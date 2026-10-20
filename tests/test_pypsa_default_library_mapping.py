# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

# import_pypsa imports numpy at module load for real array handling
# elsewhere in that file; the mapping tests exercised here don't need
# it, but the module-level `import numpy as np` still has to succeed
# to import anything from the module at all. Skip gracefully rather
# than failing test *collection* for the whole suite (a collection
# error in one file used to abort collecting every other test file
# too -- see conftest.py and CHANGELOG.md for the related fix).
pytest.importorskip("numpy")

# import_pypsa imports pypsa at module load; the mapping tests do not need it.
sys.modules.setdefault("pypsa", types.SimpleNamespace(Network=object))

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from cesdm_toolbox import build_model_from_yaml
from import_pypsa import (
    _default_generator_type_id,
    _entity_attribute,
    _relation_target,
    schema_dir_for_pypsa,
)


def test_base_schema_dir_opens_the_power_flow_package() -> None:
    opened = schema_dir_for_pypsa(str(ROOT / "cesdm" / "schemas" / "base"))
    assert Path(opened).name == "powerflow"
    model = build_model_from_yaml(opened)
    assert "series_resistance_per_km" in (model.class_attributes("TransmissionLine") or [])


def test_pypsa_aliases_map_to_default_library() -> None:
    model = build_model_from_yaml(str(ROOT / "cesdm/schemas/base"))
    model.import_library(str(ROOT / "cesdm" / "library" / "default_library"))

    expected = {
        "CCGT": "Generation.Thermal.Gas.CCGT.Existing",
        "OCGT": "Generation.Thermal.Gas.OCGT.New",
        "nuclear": "Generation.Nuclear.LWR",
        "coal": "Generation.Thermal.Coal.HardCoal.New",
        "lignite": "Generation.Thermal.Coal.Lignite.New",
        "onwind": "Generation.Renewable.Wind.Onshore",
        "offwind-ac": "Generation.Renewable.Wind.Offshore",
        "solar": "Generation.Renewable.Solar.PV.Utility",
        "ror": "Generation.Renewable.Hydro.RunOfRiver",
    }

    for label, type_id in expected.items():
        assert _default_generator_type_id(label, label) == type_id
        assert type_id in model.entities["GeneratorType"]

    ccgt = expected["CCGT"]
    assert _entity_attribute(model, ccgt, "variable_operating_cost") == 1.6
    assert _relation_target(model, ccgt, "hasInputCarrier") == "carrier.fuel.fossil.gas.natural_gas"
    carrier = _relation_target(model, ccgt, "hasInputCarrier")
    assert _entity_attribute(model, carrier, "energy_carrier_cost") == 22.68
