# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

"""Shared paths for scripts that are not a group's adapter.

The four adapters open a model themselves. The Swiss analysis scripts and
`compare.py` still use `new_model` and `load` from here.
"""

from __future__ import annotations

import sys
from pathlib import Path


def repository_root() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in [here, *here.parents, Path.cwd()]:
        if (candidate / "cesdm" / "schemas" / "base").exists():
            return candidate
    raise FileNotFoundError("Run this from inside the cesdm-toolbox repository.")


REPO = repository_root()
# The example and the schema it loads live in this repository. Prefer that
# code over another CESDM checkout that happens to be installed.
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cesdm_toolbox import build_model_from_yaml  # noqa: E402


def new_model(schemas: str | tuple[str, ...] = "base"):
    """Schema plus the shared libraries: technologies, carriers, regions.

    ``schemas`` names folders under ``cesdm/schemas/``. ``powerflow`` already
    extends the base. A study that also needs dynamics passes both folders.
    """
    names = (schemas,) if isinstance(schemas, str) else tuple(schemas)
    paths = [str(REPO / "cesdm" / "schemas" / name) for name in names]
    model = build_model_from_yaml(paths[0] if len(paths) == 1 else paths)
    model.import_library(str(REPO / "cesdm/library/default_library"))
    model.import_library(str(REPO / "cesdm/library/regions_library"))
    return model


def load(path, schemas: str | tuple[str, ...] = "base"):
    """Receive a CESDM file from another group."""
    model = new_model(schemas)
    model.import_yaml(str(path))
    return model


def number(x: float):
    """3000.0 -> 3000, 0.4 stays 0.4, 8.799999999 -> 8.8."""
    x = round(float(x), 9)
    return int(x) if x.is_integer() else x
