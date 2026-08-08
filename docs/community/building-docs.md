# Building the Documentation Locally

Preview the CESDM documentation site before publishing to [GitHub Pages](https://cesdm.github.io/cesdm-toolbox/).

## Requirements

- Python 3.11+
- Git

## Setup

From the **repository root** (where `mkdocs.yml` lives):

```bash
python -m venv .venv-docs
source .venv-docs/bin/activate   # Windows: .venv-docs\Scripts\activate

python -m pip install --upgrade pip
pip install -e /path/to/cesdm-toolbox    # provides ear + cesdm_schema_docs for API/schema docs
pip install -r docs-requirements.txt
```

If you do not have a local clone, install from GitHub instead:

```bash
pip install "git+https://github.com/cesdm/cesdm-toolbox.git@main"
pip install -r docs-requirements.txt
```

## Preview

```bash
mkdocs serve
```

Open the URL shown in the terminal (usually `http://127.0.0.1:8000/cesdm-toolbox/`).  
Stop the server with `Ctrl+C`.

## Production build

```bash
mkdocs build --strict
```

Output is written to `site/`. The GitHub Actions workflow in `.github/workflows/docs.yml` runs the same strict build and deploys to GitHub Pages on pushes to `main`.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ConfigError: The 'redirects' plugin is not installed` | Run `pip install -r docs-requirements.txt` |
| Mermaid diagrams show as code | Ensure `pymdownx.superfences` includes the `mermaid` custom fence in `mkdocs.yml` |
| Broken image paths | Run `mkdocs serve` from the repo root; use relative paths in Markdown |
| `ModuleNotFoundError: ear` during build | Install `cesdm-toolbox` first (`pip install -e /path/to/cesdm-toolbox` or from GitHub — see Setup above) |
| Schema reference shows empty entity blocks | Regenerate stubs and Markdown from the toolbox repo: `python -m tools.update_generated` (or `python -m tools.generate_cesdm_schema_stubs` then `python -m tools.generate_cesdm_schema_md`) |

## Regenerating schema reference

The **CESDM Schema Reference** is rendered by mkdocstrings from auto-generated Python stubs in `cesdm_schema_docs/` (same YAML source as the HTML companion). After schema changes in `cesdm-toolbox`:

```bash
cd /path/to/cesdm-toolbox
python -m tools.update_generated
```

Then copy `docs/reference/schema-reference.md` (and optionally `schema-reference.html`) into this docs tree if you maintain a separate checkout.

→ [Contributing](contributing.md)
