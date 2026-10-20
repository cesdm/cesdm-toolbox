# 4. The dynamics layer

A dynamic simulation needs a machine model and the controllers on it. This step reads `output/swiss-analyses/power_flow.yaml` with `cesdm/schemas/powerflow` and `cesdm/schemas/dynamics`, and appends those objects. The dispatch year and the network stay. The result is `output/swiss-analyses/dynamics.yaml`. In CESDM the machine is not an extra column on the plant. It is another object, and the plant points at it.

```bash
python docs/examples/swiss-analyses/step4_dynamics.py
```

## What hangs off the plant

| Link on the plant | Points at | What is stored there |
|---|---|---|
| `usesDynamicModelType` | `DynamicMachineModelType.Synchronous` | inertia, reactances, time constants, model order |
| `hasAutomaticVoltageRegulator` | one `Controller.AVR.*` | the exciter |
| `hasTurbineGovernor` | one `Controller.GOV.*` | the governor |
| `hasPowerSystemStabilizer` | one `Controller.PSS.*` | the stabiliser, when the study uses one |

The controller points back with `controlsGenerationUnit`.

Two quantities stay on the plant: `rated_apparent_power` (MVA) and `rated_voltage` (kV). The machine type is in per-unit on that base, so the same type can be shared by identical machines and read on each unit's own rating. In the Kundur system, G1 and G2 share one type and G3 and G4 share another, because only the inertia differs. A nuclear unit and a hydro unit do not share a type.

The class of the controller is the choice of model. A plant has at most one exciter, but `Controller.AVR.SEXS`, `.IEEET1`, `.AC1A` and `.ST1A` do not share a parameter list, so they are not fields of `GenerationUnit`. Governors work the same way: `Controller.GOV.IEEEG1` for a steam unit, `.HYGOV` for hydro, `.GGOV1` for a gas turbine.

Wind and PV have no synchronous machine. The parameters live on `DynamicMachineModelType.Synchronous`, not on `GenerationUnit`, so a `WindGenerationUnit` or `SolarGenerationUnit` does not carry them.

## The shipped profile only sees objects that exist

On the Swiss system from Part 1 the dynamics profile reports 0 gaps. There is no machine type and no controller, and the profile does not require a plant to have either.

```text
Shipped dynamics profile, before any machine model
    0 gaps
```

Once a machine type exists, the profile checks that object. Linking an empty type to the nuclear unit (`gen.CH_NUC`) does not produce the ten gaps the [requirements table](index.md) suggests:

```text
Link an empty machine type to the nuclear unit
    inertia_constant stored=None  effective=5.0  (schema default)
Shipped dynamics profile, empty machine type
    1 gaps
      DynamicMachineModelType.Synchronous        machine_model_order                              ×1
```

`inertia_constant` was never set. The check still accepts it, because the schema default (5 s) counts as a value, and the same is true of the reactances and time constants. `machine_model_order` has no default, so it is the one machine attribute the profile actually asks you to choose (`classical`, `two_axis`, `subtransient_4th`, `subtransient_6th`, `subtransient_8th`). Setting only that attribute clears the profile. The rated base on the plant is not in the profile at all.

An empty `Controller.AVR.SEXS` is the same story: every parameter the profile lists for it has a default, so the check reports nothing. An empty governor fails on `GOV_Pmax` only, because that limit has no default. The profile will not complain that a stabiliser is missing.

## One subtransient model, three constructions

For a study that cares about the first cycles after a fault, the machine order is `subtransient_6th`. That model uses the subtransient reactances `Xd''` and `Xq''` and their time constants, which `classical` and `two_axis` do not. `subtransient_8th` adds still more damper states; this system does not need them.

The electrical parameters follow the construction, not the plant name. A round-rotor machine (steam, gas turbine) has `Xd` close to `Xq`. A salient-pole hydro machine has `Xq` clearly below `Xd`, and no field winding on the q axis, so `Xq'` stays near `Xq`. Inertia rises from hydro to a gas turbine to a large steam unit. The schema default `Xd = 1.8` already sits in the round-rotor band cited from IEEE Std 1110 (about 1.0–2.0 pu). These figures are typical for the class. They are not nameplate data, and the Swiss plants in Part 1 are fleet totals, so the rated base on each unit is its MW capacity divided by a power factor of 0.9.

| Plant | Construction | H [s] | Xd | Xq | Governor |
|---|---|---|---|---|---|
| `gen.CH_NUC` | round-rotor steam | 6.5 | 1.80 | 1.70 | `IEEEG1` |
| `gen.CH_GAS` | round-rotor gas | 4.5 | 1.60 | 1.50 | `GGOV1` |
| `gen.CH_HYD_RES` | salient-pole hydro | 3.0 | 1.00 | 0.65 | `HYGOV`, water starting time 0.5 s |
| `gen.CH_HYD_ROR` | salient-pole hydro | 3.0 | 1.00 | 0.65 | `HYGOV`, water starting time 0.5 s |

Both hydro turbines are salient-pole machines. They share the type and each has its own governor. Wind and PV stay without a synchronous model. Every synchronous unit uses the same simplified SEXS exciter; the type dependence is in the machine and the governor.

```text
    plant            construction            H [s]     Xd     Xq  governor
    gen.CH_NUC       round-rotor steam         6.5   1.80   1.70  IEEEG1
    gen.CH_GAS       round-rotor gas           4.5   1.60   1.50  GGOV1
    gen.CH_HYD_RES   salient-pole hydro        3.0   1.00   0.65  HYGOV  Tw=0.5 s
    gen.CH_HYD_ROR   salient-pole hydro        3.0   1.00   0.65  HYGOV  Tw=0.5 s
    model order: subtransient_6th
No synchronous model: gen.CH_WIND, gen.CH_PV
```

## Ask for the link yourself

The hole is the missing link, not the parameter list. A group closes it with its own profile, the same way the four groups wrote `annual_dispatch.yaml`. For this system the two hydro turbines are the machines that form their own class:

```yaml
- entity_class: HydroGenerationUnit
  checks:
    - {attribute: usesDynamicModelType, required: true}
    - {attribute: rated_apparent_power, required: true}
    - {attribute: rated_voltage, required: true}
```

```text
A profile that requires a machine model on every hydro unit
    6 gaps
      HydroGenerationUnit                        rated_apparent_power                             ×2
      HydroGenerationUnit                        rated_voltage                                    ×2
      HydroGenerationUnit                        usesDynamicModelType                             ×2
```

That profile is `synchronous_hydro.yaml`. After the class-typical machine is attached it reports 0 gaps, because both hydro turbines point at the salient-pole type and each carries a rated base.

The same requirement does not belong on `GenerationUnit`. Wind and PV are subclasses of it, so they would be told to carry a synchronous machine. The gas and nuclear units of this system are plain `GenerationUnit` as well, so a hydro-only profile does not see them. A profile can require the link on `ThermalGenerationUnit` and `HydroGenerationUnit` once those classes are what the adapter writes.

## Where the numbers are checkable

[Kundur's two-area system](../../use-cases/kundur.md) is the benchmark: G1 and G2 share one `DynamicMachineModelType.Synchronous` (H = 6.5 s), G3 and G4 share another (H = 6.175 s), and each machine has a SEXS exciter, an IEEEG1 governor and a STAB1 stabiliser. `validate_for_analysis("dynamics")` is clean because those values were set, not because a default happened to match.

```bash
python examples/example_kundur_two_area.py
```

Reactances there are per-unit on the machine base, `Z_base = Vn² / Sn`. The network those machines would sit on is the [power-flow layer](3-power-flow.md): one winter evening, six 380 kV buses, the same plants.
