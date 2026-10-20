# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

"""An entity with no attributes and no relations is omitted on export."""

from cesdm_toolbox import build_model_from_yaml


def test_truly_empty_entity_still_skipped(tmp_path):
    """An entity with no attributes and no relations is omitted."""
    model = build_model_from_yaml("cesdm/schemas/base")
    model.add_entity("GeographicalRegion", "region.empty")
    out_path = tmp_path / "empty.yaml"
    model.export_yaml(str(out_path))

    text = out_path.read_text(encoding="utf-8")
    assert "region.empty" not in text
