# Use TYNDP and PyPSA data

The toolbox converts two widely used European datasets into CESDM: the **ENTSO-E TYNDP 2024** scenarios and a **PyPSA nodal network** (`elec.nc`). For exchange between groups this is a shared starting point: if two groups begin from the same CESDM version of a TYNDP scenario, their models agree on assets, names and units from day one.

## Option 1: download the converted models

Download [cesdm_converted_data.zip](https://ethz.ch/content/dam/ethz/special-interest/mavt/ctr-energy-networks-fen-dam/data/cesdm_converted_data.zip) and unpack it as `converted_data/`. It holds the TYNDP 2024 scenarios — National Trends 2030 and 2040, Distributed Energy and Global Ambition 2030, 2040 and 2050, weather year 2009 — and the PyPSA nodal example. Each one is a YAML file, a Frictionless package and `profiles.h5`.

## Option 2: convert yourself

```bash
pip install -e ".[pypsa,geo]"
python -m tools.download_external_data   # fetches the raw TYNDP CSVs and elec.nc into external_data/
```

TYNDP scenarios are zonal dispatch models and load `schemas/cesdm`. The PyPSA network is nodal and loads `schemas/cesdm_power_flow`, because buses and lines carry power-flow fields.

=== "TYNDP 2024"

    One scenario is a combination of policy, scenario year and weather year:

    ```python
    import sys; sys.path.insert(0, "examples")
    from example_import_tyndp import build_cesdm_model_from_tyndp_installed_capacities

    build_cesdm_model_from_tyndp_installed_capacities(
        schema_path="schemas/cesdm",
        data_folder="external_data/TYNDP2024/",     # must end with /
        output_folder="output/TYNDP2024/",
        policy="NT", year=2030, climate_year=2009,
        drop_zero=True,
    )
    ```

    `python examples/example_import_tyndp.py` converts the whole default set; that takes a while.

=== "PyPSA elec.nc"

    ```bash
    python examples/example_import_pypsa.py \
      --nc-path external_data/PYPSA/elec.nc \
      --schema-dir schemas/cesdm_power_flow \
      --nuts-shapefile external_data/PYPSA/NUTS_RG_20M_2021_4326.shp \
      --output-dir output/PYPSA/nodal/
    ```

    Leave out `--nuts-shapefile` if you do not need sub-national regions. Any other PyPSA `.nc` works the same way.

Results land in `output/<dataset>/…/cesdm/` with `yaml/`, `profiles/` and `frictionless/`.

## Look at a converted model

```bash
python tools/explore_cesdm_model.py --yaml <path>/….yaml                  # summary in the terminal
```

## Reduce it to the scale you need

A nodal European model is too large for many studies. `tools/aggregate_cesdm_model.py` merges buses to countries or NUTS regions, and the output is again a valid CESDM model:

```bash
python tools/aggregate_cesdm_model.py \
    --schemas schemas/cesdm_power_flow --yaml model.yaml --h5 profiles.h5 --outdir results \
    --level country --level-by-country CH=nuts3 \
    --keep CH DE FR IT AT
```

This keeps Switzerland at NUTS 3 and its neighbours at country level. The file is a nodal network, so the schema is `schemas/cesdm_power_flow`. A dispatch-only file uses `schemas/cesdm`. The tool also loads every package named in the file when that package sits next to `--schemas`, so a PyPSA file that records `cesdm_power_flow` keeps the transformer voltages. Other options: `--split-voltage` to keep voltage levels apart, `--tech-group 'Generation.Thermal.Gas.*'` to merge technologies, `--no-profiles` for structure only.

Aggregation is a model reduction: congestion inside a merged region disappears and branch parameters are kept, not re-estimated.

!!! note
    The converters translate data into CESDM. They do not reproduce the TYNDP process or a PyPSA optimisation.
