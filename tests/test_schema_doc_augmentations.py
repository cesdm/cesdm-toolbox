# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

"""Schema reference and diagram generators follow extends and augmentations."""

from pathlib import Path

from tools.generate_cesdm_schema_html import load_schema
from tools.generate_schema_diagrams import Schema

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "cesdm" / "schemas" / "base"
POWER_FLOW = ROOT / "cesdm" / "schemas" / "powerflow"
DYNAMIC = ROOT / "cesdm" / "schemas" / "dynamics"


def _ids(entity: dict, kind: str) -> list[str]:
    return [
        item if isinstance(item, str) else item["id"]
        for item in entity.get(kind) or []
    ]


def test_base_reference_does_not_attach_power_flow_fields():
    entities, attrs, _rels = load_schema([BASE])
    assert "powerflow_bus_type" not in _ids(entities["ElectricalBus"], "attributes")
    assert "powerflow_bus_type" not in attrs
    assert "ShuntUnit" not in entities


def test_power_flow_reference_attaches_bus_type_to_electrical_bus():
    entities, attrs, _rels = load_schema([POWER_FLOW])
    assert "powerflow_bus_type" in _ids(entities["ElectricalBus"], "attributes")
    assert "powerflow_bus_type" in attrs
    assert "ShuntUnit" in entities
    assert "Controller" not in entities
    assert "ElectricalBus" in entities


def test_both_extensions_attach_power_flow_and_dynamics():
    entities, _attrs, rels = load_schema([POWER_FLOW, DYNAMIC])
    assert "powerflow_bus_type" in _ids(entities["ElectricalBus"], "attributes")
    assert "hasAutomaticVoltageRegulator" in _ids(entities["GenerationUnit"], "relations")
    assert "usesDynamicModelType" in rels
    assert "Controller.AVR.SEXS" in entities
    assert "ShuntUnit" in entities
    assert entities["ElectricalBus"]["_schema"] == "base"
    assert entities["ShuntUnit"]["_schema"] == "powerflow"
    assert entities["Controller"]["_schema"] == "dynamics"
    bus = {item["id"]: item for item in entities["ElectricalBus"]["attributes"]}
    assert bus["powerflow_bus_type"]["_schema"] == "powerflow"
    assert _attrs["powerflow_bus_type"]["_schema"] == "powerflow"
    assert rels["usesDynamicModelType"]["_schema"] == "dynamics"


def test_schema_reference_page_can_show_each_package():
    from tools.generate_cesdm_schema_html import build_page

    page = build_page([BASE, POWER_FLOW, DYNAMIC])
    assert 'class="pkg-filter" value="cesdm"' not in page
    assert 'class="grp-filter" value="technical" data-base-pkg="base" checked' in page
    assert 'class="grp-filter" value="dispatch" data-base-pkg="base" checked' in page
    assert 'class="pkg-filter" value="powerflow"' in page
    assert 'value="powerflow" checked' not in page
    assert 'class="pkg-filter" value="dynamics"' in page
    assert 'value="dynamics" checked' not in page
    assert 'data-pkg="powerflow"' in page
    assert 'data-pkg="dynamics"' in page
    assert 'id="ElectricalBus" data-pkg="base"' in page
    assert 'id="ShuntUnit" data-pkg="powerflow"' in page
    assert "cardHasShownField" in page
    assert 'class="grp-filter" value="technical"' in page
    assert 'class="grp-filter" value="dispatch"' in page
    assert 'data-groups="dispatch"' in page
    assert 'data-groups="technical"' in page
    assert 'data-groups="technical dispatch"' in page

    base_only = build_page([BASE])
    assert 'class="pkg-filter"' not in base_only
    assert 'id="ShuntUnit"' not in base_only


def test_diagrams_include_the_same_augmentation():
    base = Schema(BASE)
    power_flow = Schema(POWER_FLOW)
    both = Schema([POWER_FLOW, DYNAMIC])
    assert "powerflow_bus_type" not in base.classes["ElectricalBus"].attributes
    assert "powerflow_bus_type" in power_flow.classes["ElectricalBus"].attributes
    bus = power_flow.classes["ElectricalBus"].attributes["powerflow_bus_type"]
    assert "power_flow" in (bus.belongsToGroup or [])
    assert "hasAutomaticVoltageRegulator" in both.classes["GenerationUnit"].relations
    assert "Controller.AVR.SEXS" in both.classes
