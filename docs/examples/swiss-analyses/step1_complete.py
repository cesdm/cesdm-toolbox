#!/usr/bin/env python3
# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

"""Part 2, step 1: correct is not complete.

    python docs/examples/swiss-analyses/step1_complete.py

The Swiss system from Part 1 passes the schema. Whether it is complete
for an analysis is a separate check, asked in the later steps.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "four-research-groups"))

import adapter_a                     # noqa: E402
from cesdm_common import REPO, load, new_model   # noqa: E402

# One file per step, written under output/ and rebuilt by CI. Each later
# file is the previous file plus one analysis. REPO is the checkout that
# contains cesdm/schemas/base, not a parent counted from this file.
MODELS = REPO / "output" / "swiss-analyses"
LAYER_FILES = {
    "system": "system.yaml",
    "dispatch": "dispatch.yaml",
    "power_flow": "power_flow.yaml",
    "dynamics": "dynamics.yaml",
}
PREVIOUS_STEP = {
    "system": "step1_complete.py",
    "dispatch": "step2_dispatch.py",
    "power_flow": "step3_power_flow.py",
    "dynamics": "step4_dynamics.py",
}


def layer_path(name: str) -> Path:
    return MODELS / LAYER_FILES[name]


def shown(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def save_layer(model, name: str) -> Path:
    """Write this step's file. It already contains every earlier layer."""
    MODELS.mkdir(parents=True, exist_ok=True)
    path = layer_path(name)
    model.export_yaml(path)
    print(f"Wrote {shown(path)}")
    return path


def load_layer(name: str, schemas: str | tuple[str, ...] = "base"):
    """Read the previous step's file, so this step only appends.

    ``schemas`` is the package this step writes into. Power flow and
    dynamics name their extension folders; the base stays the default.
    """
    path = layer_path(name)
    if not path.exists():
        script = PREVIOUS_STEP[name]
        raise SystemExit(
            f"Missing {shown(path)}. Run python docs/examples/swiss-analyses/{script} first."
        )
    print(f"Loaded {shown(path)}")
    return load(path, schemas)


def swiss_system():
    """The system of Part 1, as Group A writes it."""
    model = new_model()
    adapter_a.to_cesdm(HERE.parent / "four-research-groups" / "group-a-csv", model)
    return model


def summarise(gaps: list[str]) -> Counter:
    """'[profile] [Class:id] missing required 'attr'' -> count per (class, attr)."""
    counts = Counter()
    for gap in gaps:
        cls = gap.split("] [", 1)[1].split(":", 1)[0]
        attribute = gap.rsplit("'", 2)[1]
        counts[(cls, attribute)] += 1
    return counts


def main() -> None:
    model = swiss_system()

    print("Is it correct CESDM?")
    print(f"    model.validate(): {len(model.validate())} errors")
    save_layer(model, "system")


if __name__ == "__main__":
    main()
