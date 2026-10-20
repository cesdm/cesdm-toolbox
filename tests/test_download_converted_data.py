# Copyright (c) 2026 Research Center for Energy Networks - ETH Zürich
# The CESDM project is part of the SWEET-CoSi consortium, funded by the
# Swiss Federal Office of Energy (SFOE) through its SWEET programme.

"""tests for tools/download_converted_data.py — no real network call."""

import io
import ssl
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest

import tools.download_converted_data as mod


def test_url_is_the_converted_archive():
    assert mod.URL.endswith("/cesdm_converted_data.zip")


def test_default_run_does_not_weaken_ssl_verification():
    captured = []

    def fake_download(target, *, ssl_context):
        captured.append((Path(target), ssl_context))
        raise SystemExit(0)

    with patch("sys.argv", ["download_converted_data.py"]):
        with patch.object(mod, "_download", side_effect=fake_download):
            with pytest.raises(SystemExit):
                mod.main()

    assert len(captured) == 1
    target, ssl_context = captured[0]
    assert ssl_context is None
    assert target.name == "cesdm_converted_data.zip"
    assert target.parent == mod._repo_root()


def test_insecure_flag_creates_an_unverified_context():
    captured = []

    def fake_download(target, *, ssl_context):
        captured.append(ssl_context)
        raise SystemExit(0)

    with patch("sys.argv", ["download_converted_data.py", "--insecure"]):
        with patch.object(mod, "_download", side_effect=fake_download):
            with pytest.raises(SystemExit):
                mod.main()

    ctx = captured[0]
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.verify_mode == ssl.CERT_NONE


def test_extract_lands_in_converted_data_and_skips_macos_junk(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("TYNDP2024/scenario.yaml", "format: cesdm-yaml\n")
        zf.writestr("__MACOSX/._scenario.yaml", "junk")
        zf.writestr("TYNDP2024/.DS_Store", "junk")
    archive = tmp_path / "cesdm_converted_data.zip"
    archive.write_bytes(buf.getvalue())
    dest = tmp_path / "converted_data"

    mod._extract(archive, dest)

    assert (dest / "TYNDP2024" / "scenario.yaml").is_file()
    assert not (dest / "__MACOSX").exists()
    assert not (dest / "TYNDP2024" / ".DS_Store").exists()
