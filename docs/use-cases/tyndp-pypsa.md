# Use TYNDP and PyPSA data

The toolbox converts two widely used European datasets into CESDM: the **ENTSO-E TYNDP 2024** scenarios and a **PyPSA nodal network** (`elec.nc`). For exchange between groups this is a shared starting point: if two groups begin from the same CESDM version of a TYNDP scenario, their models agree on assets, names and units from day one. Read this page if your study needs a real European system rather than the tutorial's stylised Swiss one, or if you want to compare your results with another group on the same scenario.

## Option 1: download the converted models

```bash
python -m tools.download_converted_data
```

That fetches [cesdm_converted_data.zip](https://ethz.ch/content/dam/ethz/special-interest/mavt/ctr-energy-networks-fen-dam/data/cesdm_converted_data.zip) and unpacks it as `converted_data/`. It holds the TYNDP 2024 scenarios — National Trends 2030 and 2040, Distributed Energy and Global Ambition 2030, 2040 and 2050, weather year 2009 — and the PyPSA nodal example. Each one is a YAML file, a Frictionless package and `profiles.h5`. On a network that intercepts HTTPS, add `--insecure` only if you trust the network.

## Option 2: convert yourself

```bash
pip install -e ".[pypsa,geo]"
python -m tools.download_external_data   # fetches the raw TYNDP CSVs and elec.nc into external_data/
```

TYNDP scenarios are zonal dispatch models and load `cesdm/schemas/base`. The PyPSA network is nodal and loads `cesdm/schemas/powerflow`, because buses and lines carry power-flow fields.

=== "TYNDP 2024"

    One scenario is a combination of policy, scenario year and weather year:

    ```python
    import sys; sys.path.insert(0, "examples")
    from example_import_tyndp import build_cesdm_model_from_tyndp_installed_capacities

    build_cesdm_model_from_tyndp_installed_capacities(
        schema_path="cesdm/schemas/base",
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
      --schema-dir cesdm/schemas/powerflow \
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
    --schemas cesdm/schemas/powerflow --yaml model.yaml --h5 profiles.h5 --outdir results \
    --level country --level-by-country CH=nuts3 \
    --keep CH DE FR IT AT
```

This keeps Switzerland at NUTS 3 and its neighbours at country level. The file is a nodal network, so the schema is `cesdm/schemas/powerflow`. A dispatch-only file uses `cesdm/schemas/base`. The tool also loads every package named in the file when a sibling folder's manifest carries that name, so a PyPSA file that records `cesdm-powerflow` keeps the transformer voltages. Other options: `--split-voltage` to keep voltage levels apart, `--tech-group 'Generation.Thermal.Gas.*'` to merge technologies, `--no-profiles` for structure only.

Aggregation is a model reduction: congestion inside a merged region disappears and branch parameters are kept, not re-estimated.

!!! note
    The import scripts translate data into CESDM. They do not reproduce the TYNDP process or a PyPSA optimisation.

## Source data and how to cite

Cite the original sources as well as [CESDM](../project/contribute.md#cite) when you publish from these files.

**TYNDP 2024.** The complete package is on the [ENTSOs TYNDP 2024 Scenarios download page](https://2024.entsos-tyndp-scenarios.eu/download/). Attribute it as **TYNDP 2024 Scenarios** (ENTSO-E and ENTSOG). The citable Zenodo record is [10.5281/zenodo.16759671](https://doi.org/10.5281/zenodo.16759671) (concept DOI; this version is [10.5281/zenodo.16759672](https://doi.org/10.5281/zenodo.16759672)). That Zenodo deposit currently mirrors the line and node tables; the full input set remains on the ENTSOs page.

**PyPSA.** Cite the software paper, and a Zenodo DOI if you need a specific release. The project's own wording is on [Citing PyPSA](https://docs.pypsa.org/latest/home/citing/).

Brown, T., Hörsch, J. and Schlachtberger, D. (2018). PyPSA: Python for Power System Analysis. *Journal of Open Research Software*, 6(1), 4. [doi:10.5334/jors.188](https://doi.org/10.5334/jors.188)

Releases are archived on Zenodo under the concept DOI [10.5281/zenodo.3946412](https://doi.org/10.5281/zenodo.3946412). Use a version DOI from that record when the exact PyPSA release matters.

```bibtex
@article{PyPSA,
  author  = {T. Brown and J. H\"orsch and D. Schlachtberger},
  title   = {{PyPSA: Python for Power System Analysis}},
  journal = {Journal of Open Research Software},
  volume  = {6},
  issue   = {1},
  number  = {4},
  year    = {2018},
  eprint  = {1707.09913},
  url     = {https://doi.org/10.5334/jors.188},
  doi     = {10.5334/jors.188}
}
```
