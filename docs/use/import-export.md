# Import and export

CESDM models are portable as files. Analysis tools connect through **adapters**; they are not part of the CESDM core.

## Formats

| Format | Typical call | Best for |
|--------|--------------|----------|
| **YAML** | `export_yaml_hierarchical()`, `import_yaml()` | Version control, review, re-import |
| **Frictionless** | `export_frictionless()` | Tabular exchange, spreadsheets, pipelines |
| **HDF5 / Parquet profiles** | written with the model export | Large time series next to YAML metadata |

```python
output_dir = "output/my_study"
model.export_yaml_hierarchical(f"{output_dir}/my_study.yaml")
model.export_frictionless(
    f"{output_dir}/frictionless/",
    name="my-study",
    title="My study model",
    include_library="referenced",
)
```

Profile arrays stay outside the YAML. See [Profiles](../understand/profiles.md).

## Tool adapters

| Adapter | Status | Package / location |
|---------|--------|--------------------|
| PyPSA | In toolbox | `tools/import_pypsa.py` |
| pandapower | In toolbox | `tools/import_pandapower.py` |
| MATPOWER | In toolbox | `tools/import_matpower.py` |
| FlexECO | Separate package | `cesdm-flexeco` (`cesdm-yaml-to-flexeco`) |

Step-by-step conversion of **TYNDP 2024** tables and a PyPSA **`elec.nc`** is in [Convert TYNDP and PyPSA](../examples/import-tyndp-and-pypsa.md). Ready-made CESDM packages: `cesdm-download-converted-data`.

FlexECO conversion is an in-house adapter, not part of this toolbox. Install the sibling package and use its CLI:

```bash
pip install -e /path/to/cesdm-flexeco

cesdm-yaml-to-flexeco \
  --schema-root schemas/cesdm \
  --yaml model.yaml \
  --format hierarchical \
  --profiles-hdf5 profiles.h5 \
  --out-jpn out/scenario.jpn \
  --out-hdf5 out/profiles.h5
```

Writing a new adapter is covered in [Adapter development](../develop/adapter-development.md).

## Next

[Spatial aggregation](spatial-aggregation.md) · [Convert TYNDP and PyPSA](../examples/import-tyndp-and-pypsa.md)
