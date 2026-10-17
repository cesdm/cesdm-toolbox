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
