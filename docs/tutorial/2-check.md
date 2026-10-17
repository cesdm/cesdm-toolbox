# 2. Validation of CESDM files

Before each group sends its file, it must first check that the file is valid CESDM. This check does not depend on and does not cover what anyone will do with the model — dispatch, power flow or types of analyses. It only verifies the integrity of the file: that every class, value, unit and link mean what the schema says they mean.

```python
adapter_a.to_cesdm(folder, model)        # schema and libraries are already loaded
model.validate()                          # [] — correct CESDM
model.export_yaml("group_a.yaml")
```

Errors in an adapter are caught at two different moments. `mistakes.py` walks through several of them one at a time, each on a fresh copy of Group A's model. The messages below are what that script prints.

## Errors caught by the adapter

 Some mistakes are impossible to make: CESDM refuses them immediately upon calling the adapter code.
 
| Mistake | Message |
|---|---|
| Unit not converted: GWh passed on as GWh | `Unit 'GWh/year' is not allowed for 'annual_energy_demand'. Allowed: ['MWh/year']` |
| The group's own column name instead of the CESDM attribute | `Unknown attribute 'Pmax'` |
| A reservoir linked from a plain `GenerationUnit` instead of a `HydroGenerationUnit` | `Unknown relation 'drawsFromHydraulicStorage'` |
| A number written as text | `could not convert string to float: '3 GW'` |

## Errors caught by `model.validate()`

Other mistakes can only be judged when the whole model is there — for example, whether a link points to something that actually exists. These are reported by `model.validate()`:

| Mistake | Message |
|---|---|
| Group C's region code not translated | `Relation 'belongsToGeographicalRegion' with 'region.country.CHE' not among entities of allowed classes [GeographicalRegion]` |
| An efficiency above 1 | `Attribute 'energy_conversion_efficiency' violates maximum 1.0: 1.5` |
| A plant linked to the wrong kind of object | `Relation 'drawsFromHydraulicStorage' with 'demand.CH' is of class 'DemandUnit' not compatible with any of [HydraulicStorageUnit]` |
| A sign error | `Attribute 'energy_storage_capacity' violates minimum 0.0: -8800000.0` |

Without validating the exchanged files against a schema, each of these errors would arrive at the receiver unnoticed: an invalid geographical region, an efficiency value outside 0–1, a hydro plant that draws from a load, a reservoir with negative capacity.

## What is not checked

A correct model is not necessarily *complete for a particular analysis*. Schema validation accepts a reservoir plant without any water, because many uses of a model never need it. Whether a model contains everything a dispatch, a power flow or a dynamic simulation needs is a separate, analysis-dependent question, answered by analysis profiles — see [Part 2](analyses/1-complete.md).

Schema validation also cannot know whether a correct number is the *right* number. Leaving out the unit is the classic case: the schema then assumes its own unit, so a nuclear capacity of `3.0` meant in GW, written without `unit=`, silently becomes 3 MW.

```text
model.validate(): []
```

That is why every adapter passes `unit=` explicitly — and why the second check below exists.

## Do the four groups describe the same system?

With all four systems in correct CESDM, they can be compared directly — without converting units, translating codes or reconciling structures by hand for each pair of groups.

Due to inter-group differences, the comparison cannot be made based on identifiers: Group A's nuclear plant is referred to as `CH_NUC`, Group C's is `nuc`, Group D's is `che-nuc`. Instead, the example script `compare.py` matches plants on region and technology category. Capacities, efficiency, variable cost, storage and inflow are compared in CESDM-native units:

```python
from compare import compare
compare(load("group_a.yaml"), load("group_c.yaml"), "A", "C")      # []
```

```text
2 · Do the four groups describe the same system?
    A vs B: 0 differences
    A vs C: 0 differences
    A vs D: 0 differences
```

The missing unit from above is caught as well:

```text
compare: nuclear in CH: capacity 3,000 MW (Group A) vs 3 MW (with mistake)
```

Suppose Group D still works with last year's data. The quickstart writes that file next to the others, with solar at 6000 MW and reservoir inflow at 18 TWh/year:

```bash
python docs/examples/four-research-groups/compare.py \
    output/four-research-groups/group_a.yaml \
    output/four-research-groups/group_d_2025.yaml
```

Output:

```text
2 differences
 - reservoir_hydro in CH: annual inflow 20,000,000 MWh/year (group_a) vs 18,000,000 MWh/year (group_d_2025)
 - solar in CH: capacity 6,500 MW (group_a) vs 6,000 MW (group_d_2025)
```

In a model intercomparison, these are the kinds of input differences that may otherwise surface months later as unexplained differences in results.

!!! note "Limits of the comparison"
    Matching on region and technology category works while each group has at most one plant per category and region; with several, they should be first aggregated or matched on a finer key such as a grid node. The comparison currently covers capacity, efficiency, variable cost, storage and inflow.

**Next:** [Exchanging with other groups](3-exchange.md).
