# Convert TYNDP 2024 and PyPSA networks

This page turns **ENTSO-E TYNDP 2024** tables and a **PyPSA nodal `elec.nc`** into CESDM files. CESDM provides the shared system representation; it does not run the original TYNDP or PyPSA types of analysis.

You have two options:

| Option | Use it when |
|--------|-------------|
| **[1. Download the converted data](#1-download-the-converted-data)** | You want the published TYNDP scenarios and the PyPSA nodal example as CESDM YAML, Frictionless and HDF5 profiles, without running the importers. |
| **[2. Download the raw data and convert yourself](#2-download-the-raw-data-and-convert-yourself)** | You want to run the TYNDP or PyPSA importer yourself and create the CESDM models and save them in different CESDM formats. |

Either path gives you the same CESDM formats. What to do with those files is under **[3. After the conversion](#3-after-the-conversion)**.

Do **[Install](../get-started/install.md)** first if you use option 2. You do not need the first-model tutorial.

---

## 1. Download the converted data

Ready-made CESDM packages for the published TYNDP 2024 scenarios (NT 2030/2040, DE 2030/2040/2050, GA 2030/2040/2050, weather year 2009) and the PyPSA nodal example:

```bash
cesdm-download-converted-data
```

Equivalent: `python -m tools.download_converted_data`. If TLS verification fails on a campus or VPN network, add `--insecure` — only if you trust the network.

This creates `converted_data/` in the repository root:

```text
cesdm-toolbox/
├── schemas/cesdm/
├── library/
├── examples/
└── converted_data/
    ├── PYPSA/
    └── TYNDP2024/
```

Manual alternative: [cesdm_converted_data.zip](https://ethz.ch/content/dam/ethz/special-interest/mavt/ctr-energy-networks-fen-dam/data/cesdm_converted_data.zip).

Each study is YAML (hierarchical + flat), a Frictionless package (`datapackage.json` + CSVs), and `profiles.h5`. Continue at [3. After the conversion](#3-after-the-conversion).

---

## 2. Download the raw data and convert yourself

### 2.1 Install importer extras

From the repository root, with your virtual environment active:

```bash
pip install -e ".[pypsa,geo]"
```

`[pypsa,geo]` adds PyPSA and GeoPandas (needed for the NUTS shapefile). The TYNDP importer uses packages already installed with the toolbox.

### 2.2 Download the raw source data

The official TYNDP CSVs and the PyPSA `elec.nc` are **not** in this repository. After `pip install -e .`, download and extract them from the repository root:

```bash
cesdm-download-external-data
```

That fetches the ETH archive and unpacks it so `external_data/` sits next to `schemas/` and `examples/`. Equivalent: `python -m tools.download_external_data`. If TLS verification fails on a campus or VPN network, `cesdm-download-external-data --insecure` skips certificate checks — only use that if you trust the network.

Manual alternative: download [cesdm_external_data.zip](https://ethz.ch/content/dam/ethz/special-interest/mavt/ctr-energy-networks-fen-dam/data/cesdm_external_data.zip), extract it, and put the resulting `external_data/` folder in the repository root.

You should have:

```text
cesdm-toolbox/
├── schemas/cesdm/
├── library/
├── examples/
└── external_data/
    ├── PYPSA/
    │   ├── elec.nc
    │   └── NUTS_RG_20M_2021_4326.shp
    └── TYNDP2024/
        ├── TYNDP24_Nodes.csv
        ├── TYNDP24_InstalledCapacities.csv
        ├── TYNDP24_DemandProfiles.csv
        ├── TYNDP24_GenProfiles.csv
        ├── TYNDP24_HydroInflows.csv
        ├── TYNDP24_StorageCapacities.csv
        └── TYNDP24_NTC_types.csv
```

Check:

```bash
ls external_data/TYNDP2024/TYNDP24_Nodes.csv
ls external_data/PYPSA/elec.nc
```

### 2.3 TYNDP 2024 → CESDM

A TYNDP **scenario** in this importer is one combination of **policy**, **scenario year** and **climate / weather year**. Example: policy `NT`, year `2030`, climate year `2009`.

The pipeline lives in `examples/example_import_tyndp.py`. The function that runs all steps is `build_cesdm_model_from_tyndp_installed_capacities`.

#### What the importer reads

| File | Used for |
|------|----------|
| `TYNDP24_Nodes.csv` | Buses and countries |
| `TYNDP24_InstalledCapacities.csv` | Generation, storage power, some demand |
| `TYNDP24_DemandProfiles.csv` | Hourly demand |
| `TYNDP24_GenProfiles.csv` | Renewable availability |
| `TYNDP24_HydroInflows.csv` | Reservoir inflows |
| `TYNDP24_StorageCapacities.csv` | Storage energy (MWh) |
| `TYNDP24_NTC_types.csv` | Interconnectors |

Rows are filtered by the policy / year / climate-year you pass in.

#### What happens, in order

1. Load the CESDM schema (`schemas/cesdm`).
2. Import libraries (default library, regions, optional TYNDP generator types).
3. Create geographical regions and electrical buses from the nodes file.
4. Create generation and storage assets from installed capacities.
5. Create demand assets that appear in the capacities file (for example electrolyser and heat-pump loads).
6. Create one shared hourly `TimestampSeries`.
7. Attach demand, renewable and hydro-inflow profiles.
8. Fill storage energy capacities.
9. Create NTC interconnectors.
10. Validate the model.
11. Write YAML, HDF5 profiles and a Frictionless package.

#### Convert one scenario

From the repository root:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path("examples").resolve()))
from example_import_tyndp import build_cesdm_model_from_tyndp_installed_capacities

build_cesdm_model_from_tyndp_installed_capacities(
    schema_path="schemas/cesdm",
    data_folder="external_data/TYNDP2024/",
    output_folder="output/TYNDP2024/",
    policy="NT",
    year=2030,
    climate_year=2009,
    drop_zero=True,
)
```

`data_folder` must end with `/`. Change `policy`, `year` and `climate_year` for another published TYNDP combination (`DE`, `GA`, `2040`, `2050`, …).

#### Convert the default scenario set

The script’s `__main__` block runs National Trends for 2030 and 2040, then Distributed Energy and Global Ambition for 2030, 2040 and 2050, each with weather year 2009:

```bash
python examples/example_import_tyndp.py
```

That can take a long time. Prefer the single-scenario call while you are testing.

#### Where the CESDM files land

```text
output/TYNDP2024/SC_<policy>_SY_<year>_WY_<climate_year>/
└── cesdm/
    ├── yaml/            # hierarchical + flat YAML
    ├── profiles/        # profiles.h5
    └── frictionless/    # datapackage.json + CSVs
```

Example: `output/TYNDP2024/SC_NT_SY_2030_WY_2009/`.

#### Optional: Proxy-API variant

`examples/example_import_tyndp_proxy_api.py` follows the same mapping rules and can run a full folder or a single capacities CSV. For the complete, production-style import use `example_import_tyndp.py`.

```bash
python examples/example_import_tyndp_proxy_api.py \
  --data-folder external_data/TYNDP2024/ \
  --year 2030 --policy NT \
  --output-folder output/TYNDP2024/
```

### 2.4 PyPSA `elec.nc` → CESDM

This path converts a **nodal PyPSA NetCDF** (the bundled `elec.nc` or your own `*.nc`) into CESDM. The mapping lives in `tools/import_pypsa.py`; the runnable wrapper is `examples/example_import_pypsa.py`.

#### What happens, in order

1. Read the PyPSA network from NetCDF.
2. Create a CESDM model from `schemas/cesdm`.
3. Map carriers, buses, lines/links, generators, storage, loads and time series.
4. Optionally assign NUTS regions from the shapefile (needs GeoPandas).
5. Validate the model.
6. Write YAML, HDF5 profiles and a Frictionless package.

#### Convert the bundled nodal network

From the repository root:

```bash
python examples/example_import_pypsa.py \
  --nc-path external_data/PYPSA/elec.nc \
  --schema-dir schemas/cesdm \
  --nuts-shapefile external_data/PYPSA/NUTS_RG_20M_2021_4326.shp \
  --output-dir output/PYPSA/nodal/
```

Omit `--nuts-shapefile` if you do not need sub-national regions.

#### Convert your own `*.nc`

```bash
python examples/example_import_pypsa.py \
  --nc-path /path/to/your_network.nc \
  --schema-dir schemas/cesdm \
  --output-dir output/pypsa_nodal_model/custom/
```

#### Where the CESDM files land

```text
output/PYPSA/nodal/
└── cesdm/
    ├── yaml/            # hierarchical + flat YAML
    ├── profiles/        # profiles.h5
    └── frictionless/    # datapackage.json + CSVs
```

#### Same conversion from Python

```python
from import_pypsa import build_cesdm_from_pypsa

model, profiles_values = build_cesdm_from_pypsa(
    nc_path="external_data/PYPSA/elec.nc",
    schema_dir="schemas/cesdm",
    nuts_shapefile="external_data/PYPSA/NUTS_RG_20M_2021_4326.shp",
)
errors = model.validate()
model.export_yaml_hierarchical("output/PYPSA/nodal/cesdm/yaml/pypsa_nodal_model_hierarchical.yaml")
model.export_hdf5("output/PYPSA/nodal/cesdm/profiles/profiles.h5", values_map=profiles_values)
```

Run that with `tools/` on `PYTHONPATH` (the example script does this for you).

---

## 3. After the conversion

Whether you downloaded the packages or ran the importers, each study is the same three CESDM artefacts:

| Artefact | What it is |
|----------|------------|
| **YAML** | Hierarchical and flat model files for review and re-import |
| **Frictionless** | `datapackage.json` plus one CSV per entity class |
| **HDF5 profiles** | Hourly series next to the YAML (`profiles.h5`) |

### Explore a converted TYNDP or PyPSA model

`tools/explore_cesdm_model.py` loads a hierarchical YAML and prints capacity by country, generation mix, storage, demand and network counts. Schema default is `schemas/cesdm`.

To open the same families as an interactive dashboard (capacity, demand, storage, available energy, cross-border limits — in the style of the Sensitivities Scenario Assumptions tab):

```bash
cesdm-assumptions-dashboard --serve
```

That opens a page with a **Load YAML** button. Optional: pass `--yaml path/to/model.yaml` to start with a model already loaded. To write a standalone HTML file instead:

```bash
cesdm-assumptions-dashboard \
  --yaml converted_data/TYNDP2024/SC_NT_SY_2030_WY_2009/cesdm/yaml/tyndp_nt_2030_2009_hierarchical.yaml \
  --open
```

Equivalent: `python tools/cesdm_assumptions_dashboard.py --serve` or `--yaml …`. The standalone HTML is written next to the YAML as `*_assumptions.html`. Load YAML needs `--serve`, because the CESDM schemas are applied in Python.

After option 1:

```bash
python tools/explore_cesdm_model.py \
  --yaml converted_data/TYNDP2024/SC_NT_SY_2030_WY_2009/cesdm/yaml/tyndp_nt_2030_2009_hierarchical.yaml

cesdm-assumptions-dashboard \
  --yaml converted_data/TYNDP2024/SC_NT_SY_2030_WY_2009/cesdm/yaml/tyndp_nt_2030_2009_hierarchical.yaml \
  --open
```

After option 2:

```bash
python tools/explore_cesdm_model.py \
  --yaml output/TYNDP2024/SC_NT_SY_2030_WY_2009/cesdm/yaml/tyndp_nt_2030_2009_hierarchical.yaml

python tools/explore_cesdm_model.py \
  --yaml output/PYPSA/nodal/cesdm/yaml/pypsa_nodal_model_hierarchical.yaml
```

| Next | Page |
|------|------|
| Check that the description is consistent | [Validate models](../use/validate-models.md) |
| Understand YAML vs HDF5 | [Import and export](../use/import-export.md), [Profiles](../understand/profiles.md) |
| Aggregate a nodal model with location information to different geographical scales, such as NUTS 1, NUTS 2, NUTS 3 or country level. | [Spatial aggregation](../use/spatial-aggregation.md) |

The converters translate planning or network data into a CESDM representation. They do not replace the TYNDP process or a PyPSA solve.

Internal field-level notes (not required to run the steps above) are in `examples/README_TYNDP_IMPORT_LOGIC.md` and `examples/README_PYPSA_IMPORT_LOGIC.md`.
