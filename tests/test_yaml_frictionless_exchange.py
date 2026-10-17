"""Flat YAML keeps Unicode, a grouped file is not read as attributes,
and a Frictionless package keeps units, provenance and every relation target.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ear import build_model_from_yaml as build_ear_model
from cesdm_toolbox import build_model_from_yaml

ROOT = Path(__file__).resolve().parent.parent


def _model():
    return build_model_from_yaml(str(ROOT / "schemas/cesdm"))


def test_flat_yaml_keeps_umlauts(tmp_path):
    model = _model()
    model.add_entity("GeographicalRegion", "region.zh")
    model.add_attribute("region.zh", "name", "Zürich")
    path = tmp_path / "region.yaml"
    model.export_yaml(str(path))
    text = path.read_text(encoding="utf-8")
    assert "Zürich" in text
    assert "\\xFC" not in text


def test_import_yaml_refuses_a_grouped_file(tmp_path):
    path = tmp_path / "grouped.yaml"
    path.write_text(
        "_cesdm_meta:\n"
        "  format: cesdm-hierarchical-yaml\n"
        "GeographicalRegion:\n"
        "  region.zh:\n"
        "    attributes:\n"
        "      core:\n"
        "        name:\n"
        "          value: Zürich\n",
        encoding="utf-8",
    )
    fresh = _model()
    with pytest.raises(ValueError, match="cesdm-hierarchical-yaml"):
        fresh.import_yaml(str(path))
    assert "GeographicalRegion" not in fresh.entities or not fresh.entities["GeographicalRegion"]


def test_frictionless_keeps_unit_provenance_and_every_target(tmp_path):
    model = _model()
    model.add_entity("HydraulicStorageUnit", "res.a")
    model.add_attribute("res.a", "name", "res.a")
    model.add_entity("HydraulicStorageUnit", "res.b")
    model.add_attribute("res.b", "name", "res.b")
    model.add_entity("HydraulicStorageUnit", "storage.lake")
    model.add_attribute(
        "storage.lake", "energy_storage_capacity", 8.8e6,
        unit="m3", provenance_ref="sfoe-reservoirs",
    )
    model.add_attribute("storage.lake", "name", "Zürichsee")
    model.add_entity("HydroGenerationUnit", "gen.1")
    model.add_relation("gen.1", "drawsFromHydraulicStorage", "res.a")
    model.add_relation("gen.1", "drawsFromHydraulicStorage", "res.b")

    out = tmp_path / "pkg"
    model.export_frictionless(out, name="roundtrip")
    rel_text = (out / "resources" / "relations.csv").read_text(encoding="utf-8")
    assert "res.a" in rel_text and "res.b" in rel_text
    storage_csv = (out / "resources" / "HydraulicStorageUnit.csv").read_text(encoding="utf-8")
    assert "m3" in storage_csv
    assert "sfoe-reservoirs" in storage_csv
    assert "Zürichsee" in storage_csv

    fresh = _model()
    fresh.import_frictionless(out)
    stored = fresh.entities["HydraulicStorageUnit"]["storage.lake"].data["energy_storage_capacity"]
    assert stored["unit"] == "m3"
    assert stored["provenance_ref"] == "sfoe-reservoirs"
    assert stored["value"] == pytest.approx(8.8e6)
    targets = fresh.entities["HydroGenerationUnit"]["gen.1"].data["drawsFromHydraulicStorage"]
    assert set(targets) == {"res.a", "res.b"}


def test_ear_frictionless_keeps_author_provenance(tmp_path):
    model = build_ear_model(str(ROOT / "docs/examples/bookshelf/schema"))
    model.add_entity("Author", "author.calvino")
    model.add_attribute(
        "author.calvino", "name", "Italo Calvino", provenance_ref="colophon",
    )
    out = tmp_path / "pkg"
    model.export_frictionless(out, name="bookshelf")
    text = (out / "resources" / "Author.csv").read_text(encoding="utf-8")
    assert "colophon" in text

    fresh = build_ear_model(str(ROOT / "docs/examples/bookshelf/schema"))
    fresh.import_frictionless(out)
    stored = fresh.entities["Author"]["author.calvino"].data["name"]
    assert stored["value"] == "Italo Calvino"
    assert stored["provenance_ref"] == "colophon"
