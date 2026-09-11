# How to Cite CESDM

If you use CESDM or the CESDM Toolbox in academic work, please cite the project and mention the SWEET-CoSi context where appropriate.

## Software (toolbox)

```bibtex
@software{cesdm_toolbox,
  title        = {CESDM Toolbox: Common Energy System Domain Model},
  author       = {{CESDM Consortium / SWEET-CoSi}},
  year         = {2026},
  url          = {https://github.com/cesdm/cesdm-toolbox},
  note         = {First public release. Record the repository release and SCHEMA\_MANIFEST version used in your study.}
}
```

Adjust `year` and add a `version` or commit hash when you publish results.

## Methodology reference

CESDM is developed within the Swiss **SWEET-CoSi** programme (SWEET — Co-evolution of the Swiss Energy System and Society), Task 1.9. Project information: [sweet-cosi.ch](https://www.sweet-cosi.ch/).

## Reproducibility checklist

When sharing a study model, document:

| Item | Why |
|------|-----|
| Toolbox git tag or commit | Exact API and validation behaviour |
| Schema version from export (`SCHEMA_MANIFEST`) | Model vocabulary compatibility |
| Analysis validation profile used | e.g. `optimal_dispatch`, `power_flow`, `dynamics` |
| Export paths | [YAML](../reference/glossary.md#yaml), Frictionless, HDF5 profile files |

This first release is a starting point: a usable, flexible framework. Record the exact release or commit used in reproducible work. See the [roadmap](roadmap.md) for what is stable vs experimental.

→ [What is CESDM?](../get-started/what-is-cesdm.md) · [Contributing](contributing.md)
