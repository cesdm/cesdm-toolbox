"""Schema reference and diagram generators follow extends and augmentations."""

from pathlib import Path

from tools.generate_cesdm_schema_html import load_schema
from tools.generate_schema_diagrams import Schema

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "schemas" / "cesdm"
POWER_FLOW = ROOT / "schemas" / "cesdm_power_flow"
DYNAMIC = ROOT / "schemas" / "cesdm_dynamic"


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
