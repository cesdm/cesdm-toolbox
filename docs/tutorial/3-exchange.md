# 3. Exchanging with other groups

The conversion of Group A's own files, into CESDM and back into CSV, is the [worked example](1-map.md) in the mapping step. Here the receiver is another group.

## Group C receives Group A's system

Group C does not need to know anything about Group A's CSV files, codes or units. It loads Group A's CESDM file and writes it in its own representation with its own adapter:

```python
model = load("group_a.yaml")                      # Group A's CESDM file
adapter_c.from_cesdm(model, Path("received-by-c/system.yaml"))
```

`from_cesdm` reads the CESDM side — the same for every sender — and writes Group C's format: GW, TWh, `CHE`, the reservoir nested on the plant.

```text
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
```

**The system information comes from the sender; the representation comes from the receiver.** Group A's `Typ = 6`, its separate storage table and its GWh are gone; the meaning and the numbers are not.

## And back: Group A receives Group C's system

The same, in the other direction. Group A's adapter writes its CSV files and restores its own convention — reservoir and inflow back in `storage.csv`, technologies back to codes:

```text
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
```

The identifiers are Group C's — `nuc`, `hydro`, `CHE_RES` — because identifiers belong to the sender's data. Group C has no identifier for the run-of-river inflow at all, so its adapter made one up (`ror_inflow`). Codes, units and structure are Group A's.

## Round trip

A useful test for any adapter pair: send the system from A to C and back, then compare with the original.

```text
5 · Round trip A → C → A
    0 differences
```

## Every group with every other group

The example runs all twelve directed exchanges — A→B, A→C, …, D→C — and compares what arrived with what was sent:

```text
6 · Every group to every other group
    12 of 12 exchanges preserve the system
```

Twelve exchanges, four adapters. No group has read another group's format.

## A fifth group

A fifth group joins with its own representation. It writes one adapter — `to_cesdm`, `from_cesdm`, its own code tables — validates its files against the same schema, and can exchange with A, B, C and D from the first day. Nothing changes for the other four.

## Next

- [Part 2: one system, several analyses](analyses/index.md)
- [Write the adapter for your own representation](../guides/write-an-adapter.md)
- [How the data model works](../concepts/energy-model.md)
