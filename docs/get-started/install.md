# Installation

Four commands, then [build your first model](first-model.md).

## 1. Prerequisites

Python 3.11 or newer, Git and pip:

```bash
python --version
git --version
```

## 2. Clone the repository

```bash
git clone https://github.com/cesdm/cesdm-toolbox.git
cd cesdm-toolbox
```

## 3. Create a virtual environment

=== "Linux / macOS"

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

=== "Windows"

    ```powershell
    python -m venv .venv
    .venv\Scripts\activate
    ```

??? note "uv, Poetry or Conda instead"
    **uv:** `uv venv .venv` then activate as above.

    **Poetry:** `poetry install` then `poetry shell`.

    **Conda:** `conda create --name cesdm python=3.12` then `conda activate cesdm`.

## 4. Install CESDM

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -e .
```

## Check that it worked

```bash
python -c "from cesdm_toolbox import build_model_from_yaml; print('CESDM ready')"
```

If that prints `CESDM ready`, continue with **[Build your first model](first-model.md)**.

---

??? note "Optional extras"
    ```bash
    pip install -e ".[jupyter]"   # notebooks
    pip install -e ".[docs]"      # documentation
    pip install -e ".[dev]"       # tests and tooling
    pip install -e ".[all]"       # everything
    ```

??? note "Repository structure"
    ```text
    schemas/cesdm/            # CESDM vocabulary
    library/default_library/  # shared carriers and technologies
    docs/examples/            # runnable tutorial scripts
    tools/                    # import / export helpers
    ```

    You do not need to understand these folders before running the first example.

## Troubleshooting

**`ModuleNotFoundError`** — activate the virtual environment and run `pip install -e .` from the repository root.

**`ImportError` in a notebook** — select the environment in which CESDM was installed, or install the Jupyter extra and start Jupyter from the repository root.
