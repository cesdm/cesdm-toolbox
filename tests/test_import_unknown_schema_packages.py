"""A receiver who loaded only the base schema must hear about the rest."""

from __future__ import annotations

import warnings
from pathlib import Path

import pytest

from cesdm.helpers import build_model_from_yaml

ROOT = Path(__file__).resolve().parents[1]


def test_export_records_every_loaded_package(tmp_path: Path) -> None:
    model = build_model_from_yaml(str(ROOT / "schemas" / "cesdm_power_flow"))
    names = [item["name"] for item in model.schema_packages]
    assert names == ["cesdm", "cesdm_power_flow"]

    path = tmp_path / "empty.yaml"
    model.export_yaml(path)
    text = path.read_text(encoding="utf-8")
    assert "name: cesdm" in text
    assert 'version: 1.0.0' in text or "version: '1.0.0'" in text
    assert "name: cesdm_power_flow" in text


def test_base_import_warns_and_strict_raises(tmp_path: Path) -> None:
    path = tmp_path / "line.yaml"
    path.write_text(
        """
_cesdm_meta:
  format: cesdm-yaml
  schema_packages:
    - {name: cesdm, version: '1.0.0'}
    - {name: cesdm_power_flow, version: '1.0.0'}
TransmissionLine:
  line.1:
    attributes:
      - {id: series_resistance_per_km, value: 0.03}
""",
        encoding="utf-8",
    )
    base = build_model_from_yaml(str(ROOT / "schemas" / "cesdm"))

    with pytest.warns(UserWarning, match="cesdm_power_flow"):
        summary = base.import_yaml(path)
    assert any("series_resistance_per_km" in item[2] for item in summary["unknowns"])
    assert "cesdm_power_flow" in (summary["schema_version_warning"] or "")
    stored = base.entities["TransmissionLine"]["line.1"].data
    assert "series_resistance_per_km" not in stored

    again = build_model_from_yaml(str(ROOT / "schemas" / "cesdm"))
    with pytest.raises(ValueError, match="series_resistance_per_km"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            again.import_yaml(path, strict_unknown=True)


def test_power_flow_profile_names_the_missing_package() -> None:
    base = build_model_from_yaml(str(ROOT / "schemas" / "cesdm"))
    errors = base.validate_for_analysis(str(ROOT / "analysis_profiles" / "power_flow.yaml"))
    assert errors == [
        "[power_flow] load schemas/cesdm_power_flow before this check. "
        "The open schema does not include that package, so its "
        "classes and attributes are missing."
    ]
