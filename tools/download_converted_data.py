"""download_converted_data.py

Downloads ready-made CESDM packages (YAML, Frictionless, and HDF5
profiles) for the published TYNDP 2024 scenarios and the PyPSA nodal
example, and extracts them under ``converted_data/``.

Usage (from repository root or anywhere after install)::

    cesdm-download-converted-data
    cesdm-download-converted-data --insecure

    python -m tools.download_converted_data
    python tools/download_converted_data.py --insecure
"""

from __future__ import annotations

from tools.download_external_data import _cli

URL = "https://ethz.ch/content/dam/ethz/special-interest/mavt/ctr-energy-networks-fen-dam/data/cesdm_converted_data.zip"
ZIP_NAME = "cesdm_converted_data.zip"
EXTRACT_TO = "converted_data"


def main() -> None:
    _cli(
        URL,
        ZIP_NAME,
        description=__doc__.split("\n\n")[0],
        label="converted CESDM packages",
        extract_to=EXTRACT_TO,
    )


if __name__ == "__main__":
    main()
