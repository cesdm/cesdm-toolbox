"""Rewrite directory hrefs so `site/index.html` works under file://."""

from __future__ import annotations

from pathlib import Path
import re

_HREF = re.compile(r'href="([^"]+)"')
_SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "javascript:", "data:")


def _rewrite(value: str) -> str:
    if value.startswith(_SKIP_PREFIXES):
        return value
    path, hash_sep, fragment = value.partition("#")
    if not path or Path(path).suffix:
        return value
    if not path.endswith("/"):
        path = f"{path}/"
    rewritten = f"{path}index.html"
    return f"{rewritten}{hash_sep}{fragment}" if hash_sep else rewritten


def on_post_build(config) -> None:
    site_dir = Path(config["site_dir"])
    for html_path in site_dir.rglob("*.html"):
        text = html_path.read_text(encoding="utf-8")
        updated = _HREF.sub(lambda match: f'href="{_rewrite(match.group(1))}"', text)
        if updated != text:
            html_path.write_text(updated, encoding="utf-8")
