# Build models

The same loop as the first model, written as a checklist you can reuse for a real study: create the system, add plants, attach time series, check, export.

!!! abstract "Before you start"
    Complete [Build your first model](../get-started/first-model.md) once so the steps below look familiar.

---

## The workflow in five phases

Use this mental model first:

```text
DEFINE          BUILD             ENRICH          CHECK           USE
system     →    assets +     →    technology + → validation  →   export /
boundary        topology          profiles                       analysis tools
```

The implementation below expands those five phases into nine practical steps. You do not need to memorise them.

| Phase | Practical steps | Outcome |
|---|---|---|
| **Define** | 1. System boundary | Scope and carrier domains are clear |
| **Build** | 2. Shared library, 3. Assets | Physical objects and topology exist |
| **Enrich** | 4. Time series | Technologies and profiles are attached |
| **Check** | 5. Schema validation, 6. Analysis validation | Model is consistent and fit for the study |
| **Use** | 7. Export, 8. Optional aggregation, 9. Tool hand-off | Model can be exchanged and analysed |

![Study model lifecycle](../illustrations/modelling_workflow.svg)

## Step 1 — Define the system boundary

```python
from cesdm_toolbox import build_model_from_yaml
from cesdm.default_library import CarrierDomains

model = build_model_from_yaml("schemas/cesdm")
model.import_library("library/default_library")

system = model.add_entity("EnergySystemModel", "MY_STUDY_2030")
system.long_name = "My country study, 2030 scenario"

electricity = model.get_entity(CarrierDomains.DOMAIN_ELECTRICITY)
```

Decide which [carrier domains](../understand/carrier-domains.md) are **endogenous** (modelled explicitly) vs **exogenous** (external supply only). Electricity-only studies often keep gas exogenous. Default domains come from the library; geography stays on regions and buses via `belongsToGeographicalRegion`.

---

## Step 2 — Import the default library

```python
model.import_library("library/default_library")
```

Import shared carriers, domains, technology types, and resources. See [Libraries](../understand/libraries.md).

---

## Step 3 — Add assets

```python
from cesdm.default_library import GeneratorTypes

bus = model.add_entity("ElectricalBus", "bus.ch")
bus.name = "Switzerland 380 kV"
bus.nominal_voltage = (380, "kV")
bus.belongsToCarrierDomain = electricity

gen = model.add_entity("GenerationUnit", "gen.ch.wind")
gen.name = "Swiss wind"
gen.nominal_power_capacity = (3500, "MW")
gen.hasTechnology = GeneratorTypes.GENERATION_RENEWABLE_WIND_ONSHORE
gen.atNode = bus
```

---

## Step 4 — Attach profiles

Structural metadata lives in the CESDM model; numerical arrays live in HDF5 or Parquet. See [Profiles](../understand/profiles.md).

```python
ts = model.add_entity("TimestampSeries", "ts.main")
ts.start_datetime = "2030-01-01T00:00:00"
ts.resolution = "1h"
ts.length = 8760

profile = model.add_entity("Profile", "profile.demand.ch")
profile.profile_type = "as_normalized_annual_energy"
profile.profile_unit = "MWh"
profile.data_reference = "profiles.h5:/profiles/demand_ch"
profile.hasTimestampSeries = ts

demand = model.get_entity("dem.ch")
demand.hasDemandProfile = profile
```

---

## Step 5 — Schema validation

```python
errors = model.validate()
if errors:
    for e in errors:
        print(e)
else:
    print("Schema validation passed.")
```

See [Validation](validate-models.md#schema-validation).

---

## Step 6 — Analysis-specific validation

```python
errors = model.validate_for_analysis("optimal_dispatch")
```

Shipped profiles include `optimal_dispatch`, `power_flow`, and `dynamics` under `analysis_profiles/`. See [Validation](validate-models.md#analysis-specific-validation).

---

## Step 7 — Export

```python
output_dir = "output/my_study"
model.export_yaml_hierarchical(f"{output_dir}/my_study.yaml")
model.export_frictionless(
    f"{output_dir}/frictionless/",
    name="my-study",
    title="My study model",
    include_library="referenced",
)
```

Formats and adapters: [Import and export](import-export.md).

---

## Step 8 — Spatial aggregation (optional)

Derive a coarser model from a detailed one without rebuilding from scratch. See [Spatial aggregation](spatial-aggregation.md).

---

## Step 9 — Hand off to analysis tools

Each analysis tool maps once to CESDM. See [What is CESDM?](../get-started/what-is-cesdm.md) and [Import and export](import-export.md).

---

## Checklist

Before sharing a model:

- [ ] `EnergySystemModel` and carrier domains defined
- [ ] Assets attached to the network (`atNode`, `fromNode` / `toNode`)
- [ ] Technologies referenced from the library where appropriate
- [ ] Profiles linked with the correct `profile_type` and array length
- [ ] `model.validate()` passes
- [ ] `model.validate_for_analysis("<your study>")` passes
- [ ] YAML and profile data exported, paths documented

---

## Next step

[Validate models](validate-models.md) · [Import and export](import-export.md) · [Profiles](../understand/profiles.md)
