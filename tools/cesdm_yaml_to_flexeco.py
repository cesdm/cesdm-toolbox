#!/usr/bin/env python3
"""
example_yaml_to_flexeco.py
==========================

Example: read a CESDM model stored as a YAML file (flat or hierarchical) and
export it as a FlexECO .jpn file plus a flat HDF5 time-series file.

Supported YAML formats
----------------------
hierarchical (default)
    Written by ``CesdmModel.export_yaml_hierarchical()``.
    Views are nested under their represented assets; each section groups
    entities by class name.

flat
    Written by ``CesdmModel.export_yaml_flat()``.
    All entities appear in a single flat list regardless of class; relations
    are expressed as entity-id references.

Both formats are fully round-trippable via the CESDM toolbox and carry
identical information.  Choose ``--format flat`` when your YAML was produced
by ``export_yaml_flat()``.

Time-series input options
-------------------------
1) CESDM HDF5 profile file::

       /profiles/<profile_id>/values       float64[length]
       /timestamps/<series_id>/            group (attrs in YAML entity)

   Written by ``write_profiles_h5_cesdm`` or ``CesdmModel.export_hdf5``.
   The output ``--out-hdf5`` is always in the flat FlexECO layout::

       /series_names  ASCII strings, shape (n_profiles,)
       /values        float64, shape (n_timesteps, n_profiles)

2) Wide CSV file::

       timestamp,profile.solar_1,profile.load_1
       2025-01-01T00:00:00,0.1,45.0
       2025-01-01T01:00:00,0.2,47.0

   The timestamp column is optional and ignored.
   Every other column is interpreted as one profile id.

Usage
-----
Hierarchical YAML::

    python examples/example_yaml_to_flexeco.py \\
        --schema-root schemas/cesdm \\
        --yaml        examples/case/model.yaml \\
        --profiles-hdf5 examples/case/profiles.h5 \\
        --out-jpn     output/scenario.jpn \\
        --out-hdf5    output/profiles.h5

Flat YAML::

    python examples/example_yaml_to_flexeco.py \\
        --schema-root schemas/cesdm \\
        --yaml        examples/case/model_flat.yaml \\
        --format      flat \\
        --profiles-csv examples/case/profiles.csv \\
        --out-jpn     output/scenario.jpn \\
        --out-hdf5    output/profiles.h5
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, Iterable, Optional

import numpy as np

def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]

_REPO_ROOT = _repo_root()
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cesdm_toolbox import build_model_from_yaml           # noqa: E402
from tools.import_flexeco import export_to_flexeco, _attach_profile_values  # noqa: E402


# ---------------------------------------------------------------------------
# Profile-value readers  (shared with example_frictionless_to_flexeco.py)
# ---------------------------------------------------------------------------

def read_cesdm_profile_hdf5(path: str | Path) -> Dict[str, np.ndarray]:
    """
    Read numeric profile values from the CESDM HDF5 profile layout.

    Expected layout
    ---------------
    /profiles/<profile_id>/values : float64[length]
        One 1-D dataset per CESDM Profile entity.

    Returns
    -------
    dict[str, np.ndarray]
        profile_id -> 1-D float64 array
    """
    import h5py

    path = Path(path)
    values: Dict[str, np.ndarray] = {}

    with h5py.File(path, "r") as hf:
        if "profiles" not in hf:
            raise ValueError(
                f"{path} is not a CESDM profile HDF5 file. "
                "Expected group /profiles/<profile_id>/values. "
                "Note: flat FlexECO HDF5 input is not accepted here."
            )
        for profile_id, grp in hf["profiles"].items():
            if "values" not in grp:
                continue
            values[str(profile_id)] = np.asarray(grp["values"][:], dtype=np.float64).ravel()

    if not values:
        raise ValueError(
            f"{path} contains /profiles but no /profiles/<profile_id>/values datasets."
        )
    return values


def read_wide_profile_csv(path: str | Path) -> Dict[str, np.ndarray]:
    """
    Read profile values from a wide CSV file.

    The optional columns ``timestamp``, ``time`` or ``datetime`` are ignored.
    Every remaining column becomes one profile series.
    """
    path = Path(path)
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header: {path}")

        time_cols = {"timestamp", "time", "datetime", "date_time"}
        profile_cols = [c for c in reader.fieldnames if c not in time_cols]
        raw: Dict[str, list[float]] = {c: [] for c in profile_cols}

        for row_idx, row in enumerate(reader, start=2):
            for col in profile_cols:
                cell = (row.get(col) or "").strip()
                if cell == "":
                    raw[col].append(np.nan)
                else:
                    try:
                        raw[col].append(float(cell))
                    except ValueError as exc:
                        raise ValueError(
                            f"Non-numeric value in {path}, row {row_idx}, "
                            f"column {col!r}: {cell!r}"
                        ) from exc

    return {k: np.asarray(v, dtype=np.float64) for k, v in raw.items()}


def load_profile_values(
    *,
    profiles_hdf5: Optional[str | Path] = None,
    profiles_csv: Optional[str | Path] = None,
) -> Dict[str, np.ndarray]:
    """Merge profile arrays from optional HDF5 and/or CSV inputs."""
    values: Dict[str, np.ndarray] = {}
    if profiles_hdf5:
        values.update(read_cesdm_profile_hdf5(profiles_hdf5))
    if profiles_csv:
        values.update(read_wide_profile_csv(profiles_csv))
    return values


# ---------------------------------------------------------------------------
# YAML -> FlexECO
# ---------------------------------------------------------------------------

def export_yaml_cesdm_to_flexeco(
    *,
    schema_root: str | Path,
    yaml_path: str | Path,
    yaml_format: str,          # "hierarchical" | "flat"
    out_jpn: str | Path,
    out_hdf5: str | Path,
    profiles_hdf5: Optional[str | Path] = None,
    profiles_csv: Optional[str | Path] = None,
) -> None:
    """
    Read a CESDM YAML file and export FlexECO .jpn + HDF5.

    Parameters
    ----------
    schema_root :
        Directory containing the CESDM schema YAML files.
    yaml_path :
        Input CESDM model YAML file (flat or hierarchical).
    yaml_format :
        ``"hierarchical"`` — use ``import_yaml_hierarchical()``
        ``"flat"``         — use ``import_yaml_flat()``
    out_jpn :
        Output FlexECO JSON (.jpn) path.
    out_hdf5 :
        Output FlexECO flat HDF5 profile matrix path.
    profiles_hdf5 :
        Optional CESDM HDF5 profile file (``/profiles/<id>/values`` layout).
    profiles_csv :
        Optional wide CSV profile file.
    """
    schema_root = Path(schema_root)
    yaml_path   = Path(yaml_path)
    out_jpn     = Path(out_jpn)
    out_hdf5    = Path(out_hdf5)

    # 1) Load schema.
    print(f"Loading schema from {schema_root} …")
    model = build_model_from_yaml(str(schema_root))

    # 2) Import the CESDM YAML model.
    print(f"Importing YAML ({yaml_format}): {yaml_path} …")
    if yaml_format == "hierarchical":
        model.import_yaml_hierarchical(str(yaml_path))
    elif yaml_format == "flat":
        model.import_yaml_flat(str(yaml_path))
    else:
        raise ValueError(f"Unknown --format value: {yaml_format!r}. Use 'hierarchical' or 'flat'.")

    # Print a brief entity count summary.
    total = sum(len(v) for v in model.entities.values())
    print(f"Loaded {total} entities across {len(model.entities)} classes:")
    for cls, ents in sorted(model.entities.items()):
        if ents:
            print(f"  {cls}: {len(ents)}")

    # 3) Load and attach numeric profile arrays.
    profile_values = load_profile_values(
        profiles_hdf5=profiles_hdf5,
        profiles_csv=profiles_csv,
    )

    if profile_values:
        attached = _attach_profile_values(model, profile_values)
        print(f"Attached {attached}/{len(profile_values)} profile arrays.")
    else:
        print(
            "No profile-value file supplied. "
            "FlexECO HDF5 will contain zeros for referenced profiles."
        )

    # 4) Export FlexECO JSON + flat HDF5 time-series matrix.
    out_jpn.parent.mkdir(parents=True, exist_ok=True)
    out_hdf5.parent.mkdir(parents=True, exist_ok=True)

    export_to_flexeco(model, out_jpn, hdf5_path=out_hdf5)
    print(f"Wrote FlexECO JPN:  {out_jpn}")
    print(f"Wrote FlexECO HDF5: {out_hdf5}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Export a CESDM YAML model (flat or hierarchical) to FlexECO .jpn + HDF5 profiles.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Required
    parser.add_argument(
        "--schema-root", required=True,
        help="Path to the CESDM schemas directory.",
    )
    parser.add_argument(
        "--yaml", required=True, metavar="FILE",
        help="Input CESDM YAML model file.",
    )
    parser.add_argument(
        "--out-jpn", required=True, metavar="FILE",
        help="Output FlexECO .jpn JSON path.",
    )
    parser.add_argument(
        "--out-hdf5", required=True, metavar="FILE",
        help="Output FlexECO profile HDF5 path (flat /series_names + /values layout).",
    )

    # YAML format
    parser.add_argument(
        "--format", dest="yaml_format",
        choices=["hierarchical", "flat"],
        default="hierarchical",
        help=(
            "YAML format of the input file. "
            "'hierarchical' = export_yaml_hierarchical() output; "
            "'flat' = export_yaml_flat() output."
        ),
    )

    # Optional profile inputs
    parser.add_argument(
        "--profiles-hdf5", default=None, metavar="FILE",
        help=(
            "Optional CESDM HDF5 profile file with /profiles/<profile_id>/values layout. "
            "This is the CESDM input format — not the flat FlexECO output format."
        ),
    )
    parser.add_argument(
        "--profiles-csv", default=None, metavar="FILE",
        help=(
            "Optional wide CSV profile file. "
            "Column headers must match Profile entity ids in the model."
        ),
    )

    args = parser.parse_args(argv)

    export_yaml_cesdm_to_flexeco(
        schema_root   = args.schema_root,
        yaml_path     = args.yaml,
        yaml_format   = args.yaml_format,
        out_jpn       = args.out_jpn,
        out_hdf5      = args.out_hdf5,
        profiles_hdf5 = args.profiles_hdf5,
        profiles_csv  = args.profiles_csv,
    )


if __name__ == "__main__":
    main()
