# Best practices for writing adapters

An adapter connects one representation — your files, your tool — to CESDM. You write it once; after that you can exchange with every group that has one. The four adapters in the [tutorial](../tutorial/index.md) are complete, short examples to copy from; `adapter_a.py` is the best starting point.

## The essential steps

1. **List what your representation contains.** Files, identifiers, codes, units. Note what is implicit — the meaning of a code, the unit of a column without a unit in its name.
2. **Write the mapping table.** One row per piece of information: what it means, which CESDM class, attribute or relation it becomes, in which unit. Decide for each item whether it is a *value* (`nominal_power_capacity`) or a *link* to another object (`atNode`, `hasTechnology`). Look up names in the [schema reference](../reference/index.md).
3. **Implement `to_cesdm`.** One loop per source table, with `unit=` and `provenance_ref=` on every value.
4. **Check.** `model.validate()` before every export: the file must be correct CESDM. Pass `unit=` on every value, so the check can work. Run `python docs/examples/four-research-groups/mistakes.py` to see what it catches.
5. **Implement `from_cesdm`.** Read the same table backwards. A one-way adapter is half an exchange: without it, you cannot take back what others improved.
6. **Test the round trip.** Your files → CESDM → your files, and your files → CESDM → another group's format → CESDM, must give the same system. The tutorial's `compare.py` checks this by meaning, not by identifiers.

Some questions to guide the adapter development are given below:

| Question | Example from the tutorial |
|---|---|
| What do our codes mean? | Group B's `gas` is a CCGT — written down once, in Group B's adapter. |
| How are objects matched across groups? | By region and technology, not by identifier (`compare.py`). |
| What if our format has no field for something? | Generate it on the way in (Group C's `ror_inflow`); keep what you cannot store in the CESDM file. |

## Other rules of thumb

- **Do not drop information silently.** If your representation cannot express something, say so — print it, or keep it in CESDM.
- **Make conventions explicit in the adapter.** For example, if your storage rows belong to plants “by convention”, write the link explicitly (`drawsFromHydraulicStorage`).
- **Record the source.** Define `provenance_ref=` so that data from different groups stay distinguishable.
- **Keep the mapping knowledge in the adapter.** Code tables belong in exactly one place.
- **Use CESDM identifiers consistently.** A consistent naming scheme such as `gen.<your id>` makes it easier to write reverse adapters.

## Examples of adapters and converters

| Tool or format | Direction | Where |
|---|---|---|
| Groups A–D of the tutorial (CSV, Excel, YAML, JSON) | both | `docs/examples/four-research-groups/adapter_*.py` |
| pandapower | CESDM → tool, tool → CESDM | `tools/export_pandapower.py`, `tools/import_pandapower.py` |
| MATPOWER | CESDM → tool, tool → CESDM | `tools/export_matpower.py`, `tools/import_matpower.py` |
| PyPSA network (`.nc`) | tool → CESDM | `tools/import_pypsa.py` |
| TYNDP 2024 tables | data → CESDM | `examples/example_import_tyndp.py` |

Converters in one direction only are marked as such. For example, an export from CESDM to PyPSA is not available yet — see [contribute](../project/contribute.md).
