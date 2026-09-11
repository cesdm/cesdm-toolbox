# Validation

The first model already called `model.validate()`. CESDM has **two** checks. They answer different questions.

| Check | Question | Call |
|-------|----------|------|
| **[Is the description allowed?](#schema-validation)** | Do the objects, facts and connections match the loaded schemas? | `model.validate()` |
| **[Is it complete for my study?](#analysis-specific-validation)** | Does this model have what *this* analysis needs? | `model.validate_for_analysis("optimal_dispatch")` |

A model can pass the first check and still be unusable for power flow if impedances are missing.

## Schema validation

`model.validate()` asks: is every type allowed, every unit valid, every required connection present?

```python
errors = model.validate()
if errors:
    for error in errors:
        print(error)
```

An empty list means the description is consistent with the schemas. Run this after you change objects, and before you export.

Typical messages:

```text
DemandUnit dem.demo
    Invalid unit for attribute 'annual_energy_demand': 'GWh' (expected 'MWh/year')

DemandUnit dem.demo
    Missing required relation: atNode

GenerationUnit gen.demo.wind
    Unknown attribute: efficiency_at_full_load
```

The first is the unit rule from the first model (`MWh/year`, not `GWh`). The second means the load is not connected to a bus. The third is a fact the schema does not define on that type.

More examples: `examples/example_validation.py` and `notebooks/cesdm_schema_validation.ipynb`.

## Analysis-specific validation

Dispatch, power flow and dynamics need different facts on the **same** plants.

| Analysis | Typically needs |
|----------|-----------------|
| Optimal dispatch | Capacities, costs, demand profiles |
| Power flow | Voltages, impedances |
| Dynamics | Inertia and controller parameters |

```python
errors = model.validate_for_analysis("optimal_dispatch")
```

Shipped checks live under `analysis_profiles/` (`optimal_dispatch`, `power_flow`, `dynamics`). They are YAML lists of required facts — they do not run the study.

```text
GenerationUnit gen.demo.wind
    Missing attribute: variable_operating_cost
```

That model can still pass `validate()`. It is just not ready for a dispatch run.

```python
model.validate()
model.validate_for_analysis("optimal_dispatch")
model.export_yaml_hierarchical(...)
```

Command line: `python tools/validate_analysis.py model.yaml --profile optimal_dispatch`.

## Next

[Import and export](import-export.md) · [Build models](build-models.md) · [Schemas](../understand/schemas.md)
