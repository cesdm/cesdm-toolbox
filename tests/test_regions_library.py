# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

"""Regions library: NUTS GeographicalRegions."""

from __future__ import annotations

from pathlib import Path

from cesdm.helpers import build_model_from_yaml

ROOT = Path(__file__).resolve().parents[1]


def _model_with_regions():
    model = build_model_from_yaml(str(ROOT / "cesdm" / "schemas" / "base"))
    model.import_library(str(ROOT / "cesdm" / "library" / "default_library"))
    model.import_library(str(ROOT / "cesdm" / "library" / "regions_library"))
    return model


def test_regions_library_loads_countries_and_nuts():
    model = _model_with_regions()

    ch = model.get_entity("region.country.CH")
    assert ch.long_name == "Switzerland"
    assert ch.region_level == "country"
    assert ch.iso_country_code == "CH"

    nuts1 = model.get_entity("region.nuts1.CH0")
    assert nuts1.isSubRegionOf.id == "region.country.CH"

    n_regions = len(model.entities.get("GeographicalRegion") or {})
    assert n_regions >= 2000  # full NUTS 0–3 catalogue
    assert "MarketZone" not in model.classes


def test_bus_can_belong_to_geographical_region():
    model = _model_with_regions()
    bus = model.add_entity("ElectricalBus", "bus.test")
    bus.belongsToCarrierDomain = "domain.electricity"
    bus.belongsToGeographicalRegion = "region.country.CH"
    assert bus.belongsToGeographicalRegion.id == "region.country.CH"
    assert model.validate() == []
