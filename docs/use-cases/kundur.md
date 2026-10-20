# Kundur's two-area system

The Swiss system in [Part 2 of the tutorial](../tutorial/analyses/index.md) is stylised: one winter evening on six 380 kV corridors, not a published network. Nobody outside this documentation can tell you whether its power flow is right. Kundur's four-machine, two-area system is the opposite: a published textbook network for the same two layers, power flow and dynamics, with results anyone can look up.

Use it as a benchmark. If your adapter writes this system to your tool and the tool reproduces the book's flows, the adapter carries a network correctly. The same holds for a solver you connect to CESDM.

The numbers are Example 12.6 of P. Kundur, *Power System Stability and Control*, McGraw-Hill, 1994, Chapter 12, on a 100 MVA, 230 kV base.

| Element | Value |
|---|---|
| Lines | r = 0.0001 pu/km, x = 0.001 pu/km, b = 0.00175 pu/km |
| Corridors 7–8 and 8–9 | 110 km, two circuits each; one circuit is r = 0.011 pu, x = 0.11 pu, b = 0.1925 pu |
| Capacitors | 200 MVAr at bus 7, 350 MVAr at bus 9 |
| Step-up transformers | 15 % on their 900 MVA rating, which is 0.0167 pu on 100 MVA |
| Machines | G1 and G2 share a machine type with H = 6.5 s; G3 and G4 share another with H = 6.175 s; the reactances are the same for both types |
| Controllers | each machine has a SEXS exciter, an IEEEG1 governor and a STAB1 stabiliser |

The model loads `cesdm/schemas/powerflow` and `cesdm/schemas/dynamics`. `validate_for_analysis("dynamics")` is clean because those values were set.

```bash
python examples/example_kundur_two_area.py
```

## Compare with the book

Bus 1 is the angle reference. The solved tie flow out of area 1 is 400.4 MW, about 200 MW on each circuit from bus 7 to bus 8. Generator powers match the book: G1 is 700.1 MW and 185.1 MVAr, G2 is 700 MW and 234.7 MVAr, G3 is 719 MW and 176.0 MVAr, G4 is 700 MW and 202.1 MVAr.

```text
bus        |V| [pu]  angle [deg]
bus.1        1.0300         0.00
bus.2        1.0100        -9.77
bus.3        1.0300       -27.08
bus.4        1.0100       -37.27
bus.5        1.0064        -6.46
bus.6        0.9781       -16.55
bus.7        0.9610       -24.96
bus.8        0.9486       -38.83
bus.9        0.9714       -52.43
bus.10       0.9835       -44.02
bus.11       1.0083       -33.71

line.l3a  bus.7→bus.8   200.2 MW
line.l3b  bus.7→bus.8   200.2 MW
line.l4a  bus.8→bus.9   195.4 MW
line.l4b  bus.8→bus.9   195.4 MW
```

The book gives angles relative to its own reference, so compare angle differences, not the angles themselves.

The script is `examples/example_kundur_two_area.py`. A walk through one generator, its machine type and its three controllers is in `examples/README_KUNDUR_TWO_AREA_EXAMPLE.md`. [The dynamics layer](../tutorial/analyses/4-dynamics.md) uses the same classes on the Swiss system.
