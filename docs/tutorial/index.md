# Tutorial: Data exchange between four groups

Here we come back to our [introductory example](../index.md): four independent research groups study the same energy system with the same kind of analysis: an annual economic dispatch of Switzerland. Each group has developed its own model, its own toolchain and its own way of storing the system. They now want to exchange their system descriptions — to check each other's inputs, to reuse data, to compare results on a common basis. The files for this tutorial are located in `docs/examples/four-research-groups/`. The whole exchange is `run_exchange.py` (see [Get started](../get-started.md)). The same steps, with a short explanation of each one, are in `notebooks/run_exchange.ipynb`.

![Four research groups store the same reservoir in four ways and exchange it through CESDM](../illustrations/four-groups-exchange.svg)

## The system

The system under study is a simplified picture of the current electricity supply situation in Switzerland, defined by the annual demand and the installed capacities of generation technologies, as well as the storage capacity and inflow when relevant:

| | |
|---|---|
| Annual electricity demand | 58 TWh |
| Nuclear | 3.0 GW |
| Reservoir hydro | 8.5 GW, 8.8 TWh storage, 20 TWh/year inflow |
| Run-of-river hydro | 4.0 GW, 16 TWh/year inflow |
| Photovoltaics | 6.5 GW |
| Wind | 0.1 GW |
| Gas (CCGT) | 0.4 GW |

For simplicity within the context of this tutorial, we assume that the data used is consistent and in agreement between the four groups.

## Four representations

As every group has developed their model independently, the way they store their data varies considerably, as can be seen below:

=== "Group A: CSV"

    Data is stored as semicolon-separated CSV tables with German headers. Technologies are referred to using numeric codes; annual demand is given in GWh. Hydro storage and inflow is stored in a separate table.

    ```text
    plants.csv                              storage.csv
    ID;Region;Pmax;Typ;Eta;VarKosten        ID;Region;E_speicher;Zufluss
    CH_GAS;CH;400;1;58;45                   CH_RES;CH;8800000;20000000
    CH_NUC;CH;3000;2;33;9                   CH_ROR;CH;0;16000000
    CH_WIND;CH;100;3;;0
    CH_PV;CH;6500;4;;0                      load.csv
    CH_HYD_RES;CH;8500;6;90;0               Region;E_Jahr
    CH_HYD_ROR;CH;4000;7;90;0               CH;58000
    ```

=== "Group B: Excel"

    Data is stored as a workbook in a PyPSA-like style, with separate sheets for generators, storage and demand. Technologies are named by fuel (`carrier`); energy is in GWh.

    | Sheet | Columns | Example row |
    |---|---|---|
    | Generators | `unit_id, region_id, p_nom, carrier, efficiency, marginal_cost` | `CH_HYDRO, CH, 8500, hydro, 0.9, 0` |
    | Storage | `store_id, region_id, energy_gwh, inflow_gwh` | `CH_RES, CH, 8800, 20000` |
    | Demand | `region_id, demand_gwh` | `CH, 58000` |

=== "Group C: YAML"

    Data is stored in a single YAML file, nested by region, with capacities given in GW and TWh. The hydro reservoir is represented as part of the plant itself. The region is `CHE`, not `CH`.

    ```yaml
    regions:
      CHE:
        demand_twh: 58
        plants:
          - {id: nuc, tech: nuclear, cap_gw: 3.0, eta: 0.33, var_cost: 9}
          - {id: hydro, tech: reservoir_hydro, cap_gw: 8.5,
             reservoir_id: CHE_RES, reservoir_twh: 8.8, inflow_twh: 20,
             eta: 0.9, var_cost: 0}
          - {id: ror, tech: run_of_river, cap_gw: 4.0, inflow_twh: 16,
             eta: 0.9, var_cost: 0}
    ```

=== "Group D: JSON"

    Data is represented as flat lists, with capacities given in kW and energy in MWh.

    ```json
    {"id": "che-hydro", "region": "CHE", "technology": "reservoir_hydro",
     "capacity_kw": 8500000, "efficiency_pc": 90,
     "variable_cost_eur_per_kwh": 0, "reservoir_id": "CHE_RES",
     "reservoir_mwh": 8800000, "inflow_mwh": 20000000}
    ```

We can summarise the most important differences between the system representations:

| | A | B | C | D |
|---|---|---|---|---|
| Format | CSV | Excel | YAML | JSON |
| Technology | code `6` | fuel `hydro` | `reservoir_hydro` | `reservoir_hydro` |
| Capacity unit | MW | MW | GW | kW |
| Energy unit | GWh, MWh | GWh | TWh | MWh |
| Region | `CH` | `CH` | `CHE` | `CHE` |
| Where the reservoir is | own table, linked by convention | own sheet, linked by convention | on the plant | on the plant |
| Plant identifiers | `CH_HYD_RES` | `CH_HYDRO` | `hydro` | `che-hydro` |

Some of these differences are simple matters of convention, such as names and units. Others are structural (for example where and how the reservoir is defined) or rely on implicit knowledge (such as that Group A's `Typ = 6` denotes reservoir hydro, that Group B's `gas` specifically means a combined-cycle plant, or that Group A's storage row with `E_speicher > 0` belongs to the `Typ 6` plant). This knowledge is internal to each group, rarely formalized and is typically lost when data files are sent in their raw format.

## The exchange process

To use Group A's data, Group C has to learn A's columns, codes, units and conventions, and write a converter or do a large amount of tedious manual curation work. To use Group D's, this same process has to be repeated. Four groups that all exchange in both directions need to develop six two-way converters, each maintained by someone who does not necessarily have a good grasp of the source data and may not stay in the group indefinitely.

In the next steps of this tutorial, we show how each group needs only write one two-way adapter between its own representation and CESDM, requiring knowledge of only their own conventions and format, and CESDM.

- [1. Writing adapters](1-map.md): Group A writes its adapter, and one conversion is shown both ways: A's rows into CESDM, and those objects back into A's CSV.
- [2. Validation of CESDM files](2-check.md): Every group checks that its file is correct CESDM before sending it and then that their four files describe the same system
- [3. Exchanging with other groups](3-exchange.md): A's system arrives at C and back, and every group exchanges with every other.
