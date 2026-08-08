#!/usr/bin/env python3
"""
example_frictionless_to_flexeco.py
==================================

Example: read a CESDM model stored as a Frictionless Data Package and export it
as a FlexECO .jpn file plus a flat HDF5 time-series file.

Expected CESDM/Frictionless layout
----------------------------------
<package_dir>/
    datapackage.json
    resources/
        ElectricalBus.csv
        GenerationUnit.csv
        DemandUnit.csv
        Profile.csv
        TimestampSeries.csv
        ...

Time-series input options
-------------------------
1) Explicit HDF5 file with CESDM profile layout::

       /profiles/<profile_id>/values       float64[length]
       /profiles/<profile_id>.attrs[...]   CESDM profile metadata
       /timestamps/<series_id>/values      optional int64 epoch timestamps

   This is the layout written by ``CesdmModel.export_hdf5``. The output
   ``--out-hdf5`` is always written in the flat FlexECO layout:

       /series_names  ASCII strings, shape (n_profiles,)
       /values        float64, shape (n_timesteps, n_profiles)

2) Wide CSV file::

       timestamp,profile.solar_1,profile.load_1
       2025-01-01T00:00:00,0.1,45.0
       2025-01-01T01:00:00,0.2,47.0

   The timestamp column is optional and ignored for FlexECO profile export.
   Every other column is interpreted as one profile id.

3) Auto-discovery from the Frictionless datapackage:
   A resource is treated as time-series data if it has either
   ``"cesdm:role": "timeseries"`` or a name/title containing
   ``timeseries``, ``time_series``, ``profile_values`` or ``profiles_values``.

Usage
-----
python examples/example_frictionless_to_flexeco.py \
    --schema-root schemas/cesdm \
    --datapackage examples/frictionless_case \
    --profiles-hdf5 examples/frictionless_case/profiles.h5 \
    --out-jpn output/scenario.jpn \
    --out-hdf5 output/profiles.h5

or with CSV profiles::

python examples/example_frictionless_to_flexeco.py \
    --schema-root schemas/cesdm \
    --datapackage examples/frictionless_case \
    --profiles-csv examples/frictionless_case/resources/profile_values.csv \
    --out-jpn output/scenario.jpn \
    --out-hdf5 output/profiles.h5
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional

import numpy as np

# Make the repository root importable when this example is run directly.
def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]

_REPO_ROOT = _repo_root()
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cesdm_toolbox import build_model_from_yaml  # noqa: E402
from tools.import_flexeco import export_to_flexeco, _attach_profile_values  # noqa: E402


# ---------------------------------------------------------------------------
# Profile-value readers
# ---------------------------------------------------------------------------

def read_cesdm_profile_hdf5(path: str | Path) -> Dict[str, np.ndarray]:
    """
    Read numeric profile values from the CESDM HDF5 profile layout.

    Expected input layout
    ---------------------
    /profiles/<profile_id>/values : float64[length]
        One 1D numeric dataset per CESDM Profile entity.

    /timestamps/<timestamp_series_id>/values : int64[length], optional
        Timestamp values are read by the CESDM importer when needed, but they
        are not written to the FlexECO flat profile matrix.

    This is intentionally different from the output ``--out-hdf5`` format.
    ``--out-hdf5`` is written by ``export_to_flexeco`` as the flat FlexECO
    layout with ``/series_names`` and ``/values``.

    Returns
    -------
    dict[str, np.ndarray]
        profile_id -> 1D float64 array
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
            arr = np.asarray(grp["values"][:], dtype=np.float64).ravel()
            values[str(profile_id)] = arr

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
        values: Dict[str, list[float]] = {c: [] for c in profile_cols}

        for row_idx, row in enumerate(reader, start=2):
            for col in profile_cols:
                raw = (row.get(col) or "").strip()
                if raw == "":
                    values[col].append(np.nan)
                else:
                    try:
                        values[col].append(float(raw))
                    except ValueError as exc:
                        raise ValueError(
                            f"Non-numeric value in {path}, row {row_idx}, "
                            f"column {col!r}: {raw!r}"
                        ) from exc

    return {k: np.asarray(v, dtype=np.float64) for k, v in values.items()}


def discover_timeseries_resources(datapackage_dir: str | Path) -> list[Path]:
    """
    Return CSV resources in the Frictionless package that look like profile values.
    """
    base = Path(datapackage_dir)
    dp_path = base / "datapackage.json"
    if not dp_path.exists():
        return []

    package = json.loads(dp_path.read_text(encoding="utf-8"))
    result: list[Path] = []
    markers = ("timeseries", "time_series", "profile_values", "profiles_values")

    for resource in package.get("resources", []):
        role = str(resource.get("cesdm:role", "")).lower()
        name = str(resource.get("name", "")).lower()
        title = str(resource.get("title", "")).lower()
        path = resource.get("path")
        if not path:
            continue

        is_timeseries = role == "timeseries" or any(
            marker in name or marker in title for marker in markers
        )
        if not is_timeseries:
            continue

        file_path = base / path
        if file_path.suffix.lower() == ".csv" and file_path.exists():
            result.append(file_path)

    return result


