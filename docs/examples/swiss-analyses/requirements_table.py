#!/usr/bin/env python3
"""What each analysis asks for, read straight from the analysis profiles.

    python docs/examples/swiss-analyses/requirements_table.py [Class ...]

Prints a Markdown table: one row per class and attribute, one column per
profile. Because it reads the profiles themselves, it cannot drift from them.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "four-research-groups"))
from cesdm_common import REPO  # noqa: E402

PROFILES = ("optimal_dispatch", "power_flow", "dynamics")


def requirements(profile: str) -> dict:
    data = yaml.safe_load((REPO / "analysis_profiles" / f"{profile}.yaml").read_text(encoding="utf-8"))
    table = {}
    for block in data.get("requirements", []):
        for check in block.get("checks", []):
            if not check.get("required"):
                continue
            key = (block["entity_class"], check["attribute"])
            table[key] = f"if `{check['when']}`" if "when" in check else "required"
    return table


def main(classes: list[str]) -> None:
    tables = {p: requirements(p) for p in PROFILES}
    rows = sorted({key for t in tables.values() for key in t})
    if classes:
        rows = [r for r in rows if r[0] in classes]
    print("| Class | Attribute or link | " + " | ".join(PROFILES) + " |")
    print("|---|---|" + "---|" * len(PROFILES))
    for cls, attribute in rows:
        cells = [tables[p].get((cls, attribute), "") for p in PROFILES]
        print(f"| `{cls}` | `{attribute}` | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main(sys.argv[1:])
