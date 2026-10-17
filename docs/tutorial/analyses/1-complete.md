# 1. Checking for completeness

At the end of Part 1, the Swiss system is **correct CESDM**: `model.validate()` finds nothing. That check is analysis-independent — it says that everything in the file means what the schema says.

It does not say whether the file contains *enough* for a particular analysis. That is a second check, and the answer depends on the analysis:

```python
model.validate()                         # correct?           — the same for everyone
model.validate_for_analysis(profile)     # complete for this? — one profile per analysis
```

```bash
python docs/examples/swiss-analyses/step1_complete.py
```

```text
Is it correct CESDM?
    model.validate(): 0 errors
Wrote output/swiss-analyses/system.yaml
```

That file is the system from Part 1 and nothing else. Each later step reads the previous file and writes a new one with one analysis appended.

## How a profile works

A profile is a short YAML file. Each block names a class; it applies to every object of that class **and of its subclasses**. Each check names an attribute or a link:

| Field | Meaning | Example |
|---|---|---|
| `required: true` | must be present | `nominal_power_capacity` |
| `constraints` | limits the value must respect | `minimum: 0` |
| `when` | the check applies only if a condition holds | `when: "annual_natural_inflow_energy > 0"` |

A `when` condition can test whether an attribute or link is present, compare a value, and combine both with `and`, `or`, `not`.

The toolbox ships `optimal_dispatch`, `power_flow` and `dynamics` in `analysis_profiles/`. Any group can write its own. A profile reports a gap only for something it asks about, so an empty report can mean the profile never looked. The [dynamics layer](4-dynamics.md) is that case.

Each following step runs `validate_for_analysis` for one analysis and, where the model falls short, adds what that analysis needs. The dispatch is the first of them.

**Next:** [2. The dispatch layer](2-dispatch.md).
