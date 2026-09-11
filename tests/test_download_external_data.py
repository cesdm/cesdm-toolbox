"""
tests for tools/download_external_data.py and tools/download_converted_data.py

These tests exercise everything that *can* be tested without a real
network call: the SSL-specific error path prints actionable guidance
instead of a bare urllib error, the default is secure (no SSL context
override), and `--insecure` is a real, explicit opt-in rather than a
silent default.
"""

import ssl
import zipfile
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import pytest

import tools.download_converted_data as converted
import tools.download_external_data as external

DOWNLOADERS = [external, converted]


@pytest.mark.parametrize("mod", DOWNLOADERS)
def test_default_run_does_not_weaken_ssl_verification(mod):
    """No context override unless --insecure is explicitly given."""
    captured = []

    def fake_download(url, target, *, ssl_context):
        captured.append(ssl_context)
        raise SystemExit(0)

    with patch("sys.argv", ["download.py"]):
        with patch.object(external, "_download", side_effect=fake_download):
            with pytest.raises(SystemExit):
                mod.main()

    assert captured == [None]


@pytest.mark.parametrize("mod", DOWNLOADERS)
def test_insecure_flag_creates_an_unverified_context(mod):
    captured = []

    def fake_download(url, target, *, ssl_context):
        captured.append(ssl_context)
        raise SystemExit(0)

    with patch("sys.argv", ["download.py", "--insecure"]):
        with patch.object(external, "_download", side_effect=fake_download):
            with pytest.raises(SystemExit):
                mod.main()

    assert len(captured) == 1
    ctx = captured[0]
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.check_hostname is False
    assert ctx.verify_mode == ssl.CERT_NONE


@pytest.mark.parametrize("mod", DOWNLOADERS)
def test_ssl_certificate_error_gets_actionable_guidance(mod, capsys):
    """The exact error a user reported: a self-signed certificate in the
    chain, the signature of a TLS-intercepting network proxy."""
    cert_err = ssl.SSLCertVerificationError(
        "certificate verify failed: self-signed certificate in "
        "certificate chain (_ssl.c:1000)"
    )
    url_err = URLError(cert_err)

    with patch("sys.argv", ["download.py"]):
        with patch.object(external, "_download", side_effect=url_err):
            with pytest.raises(SystemExit) as exc_info:
                mod.main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    # Both likely causes explained, not just the raw urllib error.
    assert "intercepts HTTPS traffic" in captured.err
    assert "Install Certificates.command" in captured.err
    assert "--insecure" in captured.err


@pytest.mark.parametrize("mod", DOWNLOADERS)
def test_http_error_still_reports_the_status_code(mod):
    http_err = HTTPError(mod.URL, 404, "Not Found", {}, None)

    with patch("sys.argv", ["download.py"]):
        with patch.object(external, "_download", side_effect=http_err):
            with pytest.raises(SystemExit) as exc_info:
                mod.main()

    assert "404" in str(exc_info.value.code)


@pytest.mark.parametrize("mod", DOWNLOADERS)
def test_non_ssl_url_error_falls_through_to_the_generic_message(mod):
    """A URLError NOT caused by a certificate problem (e.g. DNS failure,
    connection refused) should not get the SSL-specific wall of text."""
    other_err = URLError("Name or service not known")

    with patch("sys.argv", ["download.py"]):
        with patch.object(external, "_download", side_effect=other_err):
            with pytest.raises(SystemExit) as exc_info:
                mod.main()

    assert "intercepts HTTPS traffic" not in str(exc_info.value.code)
    assert "Name or service not known" in str(exc_info.value.code)


@pytest.mark.parametrize("mod", DOWNLOADERS)
def test_download_target_is_under_repo_root(mod):
    """Zip path must not depend on the process CWD."""
    captured = []

    def fake_download(url, target, *, ssl_context):
        captured.append((url, Path(target)))
        raise SystemExit(0)

    with patch("sys.argv", ["download.py"]):
        with patch.object(external, "_download", side_effect=fake_download):
            with pytest.raises(SystemExit):
                mod.main()

    assert len(captured) == 1
    url, target = captured[0]
    assert url == mod.URL
    assert target.name == mod.ZIP_NAME
    assert target.parent == external._repo_root()


def test_member_dest_keeps_pypsa_and_tyndp_level():
    assert external._member_dest("TYNDP2024/cesdm/yaml/model.yaml") == (
        "TYNDP2024/cesdm/yaml/model.yaml"
    )
    assert external._member_dest("PYPSA/cesdm/frictionless/datapackage.json") == (
        "PYPSA/cesdm/frictionless/datapackage.json"
    )
    assert external._member_dest("__MACOSX/PYPSA/._.DS_Store") is None
    assert external._member_dest("TYNDP2024/.DS_Store") is None
    assert external._member_dest(
        "converted_data/PYPSA/model.yaml", strip="converted_data"
    ) == "PYPSA/model.yaml"


def test_extract_zip_writes_pypsa_and_tyndp_under_converted_data(tmp_path):
    archive = tmp_path / "sample.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("TYNDP2024/cesdm/yaml/model.yaml", "model: ok\n")
        zf.writestr("PYPSA/cesdm/frictionless/datapackage.json", "{}\n")
        zf.writestr("__MACOSX/PYPSA/._.DS_Store", "junk")
        zf.writestr("TYNDP2024/.DS_Store", "junk")

    dest = tmp_path / "converted_data"
    with zipfile.ZipFile(archive, "r") as zf:
        external._extract_zip(zf, dest)

    assert (dest / "TYNDP2024/cesdm/yaml/model.yaml").read_text() == "model: ok\n"
    assert (dest / "PYPSA/cesdm/frictionless/datapackage.json").read_text() == "{}\n"
    assert not (dest / "__MACOSX").exists()
    assert not (dest / ".DS_Store").exists()
    assert not (dest / "output").exists()


def test_extract_zip_strips_converted_data_wrapper(tmp_path):
    archive = tmp_path / "wrapped.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("converted_data/TYNDP2024/model.yaml", "ok\n")
        zf.writestr("converted_data/PYPSA/datapackage.json", "{}\n")

    dest = tmp_path / "converted_data"
    with zipfile.ZipFile(archive, "r") as zf:
        external._extract_zip(zf, dest)

    assert (dest / "TYNDP2024/model.yaml").read_text() == "ok\n"
    assert (dest / "PYPSA/datapackage.json").read_text() == "{}\n"
    assert not (dest / "converted_data").exists()
