# FAQ

**Do we have to give up our own model or file format?**
No. Each group keeps its representation and writes one adapter. CESDM is only what travels between groups.

**Is that really less work than a direct converter to the one group we work with?**
For a single pair and a one-off exchange, a direct script can be quicker. CESDM pays off when you exchange repeatedly, with more than one group, or in both directions: one adapter serves every partner, the sender checks before sending, and two groups can compare their inputs entity by entity. See the [tutorial](../tutorial/index.md).

**What happens to information the receiving tool cannot use?**
It stays in the CESDM file the receiver got, so nothing is lost for the next exchange. Where the receiver's format lacks a field that it needs — Group C has no identifier for run-of-river inflow — its adapter generates one.

**How does CESDM relate to PyPSA, Calliope or our own model?**
They solve; CESDM describes. Each tool or group keeps its own data structures and maps them once to CESDM, through an adapter. CESDM is what travels between them. See [Why CESDM](../concepts/index.md).

**Can we check that two groups model the same system?**
Yes. Once both are in CESDM, compare them by meaning — region and technology — in common units, as `compare.py` does in [step 2 of the tutorial](../tutorial/2-check.md#do-the-four-groups-describe-the-same-system).

**How do we know a model is complete enough for our analysis?**
`model.validate_for_analysis("optimal_dispatch" | "power_flow" | "dynamics")`, or a profile you write yourselves. See [validation](../concepts/validation.md).

**Does validation prove that an adapter mapped things correctly?**
No. It proves the result is valid and complete CESDM. Whether `Typ = 6` really is reservoir hydro is the adapter author's responsibility — which is why the round trip test in [write an adapter](../guides/write-an-adapter.md) matters.

**Which tools are connected?**
pandapower and MATPOWER in both directions, PyPSA networks and TYNDP data into CESDM. See the [table](../guides/write-an-adapter.md#examples-of-adapters-and-converters).

**Do I need Python?**
To write an adapter or build a model, yes. To read a model, no: YAML and the Frictionless CSVs open in any editor or spreadsheet.

**Can I edit a model in Excel?**
For inspection and small edits, via the Frictionless CSVs. Exchange and version control work best with YAML.

**Core calls or proxy API?**
The core calls (`add_entity`, `add_attribute`, `add_relation`) for adapters and code others will read; they work on any model. The [proxy API](../guides/proxy-api.md) — `gen.nominal_power_capacity = (8500, "MW")` — for your own scripts and notebooks. Both write the same entity.

**What is the difference between a carrier and a carrier domain?**
A carrier is *what* is transported: electricity, gas, heat. A carrier domain is *where* it is transported: the network or infrastructure for that carrier. See [carrier domains](../guides/carrier-domains.md).

**Where do the hourly numbers go?**
Not into the YAML. A `Profile` object in the model says what a series means and points to its numbers in an HDF5 file. See [time series](../concepts/energy-model.md#time-series).

**Why is the vocabulary in schema files and not in code?**
So that it can be read, reviewed, versioned and extended without touching the engine — and so that every group checks against the same written rules, whatever tool it uses. See [Schemas](../concepts/schemas.md).

**Can the toolbox describe something other than an energy system?**
The engine has no energy classes of its own; a schema supplies them. The [bookshelf](../concepts/ear.md#a-schema-that-is-not-energy) is a schema that does not extend CESDM: an author, a book, and `writtenBy`. The worked extension of CESDM is the [living lab](../guides/energy-and-society.md): households, a survey, and the PV and meters those households point at, on top of `schemas/cesdm`.

**Is CESDM an ontology?**
No. It is a schema with agreed meaning. The schema says what may appear; the meaning of each attribute is agreed and documented; the classes form a concept graph, but that is background, not the product.

**What if the schema lacks something we need?**
Add it in your own schema package without changing the core — see [extend the schema](../guides/extend.md) — and propose it for the core if others need it too. [How the core grows](../concepts/schemas.md#how-the-core-grows).

**Which schema version is current?**
Schema 1.0.0, in three folders. `schemas/cesdm` is the dispatch base. `schemas/cesdm_power_flow` adds load-flow fields and classes. `schemas/cesdm_dynamic` adds machine models and controllers. The toolbox release is 1.0.0. See [roadmap and releases](roadmap.md).
