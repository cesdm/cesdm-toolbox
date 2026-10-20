# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

"""Checkout shim. Importers should use ``cesdm.generation_classifier``."""

from cesdm.generation_classifier import (
    classify_generation_unit,
    classify_generator,
    generation_asset_class,
    hydrogen_generation_efficiency,
)
from cesdm.hydro_utils import hydro_machine_kind

__all__ = [
    "generation_asset_class",
    "hydrogen_generation_efficiency",
    "hydro_machine_kind",
    "classify_generation_unit",
    "classify_generator",
]
