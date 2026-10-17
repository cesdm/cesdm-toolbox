# 2. The dispatch layer

This step reads `output/swiss-analyses/system.yaml` and asks both dispatch questions. The annual one already passes. The hourly one does not, until the hours are appended and written to `output/swiss-analyses/dispatch.yaml`.

```bash
python docs/examples/swiss-analyses/step2_dispatch.py
```

## The annual balance

The four groups wrote what their analysis needs as `annual_dispatch.yaml`:

```yaml
name: annual_dispatch
requirements:
  - entity_class: GenerationUnit            # covers Wind-, Solar- and HydroGenerationUnit
    checks:
      - attribute: hasTechnology
        required: true
        when: "not generator_technology_type"
      - attribute: generator_technology_type
        required: true
        when: "not hasTechnology"
      - {attribute: belongsToGeographicalRegion, required: true}
      - {attribute: nominal_power_capacity, required: true, constraints: {minimum: 0}}
  - entity_class: HydroGenerationUnit
    checks:
      - {attribute: drawsFromHydraulicStorage, required: true}
  - entity_class: HydraulicStorageUnit
    checks:
      - {attribute: energy_storage_capacity, required: true}
      - {attribute: annual_natural_inflow_energy, required: true}
  - entity_class: DemandUnit
    checks:
      - {attribute: belongsToGeographicalRegion, required: true}
      - {attribute: annual_energy_demand, required: true}
```

```text
Is it complete for the four groups' annual dispatch?
    annual_dispatch: 0 gaps
```

Technology, region, capacity, water, and an annual demand. No hours. This is the analysis the data was made for.

## The hourly dispatch

`optimal_dispatch` distributes those annual totals over the hours of a year. On the same model it does not pass:

```text
Before the hourly shapes
    7 gaps
      DemandUnit             hasDemandProfile               ×1
      HydraulicStorageUnit   hasNaturalInflowProfile        ×2
      SolarGenerationUnit    annual_resource_potential      ×1
      SolarGenerationUnit    hasAvailabilityProfile         ×1
      WindGenerationUnit     annual_resource_potential      ×1
      WindGenerationUnit     hasAvailabilityProfile         ×1
```

Demand has a yearly total and no hourly shape. The reservoir basin `storage.CH_RES` has 8.8 TWh and 20 TWh of inflow, and no hourly shape yet. The turbine `gen.CH_HYD_RES` already has its 8.5 GW. The run-of-river reach is the same. Wind and PV have a capacity, and neither an availability nor the annual energy behind it. There is no missing node: `atNode` is required only when a unit has no region, and these plants sit in Switzerland.

## One year of hours

The same six plants and the same demand stay. What is added is one hourly year, and the two annual energies that scale the wind and PV series.

The time axis is `ts.hourly.2030`: 1 January 2030, `PT1H`, 8760 steps, `Europe/Zurich`. 2030 is not a leap year. Every profile points at that one axis.

The numbers are stylised seasons, not a measured weather year. They live in `output/swiss-analyses/profiles.h5`, beside the YAML files. The model stores what a series means (`profile_type`, `data_reference`) and which object uses it.

| Profile | On | `profile_type` | The year |
|---|---|---|---|
| `profile.demand.CH` | `demand.CH` | `as_normalized_annual_energy` | sums to 1. Peak 10965 MW. Winter (Dec–Feb) is 32% of the 58 TWh, summer (Jun–Aug) 17% |
| `profile.wind.CH` | `gen.CH_WIND` | `as_capacity_factor` | 2000 full-load hours, factor 0.12–0.34, so 100 MW gives 0.2 TWh |
| `profile.pv.CH` | `gen.CH_PV` | `as_capacity_factor` | 1000 full-load hours, zero at night, peak 0.49, so 6500 MW gives 6.5 TWh |
| `profile.inflow.CH_RES` | `storage.CH_RES` | `as_normalized_annual_energy` | sums to 1. 64% of the 20 TWh falls in Jun–Aug, 6% in Dec–Feb |
| `profile.inflow.CH_ROR` | `storage.CH_ROR` | `as_normalized_annual_energy` | sums to 1. 43% of the 16 TWh falls in Apr–Jun, 16% in Dec–Feb |

A normalised series sums to 1, so the annual total already on the object — 58 TWh of demand, 20 TWh on the reservoir and 16 TWh on the run-of-river reach — is what turns the shape into megawatt-hours. A capacity factor does not carry that total. `annual_resource_potential` is the capacity times the full-load hours: 0.2 TWh of wind, 6.5 TWh of PV.

Gas, nuclear and the run-of-river machine get no availability. Their energy is a decision, or, for run-of-river, the inflow on the reach. The reservoir's inflow is on the storage itself. No bus is added.

```text
After the hourly shapes
    0 gaps
Schema check: 0 errors
Wrote output/swiss-analyses/dispatch.yaml
profiles.h5  5 series × 8760 h
```

The script does not solve a dispatch. It makes the model complete for both: the annual balance it already satisfied, and the hourly profile it did not. The [power-flow layer](3-power-flow.md) takes 15 January at 19:00 from these series. Must-run wind, PV and run-of-river inflow come first, then nuclear up to its capacity, then the reservoir turbine, then gas. Nuclear's variable cost is 9 MU/MWh and gas is 45, so gas stays off when the turbine can cover the rest.

**Next:** [3. The power-flow layer](3-power-flow.md).
