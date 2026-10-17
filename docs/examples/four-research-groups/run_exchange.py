#!/usr/bin/env python3
"""Four research groups, one energy system, four representations.

    python docs/examples/four-research-groups/run_exchange.py

Every hand-over goes through a CESDM YAML file, as between real groups.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import adapter_a, adapter_b, adapter_c, adapter_d   # noqa: E401,E402
from cesdm_common import REPO                        # noqa: E402
from compare import compare                          # noqa: E402

OUT = REPO / "output" / "four-research-groups"

GROUPS = {   # name: (adapter, native data, file name it writes when receiving, open, read yaml)
    "A": (adapter_a, HERE / "group-a-csv", "csv",
          adapter_a.leeres_modell, adapter_a.yaml_einlesen),
    "B": (adapter_b, HERE / "group-b-excel" / "switzerland_dispatch.xlsx", "switzerland_dispatch.xlsx",
          adapter_b.network, adapter_b.network_from_yaml),
    "C": (adapter_c, HERE / "group-c-yaml" / "system.yaml", "system.yaml",
          adapter_c.start_case, adapter_c.case_from_file),
    "D": (adapter_d, HERE / "group-d-json" / "network.json", "network.json",
          adapter_d.empty_document, adapter_d.document_from_yaml),
}


def to_cesdm(group: str, source: Path):
    adapter, _, _, open_model, _ = GROUPS[group]
    model = open_model()
    adapter.to_cesdm(source, model)
    return model


def read_yaml(group: str, path: Path):
    return GROUPS[group][4](path)


def receive(group: str, model) -> Path:
    """Write a CESDM model in a group's own representation."""
    adapter, _, name, _, _ = GROUPS[group]
    target = OUT / f"received-by-{group.lower()}" / name
    adapter.from_cesdm(model, target)
    return target


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    print("1 · Each group writes its system as CESDM")
    for g, (_, native, _, _, _) in GROUPS.items():
        model = to_cesdm(g, native)
        assert not model.validate(), model.validate()
        model.export_yaml(OUT / f"group_{g.lower()}.yaml")
        print(f"    Group {g}  {native.name:28s} → group_{g.lower()}.yaml   ✓ valid CESDM")

    # Last year's Group D, for the comparison in the tutorial: solar 6000 MW
    # and reservoir inflow 18 TWh/year. Same file otherwise.
    last_year = read_yaml("D", OUT / "group_d.yaml")
    last_year.add_attribute("gen.che-pv", "nominal_power_capacity", 6000, unit="MW")
    last_year.add_attribute(
        "storage.CHE_RES", "annual_natural_inflow_energy", 18_000_000, unit="MWh/year",
    )
    last_year.export_yaml(OUT / "group_d_2025.yaml")

    print("2 · Do the four groups describe the same system?")
    a = read_yaml("A", OUT / "group_a.yaml")
    for g in "BCD":
        diffs = compare(a, read_yaml(g, OUT / f"group_{g.lower()}.yaml"), "A", g)
        print(f"    A vs {g}: {len(diffs)} differences")

    print("3 · Group C receives Group A's system")
    path = receive("C", read_yaml("A", OUT / "group_a.yaml"))
    print(f"    wrote {path.relative_to(REPO)}")
    lines = path.read_text(encoding="utf-8").splitlines()
    hydro = next(i for i, line in enumerate(lines) if "reservoir_hydro" in line)
    for line in [l for l in lines if "demand_twh" in l] + lines[hydro - 1:hydro + 7]:
        print(f"      {line}")

    print("4 · Group A receives Group C's system")
    path = receive("A", read_yaml("C", OUT / "group_c.yaml"))
    print(f"    wrote {path.relative_to(REPO)}/")
    for name in ("plants.csv", "storage.csv"):
        print(f"      {name}")
        for line in (path / name).read_text(encoding="utf-8").splitlines():
            print(f"        {line}")

    print("5 · Round trip A → C → A")
    back = to_cesdm("A", receive("A", to_cesdm("C", receive("C", read_yaml("A", OUT / "group_a.yaml")))))
    print(f"    {len(compare(a, back, 'before', 'after'))} differences")

    print("6 · Every group to every other group")
    ok = 0
    for sender in GROUPS:
        sent = read_yaml(sender, OUT / f"group_{sender.lower()}.yaml")
        for receiver in GROUPS:
            if receiver == sender:
                continue
            arrived = to_cesdm(receiver, receive(receiver, sent))
            ok += not compare(sent, arrived)
    print(f"    {ok} of 12 exchanges preserve the system")


if __name__ == "__main__":
    main()
