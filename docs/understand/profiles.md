# Profiles and time series

The [first model](../get-started/first-model.md) wrote hourly demand, wind and PV availability, and reservoir inflow to `profiles.h5`. The YAML only stores **what the series means**. The numbers stay in the HDF5 file.

```text
demand  ── hasDemandProfile ──► Profile ──► TimestampSeries
                                         └── profiles.h5 (8760 values)
```

Two objects:

| Object | Role in the first model |
|--------|-------------------------|
| `TimestampSeries` | Hourly 2030 axis, 8760 steps |
| `Profile` | “This array is a demand shape” or “this is a capacity factor” |

```python
ts = model.add_entity("TimestampSeries", "ts.hourly.2030")
ts.start_datetime = "2030-01-01T00:00:00"
ts.resolution = "PT1H"
ts.length = 8760

profile = model.add_entity("Profile", "profile.dem.demo.demand")
profile.profile_type = "as_normalized_annual_energy"
profile.data_reference = "profiles.h5:/profiles/profile.dem.demo.demand"
profile.hasTimestampSeries = ts
demand.hasDemandProfile = profile
```

| `profile_type` | Meaning | First-model use |
|----------------|---------|-----------------|
| `as_capacity_factor` | Share of installed capacity | Wind and PV |
| `as_normalized_annual_energy` | Share of a known yearly total | Demand and inflow |
| `as_SI` | Absolute values | Prices, measurements |

Reuse one time axis for every series in the same study. Array length must match `ts.length`.

![Profile types](../illustrations/profile_types.svg)

Typical links: `hasAvailabilityProfile` (generation), `hasDemandProfile` (load), `hasNaturalInflowProfile` (reservoir).

The runnable pattern is in `docs/examples/minimal_electricity_model.py`.

## Next

[Libraries](libraries.md) · [Validation](../use/validate-models.md) · [Build models](../use/build-models.md)
