# Contribute and cite

## Contribute

The most valuable contributions are **adapters** for tools and data formats, **use cases** that show what is missing, and **critique** of the schema.

1. Fork [cesdm/cesdm-toolbox](https://github.com/cesdm/cesdm-toolbox) and branch from `main`.
2. `pip install -e ".[dev]"`
3. Open a pull request that says why the change helps modellers.

To preview a documentation change:

```bash
pip install -r docs-requirements.txt
mkdocs serve            # preview
mkdocs build --strict   # what CI runs
```

### Proposing a schema change

Additions start in an extension package of your own ([how the core grows](../concepts/schemas.md#how-the-core-grows)). When you propose one for the core, say in the issue:

- **what** changes — classes, attributes, relations, units;
- **why** — the use case, ideally with a model that needs it;
- whether it is a **patch, minor or major** change by the [versioning rule](roadmap.md#versioning);
- what it means for **existing models and adapters**.

### Issues and contacts

Bugs, gaps in the documentation and requests go to [GitHub Issues](https://github.com/cesdm/cesdm-toolbox/issues) — with the toolbox commit, a minimal example, and what you expected. Contributions are accepted under the [MIT License](https://github.com/cesdm/cesdm-toolbox/blob/main/LICENSE).

| Topic | Contact |
|---|---|
| CESDM capabilities | [Dr. Rafaella Canessa](mailto:rcanessa@ethz.ch) |
| Semantics and ontology | [Dr. Edrisi Muñoz Mata](mailto:edrisim@ethz.ch) |
| Electric power system analysis | [Dr. Nikolaos Savvopoulos](mailto:nsavvopoulos@ethz.ch) |
| Energy system analysis | [Dr. Andrea Bellè](mailto:abelle@ethz.ch) |

## Cite

The CESDM project is part of the [SWEET-CoSi consortium](https://www.sweet-cosi.ch/), funded by the [Swiss Federal Office of Energy (SFOE)](https://www.bfe.admin.ch/de/foerderprogramm-sweet) through its [SWEET programme](https://www.bfe.admin.ch/en/general-information-sweet). See [Acknowledgement](acknowledgement.md).

```bibtex
@software{cesdm_toolbox,
  title  = {CESDM: Common Energy System Domain Model},
  author = {{CESDM Consortium / SWEET-CoSi}},
  year   = {2026},
  url    = {https://github.com/cesdm/cesdm-toolbox},
  note   = {Record the toolbox release and the schema version used.}
}
```

When you publish results or share a model, state:

| Item | Why |
|---|---|
| toolbox commit or release | the exact behaviour of the calls and checks |
| schema packages and their versions (`SCHEMA_MANIFEST.yaml`) | which vocabulary the model uses — a receiver must load the same packages |
| analysis profiles you validated against | what "complete" meant for your study |
| the files exchanged — YAML, Frictionless, HDF5 profiles | what exactly was used |