def load_profile_values(
    *,
    datapackage_dir: str | Path,
    profiles_hdf5: Optional[str | Path] = None,
    profiles_csv: Optional[str | Path] = None,
) -> Dict[str, np.ndarray]:
    """
    Load profile arrays from explicit HDF5/CSV inputs or from timeseries resources
    declared in the Frictionless datapackage.
    """
    values: Dict[str, np.ndarray] = {}

    if profiles_hdf5:
        values.update(read_cesdm_profile_hdf5(profiles_hdf5))

    if profiles_csv:
        values.update(read_wide_profile_csv(profiles_csv))

    if not values:
        for csv_resource in discover_timeseries_resources(datapackage_dir):
            values.update(read_wide_profile_csv(csv_resource))

    return values


# ---------------------------------------------------------------------------
# CESDM/Frictionless -> FlexECO
# ---------------------------------------------------------------------------

def export_frictionless_cesdm_to_flexeco(
    *,
    schema_root: str | Path,
    datapackage_dir: str | Path,
    out_jpn: str | Path,
    out_hdf5: str | Path,
    profiles_hdf5: Optional[str | Path] = None,
    profiles_csv: Optional[str | Path] = None,
) -> None:
    """
    Read a CESDM Frictionless Data Package and export FlexECO .jpn + HDF5.
    """
    schema_root = Path(schema_root)
    datapackage_dir = Path(datapackage_dir)
    out_jpn = Path(out_jpn)
    out_hdf5 = Path(out_hdf5)

    # 1) Load empty CESDM model from schemas.
    model = build_model_from_yaml(str(schema_root))

    # 2) Import CESDM entities from Frictionless resources.
    #    import_frictionless is defined on ear_toolbox.Model and inherited by CesdmModel.
    stats = model.import_frictionless(datapackage_dir)
    print("Imported Frictionless resources:")
    for class_name, count in sorted(stats.items()):
        print(f"  {class_name}: {count}")

    # 3) Load numeric CESDM profile arrays and attach them to Profile entities.
    #    Important: --profiles-hdf5 is CESDM format
    #       /profiles/<profile_id>/values
    #    while --out-hdf5 is exported as FlexECO flat format
    #       /series_names and /values.
    profile_values = load_profile_values(
        datapackage_dir=datapackage_dir,
        profiles_hdf5=profiles_hdf5,
        profiles_csv=profiles_csv,
    )

    if profile_values:
        attached = _attach_profile_values(model, profile_values)
        print(f"Attached {attached}/{len(profile_values)} profile arrays.")
    else:
        print(
            "No profile-value file found. FlexECO HDF5 will contain zeros for "
            "referenced profiles."
        )

    # 4) Export FlexECO JSON plus flat HDF5 time-series matrix.
    export_to_flexeco(model, out_jpn, hdf5_path=out_hdf5)
    print(f"Wrote FlexECO JPN:  {out_jpn}")
    print(f"Wrote FlexECO HDF5: {out_hdf5}")


def main(argv: Optional[Iterable[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Export a CESDM Frictionless Data Package to FlexECO .jpn + HDF5 profiles."
    )
    parser.add_argument("--schema-root", required=True, help="Path to CESDM schemas directory.")
    parser.add_argument("--datapackage", required=True, help="Directory containing datapackage.json.")
    parser.add_argument("--out-jpn", required=True, help="Output FlexECO .jpn JSON path.")
    parser.add_argument("--out-hdf5", required=True, help="Output FlexECO profile HDF5 path.")
    parser.add_argument(
        "--profiles-hdf5",
        default=None,
        help="Optional input CESDM HDF5 profile file with /profiles/<profile_id>/values. Output --out-hdf5 is FlexECO flat format.",
    )
    parser.add_argument(
        "--profiles-csv",
        default=None,
        help="Optional input wide CSV profile file. Columns must match Profile entity ids.",
    )
    args = parser.parse_args(argv)

    export_frictionless_cesdm_to_flexeco(
        schema_root=args.schema_root,
        datapackage_dir=args.datapackage,
        out_jpn=args.out_jpn,
        out_hdf5=args.out_hdf5,
        profiles_hdf5=args.profiles_hdf5,
        profiles_csv=args.profiles_csv,
    )


if __name__ == "__main__":
    main()
