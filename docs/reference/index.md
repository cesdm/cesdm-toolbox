# Reference

For looking things up, not for learning. If you are new, start with the [tutorial](../tutorial/index.md).

| What | Where |
|---|---|
| Every class, attribute and relation, with types, units and limits | **[Schema reference](schema-reference.html)** — interactive, searchable. [How to use it](using-schema-reference.md) |
| The classes drawn as UML class diagrams: inheritance, attributes, relations | **[Schema diagrams](schema-diagrams/index.md)** — one view per family of classes |
| Python calls | [API](api.md) |
| What an entity, an attribute and a relation are, and how the toolbox is built | [Concepts](../concepts/index.md) |
| Terms used in these pages | [Glossary](glossary.md) |
| Analysis profiles | `cesdm/analysis_profiles/` in the repository: `optimal_dispatch`, `power_flow`, `dynamics` |

Schema 1.0.0 is three folders. `cesdm/schemas/base` is the dispatch base (42 entities, 130 attributes, 32 relations). `cesdm/schemas/powerflow` and `cesdm/schemas/dynamics` extend it. The published schema reference and the diagrams are generated from all three: 59 entities, 271 attributes, 37 relations. The reference page opens with Technical and Dispatch on. Checkboxes turn power flow and dynamic on as well. `powerflow_bus_type` is on `ElectricalBus` because the power-flow package attaches it. After a schema change, regenerate with:

```bash
python -m tools.generate_cesdm_schema_html cesdm/schemas/base cesdm/schemas/powerflow cesdm/schemas/dynamics docs/reference/schema-reference.html
python -m tools.generate_schema_diagrams
```
