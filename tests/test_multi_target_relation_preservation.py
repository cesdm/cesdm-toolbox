# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

"""
ear/model/persistence_yaml_json.py's import_yaml() calls add_relation()
once per target. When the schema cardinality allows more than one
target (``0..*``), a second call keeps the first and appends. A single
target stays a plain string. A cardinality of ``1`` still replaces,
and says so.

Found via tools/aggregate_cesdm_model.py's per-country technology
aggregation, which is the first place in the whole codebase to ever
need one entity to genuinely hold more than one target through the
same relation id (HydroGenerationUnit.drawsFromHydroReservoir, after
merging different reservoir-side technology groups onto one
generator) -- but the bug lives in the generic EAR persistence layer
itself, not the aggregation tool, so it's tested here independently of
it.
"""

from __future__ import annotations

import warnings
from pathlib import Path

from cesdm_toolbox import build_model_from_yaml

ROOT = Path(__file__).resolve().parent.parent


def _build_model_with_multi_target_relation():
    model = build_model_from_yaml(str(ROOT / "cesdm/schemas/base"))
    model.add_entity("HydroReservoir", "res.a")
    model.add_attribute("res.a", "name", "res.a")
    model.add_entity("HydroReservoir", "res.b")
    model.add_attribute("res.b", "name", "res.b")
    model.add_entity("HydroGenerationUnit", "gen.1")
    model.add_attribute("gen.1", "name", "gen.1")
    model.add_relation("gen.1", "drawsFromHydroReservoir", "res.a")
    model.add_relation("gen.1", "drawsFromHydroReservoir", "res.b")
    return model


def test_add_relation_keeps_every_target_when_cardinality_allows_many():
    """drawsFromHydroReservoir is cardinality 0..*, so the second call
    appends instead of replacing the first target."""
    model = _build_model_with_multi_target_relation()
    stored = model.entities["HydroGenerationUnit"]["gen.1"].data.get("drawsFromHydroReservoir")
    assert stored == ["res.a", "res.b"]


def test_import_yaml_flat_preserves_every_target(tmp_path):
    model = _build_model_with_multi_target_relation()

    yaml_path = tmp_path / "model.yaml"
    model.export_yaml(str(yaml_path))

    reloaded = build_model_from_yaml(str(ROOT / "cesdm/schemas/base"))
    reloaded.import_yaml(str(yaml_path))

    stored = reloaded.entities["HydroGenerationUnit"]["gen.1"].data.get("drawsFromHydroReservoir")
    assert isinstance(stored, list), f"expected a real list, got {stored!r}"
    assert set(stored) == {"res.a", "res.b"}


def test_single_target_relation_still_stores_a_plain_scalar(tmp_path):
    """The common case (one target) must stay exactly as before -- a
    plain string, not a single-element list -- so this fix doesn't
    change behaviour for the overwhelming majority of relations that
    are genuinely single-valued."""
    model = build_model_from_yaml(str(ROOT / "cesdm/schemas/base"))
    model.add_entity("HydroReservoir", "res.a")
    model.add_attribute("res.a", "name", "res.a")
    model.add_entity("HydroGenerationUnit", "gen.1")
    model.add_attribute("gen.1", "name", "gen.1")
    model.add_relation("gen.1", "drawsFromHydroReservoir", "res.a")

    yaml_path = tmp_path / "model.yaml"
    model.export_yaml(str(yaml_path))

    reloaded = build_model_from_yaml(str(ROOT / "cesdm/schemas/base"))
    reloaded.import_yaml(str(yaml_path))

    stored = reloaded.entities["HydroGenerationUnit"]["gen.1"].data.get("drawsFromHydroReservoir")
    assert stored == "res.a"
    assert not isinstance(stored, list)


def test_single_cardinality_relation_warns_when_replaced():
    """releasesToHydroReservoir is cardinality 1. A second target
    replaces the first, and the call says so."""
    model = build_model_from_yaml(str(ROOT / "cesdm/schemas/base"))
    model.add_entity("HydroReservoir", "res.a")
    model.add_entity("HydroReservoir", "res.b")
    model.add_entity("HydroGenerationUnit", "gen.1")
    model.add_relation("gen.1", "releasesToHydroReservoir", "res.a")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model.add_relation("gen.1", "releasesToHydroReservoir", "res.b")
    stored = model.entities["HydroGenerationUnit"]["gen.1"].data.get("releasesToHydroReservoir")
    assert stored == "res.b"
    assert any("replaced by" in str(w.message) for w in caught)
