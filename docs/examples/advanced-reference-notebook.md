# Advanced Tutorial — Multi-domain Reference Notebook

!!! abstract "Before you start"
    - **Prerequisites:** Complete [Build your first model](../get-started/first-model.md) first
    - **Time:** ~45–60 minutes
    - **You'll learn:** multi-domain system, profiles, hydro, interconnectors — all via Core [EAR](../reference/glossary.md#ear) API

!!! tip "Not your first tutorial"
    If you are new to CESDM, start with **[Build your first model](../get-started/first-model.md)** (~10 min). This notebook is the full Switzerland + neighbours reference model used throughout the documentation.

The CESDM repository includes an interactive Jupyter notebook that builds a **complete multi-domain energy system** using the core Entity–Attribute–Relation API.

Unlike the minimal first model, this notebook covers electricity, gas, and heat, plus profiles, reservoir hydro, interconnectors, and CHP coupling.

---

## Install Jupyter support

```bash
pip install -e ".[jupyter]"
```

---

## Location

```text
notebooks/building_your_cesdm_model.ipynb
docs/examples/reference_energy_system_model.py
```

Both build the same model. The notebook is the interactive Proxy companion to [Building your CESDM Model](building-first-model/overview.md) (Parts 1–4); the script is the Core EAR reference.

!!! warning "Run from repository root"
    Start Jupyter from `cesdm-toolbox/` so the notebook can find `schemas/cesdm/`.

---

## Running the notebook

```bash
jupyter lab
```

Open `notebooks/building_your_cesdm_model.ipynb` and run all cells sequentially.

For a focused walkthrough of `model.validate()` (enums, min/max, relations, units), open
`notebooks/cesdm_schema_validation.ipynb` (backed by `examples/example_validation.py`).

---

## What the notebook builds

- energy system model and multi-domain [carrier domains](../reference/glossary.md#carrier-domain);
- geographical regions and network nodes;
- electricity, gas, and heat demand and generation (full CH + neighbour fleet);
- reservoir hydro in CH/DE/FR/IT/AT and natural resources;
- [timestamp series](../reference/glossary.md#timestamp-series) and [profiles](../understand/profiles.md) (synthetic arrays → `profiles.h5`);
- eight cross-border NTCs (CH–neighbours + DE–FR, DE–AT, FR–IT, AT–IT) and CHP conversion;
- validation and export to [YAML](../reference/glossary.md#yaml) + [Frictionless](../reference/glossary.md#frictionless-data-package) + HDF5.

---

## Interactive inspection

The notebook includes helpers such as:

```python
print_entity(model, "gen.ch.wind")
print_class_counts(model)
```

Use these to inspect entities as the model grows.

---

## Export location

```text
output/reference_energy_system_model/
├── ch_neighbours_2030.yaml
├── profiles.h5
└── frictionless/
```

---

## Related material

| Resource | Purpose |
|----------|---------|
| [Core API tutorial (4 parts)](building-first-model/overview.md) | Same model as readable markdown |
| [Profiles guide](../understand/profiles.md) | Understand time series after Part 3 |
| [Carrier domains](../understand/carrier-domains.md) | Multi-domain scope after Part 4 |

---

## Next step

→ [Reference](../reference/index.md) · [Python API](../develop/python-api.md)
