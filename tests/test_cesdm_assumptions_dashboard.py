"""Tests for tools/cesdm_assumptions_dashboard.py."""

from pathlib import Path

from tools.cesdm_assumptions_dashboard import (
    TEMPLATE_PATH,
    _country_label,
    _pretty_tech_id,
    empty_payload,
    render_html,
)


def test_country_label_maps_unknown():
    assert _country_label("CH") == "CH"
    assert _country_label("??") == "Unspecified"
    assert _country_label("") == "Unspecified"


def test_pretty_tech_id():
    assert _pretty_tech_id("Generation.Nuclear.LWR") == "Nuclear LWR"
    assert _pretty_tech_id("Generation.Other.DemandResponse") == "Other DemandResponse"


def test_template_contains_placeholder():
    text = TEMPLATE_PATH.read_text(encoding="utf-8")
    assert TEMPLATE_PATH.exists()
    assert "__CESDM_DATA__" in text
    assert "__CESDM_SERVE__" in text
    assert 'id="load-yaml"' in text


def test_render_html_embeds_payload():
    html = render_html(
        {
            "meta": {
                "title": "Demo",
                "yaml": "demo.yaml",
                "yaml_name": "demo.yaml",
                "n_entities": 3,
                "n_classes": 2,
                "n_countries": 1,
            },
            "countries": ["CH"],
            "counts": {"DemandUnit": 1},
            "capacity": {"CH": {"solar": 10.0}},
            "demand": {"CH": 100.0},
            "demand_types": {"CH": {"electricity": 100.0}},
            "storage_energy": {},
            "storage_power": {},
            "inflow": {},
            "hydro": {},
            "reservoir": {},
            "ntc": [],
            "network": {
                "lines": 0,
                "line_km": 0.0,
                "line_mva": 0.0,
                "transformers": 0,
                "transformer_mva": 0.0,
                "interconnectors": 0,
            },
        }
    )
    assert "__CESDM_DATA__" not in html
    assert "__CESDM_SERVE__" not in html
    assert '"title": "Demo"' in html
    assert "Installed capacity mix" in html
    assert "Load YAML" in html
    assert "const SERVE = false;" in html


def test_render_html_serve_flag():
    html = render_html(empty_payload(), serve=True)
    assert "const SERVE = true;" in html
    assert empty_payload()["meta"]["title"] in html
