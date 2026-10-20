# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

"""Run every example the toolbox and the documentation ship.

Each case is the command a reader is told to type, from the repository
root. A non-zero exit fails the test and keeps the end of the output.

TYNDP's full conversion and the PyPSA network import need the downloaded
files and take much longer than the other examples. They run when those
files are present and ``CESDM_RUN_SLOW_EXAMPLES=1`` is set. Otherwise they
are skipped, with the reason on the skip line.

    CESDM_RUN_SLOW_EXAMPLES=1 pytest tests/test_examples_run.py
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

# (name, commands, timeout seconds, required files, slow)
# A command is the argv after the interpreter. Required files are relative
# to the repository. Slow cases also wait for CESDM_RUN_SLOW_EXAMPLES=1.
CASES: list[tuple[str, tuple[tuple[str, ...], ...], int, tuple[str, ...], bool]] = [
    ("validation", (("examples/example_validation.py",),), 180, (), False),
    ("analysis-validation", (("examples/example_analysis_validation.py",),), 180, (), False),
    ("conversion-units", (("examples/example_conversion_units.py",),), 180, (), False),
    ("living-lab", (("docs/examples/living-lab/run.py",),), 180, (), False),
    ("bookshelf", (("docs/examples/bookshelf/run.py",),), 60, (), False),
    ("schema-extension", (("examples/example_schema_extension.py",),), 180, (), False),
    ("schema-augmentation", (("examples/schema_augmentation/example.py",),), 180, (), False),
    ("multienergy", (("examples/example_multienergy.py",),), 180, (), False),
    ("hydro-reservoir", (("examples/example_hydro_reservoir_plant.py",),), 180, (), False),
    ("kundur", (("examples/example_kundur_two_area.py",),), 180, (), False),
    ("power-flow-export", (("examples/example_cesdm_to_pandapower_and_matpower.py",),), 180, (), False),
    (
        "tyndp-sample",
        (
            (
                "examples/example_import_tyndp_proxy_api.py",
                "examples/sample_data/tyndp_sample_installed_capacities.csv",
                "--year",
                "2030",
                "--output",
                "output/tyndp_sample_example.yaml",
            ),
        ),
        180,
        (),
        False,
    ),
    (
        "four-groups",
        (
            ("docs/examples/four-research-groups/run_exchange.py",),
            ("docs/examples/four-research-groups/mistakes.py",),
            (
                "docs/examples/four-research-groups/compare.py",
                "output/four-research-groups/group_a.yaml",
                "output/four-research-groups/group_d_2025.yaml",
            ),
        ),
        240,
        (),
        False,
    ),
    (
        "swiss-analyses",
        (
            ("docs/examples/swiss-analyses/step1_complete.py",),
            ("docs/examples/swiss-analyses/step2_dispatch.py",),
            ("docs/examples/swiss-analyses/step3_power_flow.py",),
            ("docs/examples/swiss-analyses/step4_dynamics.py",),
            (
                "docs/examples/swiss-analyses/requirements_table.py",
                "GenerationUnit",
                "DemandUnit",
            ),
        ),
        240,
        (),
        False,
    ),
    (
        "pypsa-import",
        (("examples/example_import_pypsa.py",),),
        900,
        ("external_data/PYPSA/elec.nc",),
        True,
    ),
    (
        "tyndp-import",
        (("examples/example_import_tyndp.py",),),
        1800,
        ("external_data/TYNDP2024",),
        True,
    ),
]

_SCRIPT = re.compile(r"python\s+((?:examples|docs/examples)/[\w./-]+\.py)")


def _run(argv: tuple[str, ...], timeout: int) -> None:
    env = os.environ.copy()
    previous = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(ROOT) if not previous else str(ROOT) + os.pathsep + previous
    completed = subprocess.run(
        [sys.executable, *argv],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if completed.returncode == 0:
        return
    tail = (completed.stdout + "\n" + completed.stderr).strip()[-4000:]
    raise AssertionError(
        f"{' '.join(argv)} exited {completed.returncode}\n{tail}"
    )


def _covered_scripts() -> set[str]:
    return {command[0] for _name, commands, *_rest in CASES for command in commands}


def test_documented_example_commands_have_a_script():
    """Every `python examples/...py` line in the live docs points at a file."""
    missing = []
    for path in sorted((ROOT / "docs").rglob("*.md")):
        for script in _SCRIPT.findall(path.read_text(encoding="utf-8")):
            if not (ROOT / script).is_file():
                missing.append(f"{path.relative_to(ROOT)}: {script}")
    assert missing == []


def test_every_example_entry_point_is_in_the_check():
    """A new example with a __main__ block has to be added to CASES."""
    found = []
    for folder in (ROOT / "examples", ROOT / "docs" / "examples"):
        for path in folder.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "__main__" not in text:
                continue
            found.append(path.relative_to(ROOT).as_posix())
    missing = sorted(set(found) - _covered_scripts())
    assert missing == []


@pytest.mark.parametrize(
    "name,commands,timeout,needs,slow",
    CASES,
    ids=[case[0] for case in CASES],
)
def test_example_runs(name, commands, timeout, needs, slow):
    del name
    if slow and os.environ.get("CESDM_RUN_SLOW_EXAMPLES") != "1":
        pytest.skip("set CESDM_RUN_SLOW_EXAMPLES=1 to run the data imports")
    absent = [rel for rel in needs if not (ROOT / rel).exists()]
    if absent:
        pytest.skip("missing " + ", ".join(absent))
    for argv in commands:
        _run(argv, timeout)
