"""download_external_data.py

Downloads and extracts the external CESDM reference datasets (TYNDP 2024,
PyPSA network files) used by examples/example_import_tyndp_proxy_api.py's
full-pipeline mode and examples/example_import_pypsa.py.

Usage (from repository root or anywhere after install)::

    cesdm-download-external-data
    cesdm-download-external-data --insecure

    python -m tools.download_external_data
    python tools/download_external_data.py --insecure
"""

from __future__ import annotations

import argparse
import shutil
import ssl
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import zipfile

URL = "https://ethz.ch/content/dam/ethz/special-interest/mavt/ctr-energy-networks-fen-dam/data/cesdm_external_data.zip"
ZIP_NAME = "cesdm_external_data.zip"

_SSL_HELP = """\
SSL errors here are almost always one of two things, not a problem
with this script or with ethz.ch itself:

  1. Your network intercepts HTTPS traffic for inspection (common on
     corporate/institutional staff networks and VPNs) and presents its
     own certificate instead of the real one. Try a different network
     (mobile hotspot, home network, a VPN split tunnel that excludes
     this domain) to confirm, then ask your IT department for the
     proxy's CA certificate if you need to stay on this network.
  2. Your Python installation is missing an up-to-date certificate
     bundle -- on macOS with python.org's installer, run the
     "Install Certificates.command" script it ships with (in
     /Applications/Python <version>/), or `pip install --upgrade certifi`.

Only if you understand and accept the risk (this disables protection
against a man-in-the-middle attack, not just a certificate warning):
rerun with --insecure.\
"""


def _repo_root() -> Path:
    """Toolbox root (parent of ``tools/``), so extract always lands correctly."""
    return Path(__file__).resolve().parents[1]


def _download(url: str, target: Path, *, ssl_context: "ssl.SSLContext | None") -> None:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/zip,*/*",
        },
    )

    with urlopen(request, context=ssl_context) as response:
        total = int(response.headers.get("Content-Length", 0))

        with target.open("wb") as out:
            downloaded = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                downloaded += len(chunk)

                if total:
                    percent = downloaded / total * 100
                    print(f"\rDownloaded {percent:5.1f}%", end="")


# Optional single top-level folder in the zip; PYPSA/ and TYNDP2024/ should
# sit at the same level as in external_data/.
_ZIP_WRAPPERS = frozenset({"output", "converted_data"})


def _zip_parts(name: str) -> list[str] | None:
    posix = name.replace("\\", "/")
    parts = [p for p in posix.split("/") if p not in ("", ".")]
    if not parts or parts[0] == "__MACOSX" or parts[-1] == ".DS_Store":
        return None
    return parts


def _member_dest(name: str, *, strip: str | None = None) -> str | None:
    """Map a zip member to a relative extract path, or None to skip it."""
    parts = _zip_parts(name)
    if parts is None:
        return None
    if strip and parts[0] == strip:
        parts = parts[1:]
    if not parts:
        return None
    return "/".join(parts)


def _common_wrapper(names: list[str]) -> str | None:
    """Strip one wrapper dir if every kept member lives under it."""
    tops = {parts[0] for name in names if (parts := _zip_parts(name))}
    if len(tops) == 1:
        only = next(iter(tops))
        if only in _ZIP_WRAPPERS:
            return only
    return None


def _extract_zip(zf: zipfile.ZipFile, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    dest_resolved = dest.resolve()
    strip = _common_wrapper([info.filename for info in zf.infolist()])
    for info in zf.infolist():
        rel = _member_dest(info.filename, strip=strip)
        if rel is None:
            continue
        out = dest.joinpath(*rel.split("/"))
        out_resolved = out.resolve()
        if dest_resolved not in out_resolved.parents and out_resolved != dest_resolved:
            raise ValueError(f"Refusing zip path outside extract dir: {info.filename}")
        if info.is_dir() or info.filename.endswith("/"):
            out.mkdir(parents=True, exist_ok=True)
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(info) as src, out.open("wb") as dst:
            shutil.copyfileobj(src, dst)


def download_archive(
    url: str,
    zip_name: str,
    *,
    insecure: bool,
    label: str,
    extract_to: str | None = None,
) -> None:
    """Download ``url`` to the toolbox root as ``zip_name`` and extract it.

    If ``extract_to`` is set, create that folder under the toolbox root and
    extract the archive contents there. The converted-data archive uses the
    same top-level names as ``external_data/`` (``PYPSA/``, ``TYNDP2024/``).
    A single wrapping ``output/`` or ``converted_data/`` folder is stripped
    if present. Otherwise extract into the toolbox root, as the external-data
    archive already contains ``external_data/``.
    """
    ssl_context = None
    if insecure:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

    root = _repo_root()
    target = root / zip_name
    dest = root / extract_to if extract_to else root

    print(f"Downloading {label} from:\n{url}")
    if insecure:
        print("(TLS certificate verification disabled via --insecure)")
    _download(url, target, ssl_context=ssl_context)

    print("\nExtracting archive...")
    with zipfile.ZipFile(target, "r") as zf:
        if extract_to:
            _extract_zip(zf, dest)
        else:
            zf.extractall(root)

    print(f"{label.capitalize()} downloaded and extracted under:\n{dest}")


def _cli(
    url: str,
    zip_name: str,
    *,
    description: str,
    label: str,
    extract_to: str | None = None,
) -> None:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--insecure", action="store_true",
        help="Skip TLS certificate verification for this download. Only use "
             "this if you understand why verification is failing (see the "
             "message printed on failure) and trust the network you're on "
             "-- it removes protection against a man-in-the-middle attack, "
             "not just a certificate warning.",
    )
    args = parser.parse_args()

    try:
        download_archive(
            url,
            zip_name,
            insecure=args.insecure,
            label=label,
            extract_to=extract_to,
        )
    except HTTPError as e:
        raise SystemExit(f"Download failed: HTTP {e.code}")
    except URLError as e:
        if isinstance(e.reason, ssl.SSLCertVerificationError):
            print(f"Download failed: {e}\n", file=sys.stderr)
            print("This network intercepts HTTPS traffic or your certificate "
                  "bundle is outdated.\n" + _SSL_HELP, file=sys.stderr)
            raise SystemExit(1)
        raise SystemExit(f"Download failed: {e}")


def main() -> None:
    _cli(
        URL,
        ZIP_NAME,
        description=__doc__.split("\n\n")[0],
        label="external CESDM example data",
    )


if __name__ == "__main__":
    main()
