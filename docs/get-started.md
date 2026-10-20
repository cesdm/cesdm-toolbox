# Get started

Install the toolbox and run the example. You need Python 3.11 or newer and Git.

## Install

=== "Linux / macOS"

    ```bash
    git clone https://github.com/cesdm/cesdm-toolbox.git
    cd cesdm-toolbox
    python -m venv .venv && source .venv/bin/activate
    pip install -e .
    ```

=== "Windows"

    ```powershell
    git clone https://github.com/cesdm/cesdm-toolbox.git
    cd cesdm-toolbox
    python -m venv .venv; .venv\Scripts\activate
    pip install -e .
    ```

Optional extras: `jupyter`, `data`, `excel`, `pypsa`, `tyndp`, `pandapower`, `geo`, `docs`, `dev`, `all`. 

## Run the example

From the repository root:

```bash
python docs/examples/four-research-groups/run_exchange.py
```

The same steps, with a short explanation of each one, are in `notebooks/run_exchange.ipynb`. That notebook needs the `jupyter` extra, and Jupyter has to be the one from this environment. A `jupyter` command from another installation (for example Homebrew) uses a different environment and will not see the package:

```bash
pip install -e ".[jupyter]"
python -m jupyter lab notebooks/run_exchange.ipynb
```

You should see:

```text
1 · Each group writes its system as CESDM
    Group A  group-a-csv                  → group_a.yaml   ✓ valid CESDM
    Group B  switzerland_dispatch.xlsx    → group_b.yaml   ✓ valid CESDM
    Group C  system.yaml                  → group_c.yaml   ✓ valid CESDM
    Group D  network.json                 → group_d.yaml   ✓ valid CESDM
2 · Do the four groups describe the same system?
    A vs B: 0 differences
    A vs C: 0 differences
    A vs D: 0 differences
3 · Group C receives Group A's system
    wrote output/four-research-groups/received-by-c/system.yaml
          demand_twh: 58
          - id: CH_HYD_RES
            tech: reservoir_hydro
            cap_gw: 8.5
            var_cost: 0
            eta: 0.9
            reservoir_id: CH_RES
            reservoir_twh: 8.8
            inflow_twh: 20
4 · Group A receives Group C's system
    wrote output/four-research-groups/received-by-a/csv/
      plants.csv
        ID;Region;Pmax;Typ;Eta;VarKosten
        ccgt;CH;400;1;58;45
        nuc;CH;3000;2;33;9
        wind;CH;100;3;;0
        pv;CH;6500;4;;0
        hydro;CH;8500;6;90;0
        ror;CH;4000;7;90;0
      storage.csv
        ID;Region;E_speicher;Zufluss
        CHE_RES;CH;8800000;20000000
        ror_inflow;CH;0;16000000
5 · Round trip A → C → A
    0 differences
6 · Every group to every other group
    12 of 12 exchanges preserve the system
```

Each group's CESDM file and what every group received are in `output/four-research-groups/`. Open them — they are plain YAML, CSV, Excel and JSON.

To see what the validation catches, run `python docs/examples/four-research-groups/mistakes.py`.

**Next:** [what happened in each step](tutorial/index.md).

??? note "Troubleshooting"
    **`ModuleNotFoundError`** — activate the virtual environment and run `pip install -e .` from the repository root.

    **`pandapower is required`** — install the extra: `pip install -e ".[pandapower]"`.

    **pandapower prints a numba warning** — harmless; install `numba` for speed if you like.
