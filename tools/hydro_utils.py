"""Checkout shim. Importers should use ``cesdm.hydro_utils``."""

from cesdm.hydro_utils import (
    has_natural_inflow,
    has_reservoir,
    hydro_machine_kind,
    hydro_storage_kind,
    is_pondage,
    is_pumped_storage,
    is_reservoir,
    is_run_of_river,
    normalize_hydro_technology,
)

__all__ = [
    "has_natural_inflow",
    "has_reservoir",
    "hydro_machine_kind",
    "hydro_storage_kind",
    "is_pondage",
    "is_pumped_storage",
    "is_reservoir",
    "is_run_of_river",
    "normalize_hydro_technology",
]
