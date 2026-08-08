"""
HVDCLink's own distinguishing features: converter technology is
represented by a single `converter_technology` attribute (an enum of
`LCC`/`VSC`), not by subclasses -- so, unlike most other asset
classes, there's genuinely class-specific behavior here worth pinning
down beyond "can this class be created at all" (already covered
generically by countless other tests). Found while reviewing the test
suite for continued relevance: the original version of this file only
checked basic entity creation, duplicating what dozens of other tests
already do, without touching any of the schema features that actually
make HVDCLink distinct. See CHANGELOG.md.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cesdm_toolbox import build_model_from_yaml


def test_hvdc_link_can_be_created_and_typed():
    model = build_model_from_yaml(ROOT / "schemas/cesdm")
    model.add_entity("HVDCLink", "hvdc.test")
    model.add_attribute("hvdc.test", "converter_technology", "VSC")
    entity = model.entities["HVDCLink"]["hvdc.test"]
    assert entity.data["converter_technology"]["value"] == "VSC"


def test_converter_technology_rejects_a_value_outside_the_enum():
    """converter_technology is deliberately an enum (LCC/VSC), not a
    free-text string -- the whole point of representing converter
    technology this way instead of via subclasses is that validate()
    can catch a typo/invalid value directly."""
    model = build_model_from_yaml(ROOT / "schemas/cesdm")
    model.add_entity("HVDCLink", "hvdc.bad")
    model.add_attribute("hvdc.bad", "converter_technology", "MMC")  # not LCC or VSC
    errors = model.validate()
    assert any("converter_technology" in e for e in errors)


def test_hvdc_link_required_fields_are_enforced():
    """hvdc_technology_type/p_max_hvdc (power_flow group) and max_flow
    (dispatch group) are all required: true -- but only once something
    else from their own group is already present, the same conditional
    requiredness every belongsToGroup-tagged field gets."""
    model = build_model_from_yaml(ROOT / "schemas/cesdm")
    model.add_entity("HVDCLink", "hvdc.bare")
    assert model.validate() == []  # bare link, no group engaged -> clean

    model.add_entity("HVDCLink", "hvdc.partial")
    gen = model.get_entity("hvdc.partial")
    gen.power_flow.dc_voltage_kv = 500.0  # engages the power_flow group
    errors = model.validate()
    assert any("hvdc.partial" in e and "hvdc_technology_type" in e for e in errors)
    assert any("hvdc.partial" in e and "p_max_hvdc" in e for e in errors)


def test_hvdc_link_power_flow_and_dispatch_groups_are_flattened():
    """Both belongsToGroup families HVDCLink declares work like every
    other asset class's flattened groups: .power_flow/.dispatch alias
    directly onto the asset's own data, no separate view entity."""
    model = build_model_from_yaml(ROOT / "schemas/cesdm")
    model.add_entity("HVDCLink", "hvdc.flat")
    hvdc = model.get_entity("hvdc.flat")

    hvdc.power_flow.hvdc_technology_type = "LCC"
    hvdc.power_flow.p_max_hvdc = 1000.0
    hvdc.dispatch.max_flow = 1000.0
    hvdc.dispatch.variable_operating_cost = 2.5

    assert hvdc.hvdc_technology_type == "LCC"  # flat access, same storage
    assert hvdc.max_flow == 1000.0
    assert model.validate() == []
