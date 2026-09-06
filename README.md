<p align="center">
  <img src="docs/illustrations/cesdm_hero.svg" alt="CESDM – Common Energy System Domain Model" width="900">
</p>

<p align="center">
  <a href="https://cesdm.github.io/cesdm-toolbox/"><img src="https://img.shields.io/badge/docs-GitHub%20Pages-2563EB.svg" alt="Documentation"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-16A34A.svg" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/status-research%20%2F%20beta-F59E0B.svg" alt="Research / Beta">
</p>

# CESDM

**A common description of an energy system that different modelling tools can share.**

```text
                  ONE ENERGY SYSTEM

           ┌─────────────────────────┐
           │          CESDM          │
           │                         │
           │ buses • generators      │
           │ loads • storage         │
           │ regions • profiles      │
           └────────────┬────────────┘
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
        PyPSA       pandapower     FlexECO
       planning      grid flow     dispatch
```

**CESDM describes the system. Tools perform analyses on it.**

### Use CESDM when you want to

- describe an energy system independently of a particular tool;
- reuse the same system across different analyses;
- exchange models between tools;
- validate that a model contains the information required for an analysis.

| CESDM is | CESDM is not |
|----------|--------------|
| A common energy-system description | An optimisation model |
| A semantic data model + validation | A power-flow solver |
| An interoperability layer | Another PyPSA or a CIM operations standard |

Docs: **[CESDM in 5 Minutes](https://cesdm.github.io/cesdm-toolbox/getting-started/cesdm-in-5-minutes/)** · **[Build a Small Electricity System](https://cesdm.github.io/cesdm-toolbox/getting-started/first-model-simple/)** · [Project status](docs/getting-started/project-status.md)

---

## Installation

```bash
git clone https://github.com/cesdm/cesdm-toolbox.git
cd cesdm-toolbox

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

python -m pip install --upgrade pip setuptools wheel
pip install -e .
```

<details>
<summary>Using <a href="https://docs.astral.sh/uv/">uv</a> or Poetry instead</summary>

```bash
# uv
uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -e .

# Poetry
poetry install
poetry shell
```

</details>

| Optional component | Command |
|---|---|
| PyPSA | `pip install -e ".[pypsa]"` |
| pandapower | `pip install -e ".[pandapower]"` |
| MATPOWER | `pip install -e ".[matpower]"` |
| Jupyter | `pip install -e ".[jupyter]"` |
| Everything (toolbox extras) | `pip install -e ".[all]"` |

---

## Quick start

```bash
python docs/examples/minimal_electricity_model.py
```

Wind + PV + reservoir hydro + demand, then YAML, Frictionless, and `profiles.h5` under `output/minimal_electricity_model/`.

Walkthrough: **[Build a Small Electricity System](docs/getting-started/first-model-simple.md)** · full site: **[cesdm.github.io/cesdm-toolbox](https://cesdm.github.io/cesdm-toolbox/)**

---

<details>
<summary>How CESDM works internally (EAR)</summary>

CESDM uses **Entity–Attribute–Relation (EAR)**:

- An **entity** is an object (generation unit, bus, demand, line).
- An **attribute** is a property (`nominal_voltage`, `nominal_power_capacity`).
- A **relation** connects entities (`atNode`, `hasTechnology`).

Energy-specific semantics live in YAML schemas. Day-to-day Python uses entity handles (`bus.name = …`, `gen.atNode = bus`). See [How CESDM represents your system](docs/getting-started/core-concepts.md).

</details>

---

## Examples and adapters

| Script | Role |
|---|---|
| [`docs/examples/minimal_electricity_model.py`](docs/examples/minimal_electricity_model.py) | First model — wind, PV, hydro, demand |
| [`docs/examples/reference_energy_system_model.py`](docs/examples/reference_energy_system_model.py) | CH + neighbours reference |
| [`notebooks/building_your_cesdm_model.ipynb`](notebooks/building_your_cesdm_model.ipynb) | Interactive walkthrough |
| [`examples/`](examples/) | PyPSA / TYNDP import, hydro, multi-energy |

| Interface | In this toolbox |
|---|---|
| YAML / Frictionless / HDF5 | Core exchange |
| PyPSA, pandapower, MATPOWER | [Tool adapters](docs/guides/tool-adapters.md) |

---

## Documentation

| I want to… | Page |
|---|---|
| Understand CESDM | [CESDM in 5 Minutes](docs/getting-started/cesdm-in-5-minutes.md) |
| Compare with PyPSA / CIM | [CESDM vs other tools](docs/getting-started/cesdm-vs-others.md) |
| See maturity | [Project status](docs/getting-started/project-status.md) |
| Choose a role path | [Choose your path](docs/getting-started/choose-your-path.md) |

---

## Project status

Research / beta (SWEET-CoSi). Schemas and APIs evolve. Details: [Project status](docs/getting-started/project-status.md).

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Open an issue before large structural changes.

## License

See [`LICENSE`](LICENSE).
