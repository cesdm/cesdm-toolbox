"""Rewrite a built MkDocs `site/` so pages open under file://.

Not a MkDocs plugin. Run it after `mkdocs build`:

    python tools/mkdocs_file_links.py
    python tools/mkdocs_file_links.py site
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
import re

_HREF = re.compile(r'href="([^"]+)"')
_SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "javascript:", "data:")
_MATERIAL_RESTORE = re.compile(
    r'<script>var palette=__md_get\("__palette"\);.*?</script>',
    re.DOTALL,
)
_PALETTE_SCRIPT = """<script>
(function () {
  var KEY = "cesdm-docs-palette-index";
  var form = document.querySelector("[data-cesdm-palette]");
  if (!form) return;
  var inputs = Array.prototype.slice.call(form.querySelectorAll('input[name="__palette"]'));
  function apply(index, persist) {
    var input = inputs[index];
    if (!input) return;
    input.checked = true;
    document.body.setAttribute("data-md-color-scheme", input.getAttribute("data-md-color-scheme") || "default");
    inputs.forEach(function (el, i) {
      var label = el.nextElementSibling;
      if (label && label.tagName === "LABEL") {
        if (i === index) label.removeAttribute("hidden");
        else label.setAttribute("hidden", "");
      }
    });
    if (persist) {
      try { localStorage.setItem(KEY, String(index)); } catch (e) {}
    }
  }
  var index = 0;
  try {
    var saved = localStorage.getItem(KEY);
    if (saved !== null) index = parseInt(saved, 10) || 0;
  } catch (e) {}
  inputs.forEach(function (input, i) {
    input.addEventListener("change", function () {
      if (input.checked) apply(i, true);
    });
  });
  apply(index, false);
})();
</script>"""


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


def _fix_palette(text: str) -> str:
    text = text.replace(
        'data-md-component="palette"',
        "data-cesdm-palette",
        1,
    )
    text = text.replace(
        'type="radio" name="__palette" id="__palette_0">',
        'type="radio" name="__palette" id="__palette_0" checked>',
        1,
    )
    text = text.replace(
        'title="Switch to dark mode" for="__palette_1" hidden>',
        'title="Switch to dark mode" for="__palette_1">',
        1,
    )
    text = _MATERIAL_RESTORE.sub("", text)
    if "cesdm-docs-palette-index" not in text:
        marker = "</form>"
        form_end = text.find(
            marker,
            text.find("data-cesdm-palette") if "data-cesdm-palette" in text else 0,
        )
        if form_end != -1:
            insert_at = form_end + len(marker)
            text = text[:insert_at] + "\n" + _PALETTE_SCRIPT + text[insert_at:]
    return text


def process_site(site_dir: Path) -> int:
    if not site_dir.is_dir():
        raise FileNotFoundError(f"site directory not found: {site_dir}")
    changed = 0
    for html_path in site_dir.rglob("*.html"):
        text = html_path.read_text(encoding="utf-8")
        updated = _HREF.sub(lambda match: f'href="{_rewrite(match.group(1))}"', text)
        updated = _fix_palette(updated)
        if updated != text:
            html_path.write_text(updated, encoding="utf-8")
            changed += 1
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "site_dir",
        nargs="?",
        default="site",
        type=Path,
        help="Built MkDocs output directory (default: site)",
    )
    args = parser.parse_args(argv)
    changed = process_site(args.site_dir.resolve())
    print(f"Updated {changed} HTML files in {args.site_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
