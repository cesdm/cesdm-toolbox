# Files and time series

How is a model written down? YAML and Frictionless hold the objects, the values and the links. HDF5 holds the numbers of a time series. A `Profile` says what those numbers mean, and a `TimestampSeries` gives the time axis. The classes those files describe are in [Classes and libraries](classes-and-libraries.md).

## Files

| Format | Content | Best for |
|---|---|---|
| YAML | the whole model | exchange, review, version control |
| Frictionless | `datapackage.json` + one CSV per class | spreadsheets, data pipelines |
| HDF5 | the numbers of time series | large profiles, referenced from the YAML |

A YAML file is one way of writing a CESDM model down. `export_yaml(path)` writes the flat EAR file and `import_yaml(path)` reads it, for an `ear` model and for a `CesdmModel`. The header is `_cesdm_meta`. YAML keeps the unit that was written and the [provenance](ear.md#provenance) of each value, including letters such as ü. A Frictionless package does the same: each attribute has a value column plus `__unit` and `__provenance_ref`, and every relation target is a row in `relations.csv`. The class table still shows the first target, so a foreign key has a single id to point at. The optional `parquet` extra adds `export_parquet` for profile numbers; the examples store those numbers in HDF5.

## Time series

Hourly data are not stored in the YAML. A `Profile` object says what a series means and where its numbers are; a `TimestampSeries` gives the time axis.

```python
ts = model.add_entity("TimestampSeries", "ts.hourly.2030")
model.add_attribute("ts.hourly.2030", "start_datetime", "2030-01-01T00:00:00")
model.add_attribute("ts.hourly.2030", "resolution", "PT1H")
model.add_attribute("ts.hourly.2030", "length", 8760)

model.add_entity("Profile", "profile.demand.CH")
model.add_attribute("profile.demand.CH", "profile_type", "as_normalized_annual_energy")
model.add_attribute("profile.demand.CH", "data_reference", "profiles.h5:/profiles/profile.demand.CH")
model.add_relation("profile.demand.CH", "hasTimestampSeries", "ts.hourly.2030")
model.add_relation("demand.CH", "hasDemandProfile", "profile.demand.CH")
```

| `profile_type` | Meaning | Typical use |
|---|---|---|
| `as_capacity_factor` | share of installed capacity | wind, PV availability |
| `as_normalized_annual_energy` | share of a yearly total | demand |
| `as_SI` | absolute values | prices, measurements |

| Common mistake | Fix |
|---|---|
| an array whose length differs from the `TimestampSeries` length | regenerate or trim the data |
| a `profile_type` that does not match the data — a capacity factor declared as `as_SI` | match the type to what the numbers mean |
| one time axis per profile | let all profiles of a study share one `TimestampSeries` |
