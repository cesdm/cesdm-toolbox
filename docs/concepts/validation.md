# Validation

CESDM checks a model twice, for two different questions.

| Check | Question | Depends on the analysis? | Call |
|---|---|---|---|
| **Schema validation** | Is this correct CESDM? | no — the same for everyone | `model.validate()` |
| **Analysis validation** | Is it complete for *this* use? | yes — one profile per analysis | `model.validate_for_analysis("power_flow")` |

A model can pass the first and fail the second. A valid model with a reservoir plant but no water cannot run a dispatch; a valid model without line impedances cannot run a power flow. Both checks only look at the data. Neither runs the analysis.

## Is it correct CESDM?

Schema validation is what a sender guarantees before exchanging a model. It checks everything the schema says:

- every object has a known class;
- every value is an allowed attribute of that class, of the right type, in a permitted unit, within its limits;
- every link is an allowed relation of that class and points at an existing object of an allowed class;
- everything the schema marks as required is present.

Some of this is enforced the moment a value is written — an unknown attribute, a wrong unit or text where a number belongs is refused by `add_attribute`. The rest needs the whole model, such as whether a link target exists, and is reported by `validate()`, which returns a list of messages (empty when the model is correct). [Step 2 of the tutorial](../tutorial/2-check.md) shows both kinds with the real messages.

What schema validation cannot know is whether a correct number is the *right* number. A capacity of `3.0` meant in GW but written without a unit becomes 3 MW and is perfectly valid. That is why adapters always pass `unit=`, and why [comparing two groups' models](../tutorial/2-check.md#do-the-four-groups-describe-the-same-system) catches what validation cannot.

## Is it complete for this analysis?

Most data that only some analyses need is optional in the schema — power-flow setpoints, machine parameters, even costs — because many models never use it. Whether it must be present is decided by an **analysis profile**: a short YAML file that lists, per class, what one analysis needs.

```yaml
name: annual_dispatch
requirements:
  - entity_class: HydroGenerationUnit
    checks:
      - attribute: drawsFromHydraulicStorage
        required: true
  - entity_class: HydraulicStorageUnit
    checks:
      - attribute: hasNaturalInflowProfile
        required: true
        when: "annual_natural_inflow_energy > 0"
```

| Field | Meaning |
|---|---|
| `entity_class` | the block applies to every object of this class **and its subclasses** |
| `attribute` | an attribute or a relation; both are named the same way |
| `required: true` | must be present |
| `constraints` | limits the value must respect, e.g. `minimum: 0`, `enum: [slack, PV, PQ]` |
| `when` | the check applies only if a condition holds — presence of an attribute or link, a comparison, combined with `and`, `or`, `not` |

```python
model.validate_for_analysis("optimal_dispatch")                  # a shipped profile, by name
model.validate_for_analysis("path/to/annual_dispatch.yaml")      # your own
model.validate_for_analysis_or_raise("power_flow")               # raises ValueError listing the gaps
```

The toolbox ships `optimal_dispatch`, `power_flow` and `dynamics` in `analysis_profiles/`. Any group can write its own, and two groups can agree on one — then "complete" means the same for both. A profile only reports what it asks about: an empty result means nothing the profile checks is missing, not that the model is complete for every purpose. [Part 2 of the tutorial](../tutorial/analyses/index.md) uses one profile per layer on the Swiss system.

### From the command line

```bash
python tools/validate_analysis.py output/swiss-analyses/system.yaml \
    -p optimal_dispatch -p power_flow -s schemas/cesdm_power_flow
```

```text
Model: output/swiss-analyses/system.yaml

✗ optimal_dispatch: 7 issue(s)
    - [optimal_dispatch] [DemandUnit:demand.CH] missing required 'hasDemandProfile'
    …
✗ power_flow: 14 issue(s)
    - [power_flow] [GenerationUnit:gen.CH_GAS] missing required 'atNode'
    …
```

`-p` can be repeated; `-s` loads the schema packages the file needs; `--json` prints machine-readable output for CI.

## Design

- **Two questions, two checks.** Correctness is shared; completeness depends on the use.
- **Declarative.** Profiles are YAML, not code, so they can be read, reviewed and exchanged like the model.
- **Entity-centric and inheritance-aware.** A requirement names the class that owns the data, and covers its subclasses.
- **Domain-independent.** Both checks live in the `ear` engine. The [living-lab guide](../guides/energy-and-society.md) uses the same profile mechanism for a survey and for the joint analysis.
