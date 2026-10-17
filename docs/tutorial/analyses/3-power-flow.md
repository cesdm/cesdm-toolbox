# 3. The power-flow layer

A power flow is one operating point on a network. This step reads `output/swiss-analyses/dispatch.yaml` — the plants, the basins and the hourly year — with `schemas/cesdm_power_flow`, and appends the evening and the network. The power-flow profile on that file still reports 14 gaps: no bus, no setpoint, no demand in megawatts. Both hydro turbines are among them, because they are generators. The basins are not. The result is `output/swiss-analyses/power_flow.yaml`.

```bash
python docs/examples/swiss-analyses/step3_power_flow.py
```

The same plants and the same demand stay. What is added is where the machines are connected, and what they do in one hour. The basins stay unconnected: a power flow has a setpoint on the turbine, not on the water.

Opening `power_flow.yaml` with only `schemas/cesdm` drops the impedance, the setpoints and the power-flow result classes. The import warns, and lists each dropped field. `strict_unknown=True` raises instead. `validate_for_analysis("power_flow")` on that base model says to load `schemas/cesdm_power_flow`, rather than reporting each missing attribute as if the plant were incomplete.

```python
from cesdm.helpers import build_model_from_yaml

base = build_model_from_yaml("schemas/cesdm")
base.import_yaml("output/swiss-analyses/power_flow.yaml")
base.validate_for_analysis("power_flow")
# ['[power_flow] load schemas/cesdm_power_flow before this check. ...']
```

## One hour, not the year

The hour is 15 January at 19:00, taken from the dispatch series. Must-run wind, PV and run-of-river inflow come first, then nuclear up to its capacity (variable cost 9 MU/MWh), then the reservoir turbine, then gas (45 MU/MWh). Gas stays off. The six setpoints add up to the demand.

| Plant | Setpoint | Of a capacity of |
|---|---|---|
| `gen.CH_NUC` | 3000 MW | 3000 MW |
| `gen.CH_HYD_RES` | 6822 MW | 8500 MW |
| `gen.CH_HYD_ROR` | 1113 MW | 4000 MW |
| `gen.CH_GAS` | 0 MW | 400 MW |
| `gen.CH_WIND` | 30 MW | 100 MW |
| `gen.CH_PV` | 0 MW | 6500 MW |
| `demand.CH` | 10965 MW, power factor 0.98 | 58 TWh/year |

Each plant also gets `atNode`. The demand gets `active_power_demand` and `reactive_power_demand`. That is the whole of what the profile asked for on the assets that already existed. Buses and lines are new objects, so they show up as gaps only once they exist.

## Six buses, six corridors

The network is 380 kV and stylised. It is not the Swiss transmission grid. The plants are fleet totals, and one 380 kV circuit carries about 2000 MVA, so each branch is an equivalent corridor: resistance and reactance of one overhead circuit (0.028 Ω/km, 0.260 Ω/km), divided by the number of circuits, charging susceptance and thermal rating multiplied by it.

| Bus | Holds | Type |
|---|---|---|
| `bus.ch_alpine` | reservoir turbine, voltage 1.01 pu | slack |
| `bus.ch_ror` | run-of-river, voltage 1.01 pu | PV |
| `bus.ch_nuclear` | nuclear unit, voltage 1.02 pu | PV |
| `bus.ch_gas` | gas turbine, voltage 1.01 pu | PV |
| `bus.ch_plateau` | wind and PV, voltage 1.00 pu | PV |
| `bus.ch_load` | the demand | PQ |

| Corridor | Path | Length | Circuits |
|---|---|---|---|
| `line.alpine_load` | alpine → load | 100 km | 8 |
| `line.ror_alpine` | run-of-river → alpine | 15 km | 3 |
| `line.nuclear_load` | nuclear → load | 120 km | 3 |
| `line.gas_nuclear` | gas → nuclear | 20 km | 1 |
| `line.plateau_load` | plateau → load | 140 km | 4 |
| `line.nuclear_alpine` | nuclear → alpine | 160 km | 2 |

The alpine corridor carries the reservoir, 8.5 GW. Eight circuits (16000 MVA) leave the load at 0.95 pu or above; seven leave it at 0.946 pu. The short run-of-river tie is sized for 4.0 GW. The plateau corridor is sized for the wind and PV fleet, 6.6 GW, not for the 30 MW this evening actually sends.

The alpine bus is the slack. The reservoir setpoint is 6822 MW of 8500 MW, so the losses sit where there is still headroom, which is also where Swiss storage hydro balances the system. The export builds one `ext_grid` per generator on a slack bus, so the run-of-river unit stays on its own PV bus and only the reservoir is the angular reference. Nuclear keeps its 3000 MW setpoint on a PV bus.

```text
After the network
    0 gaps
Schema check: 0 errors
Wrote output/swiss-analyses/power_flow.yaml
```

## What the solver does with it

With pandapower installed, the script exports the model and runs an AC power flow. The reservoir keeps 6822 MW. The slack covers 251 MW of losses, so the alpine bus injects 7073 MW, still inside the 8500 MW turbine. The load sits at 0.954 pu.

```text
pandapower AC power flow converged
    bus.ch_alpine     1.010 pu     0.00 deg
    bus.ch_gas        1.010 pu     1.05 deg
    bus.ch_load       0.954 pu   -10.85 deg
    bus.ch_nuclear    1.020 pu     0.99 deg
    bus.ch_plateau    1.000 pu   -11.03 deg
    bus.ch_ror        1.010 pu     0.57 deg
    reservoir keeps its setpoint 6822 MW; slack gen.CH_HYD_RES covers 251.0 MW of losses
```

Without pandapower the CESDM data is still complete: `validate_for_analysis("power_flow")` is empty either way.

**Next:** [4. The dynamics layer](4-dynamics.md).
